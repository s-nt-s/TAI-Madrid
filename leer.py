#!/usr/bin/python3
# -*- coding: utf-8 -*-
import io
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from glob import glob
from urllib.parse import unquote, urljoin
import time

import bs4
import requests
import xlrd
import argparse
from subprocess import check_output
import json

from api import Descripciones, Organismo, Puesto

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

parser = argparse.ArgumentParser(
    description='Pasa los datos fuentes a json o similares')
parser.add_argument('--todo', action='store_true', help='Autoexplicativo')
parser.add_argument('--rpt', action='store_true',
                    help='Solo genera la parte de los RPT')
parser.add_argument(
    '--dir3', action='store_true', help='Solo genera la parte de Dir3')
parser.add_argument('--gob', action='store_true',
                    help='Solo genera la parte de administracion.gob.es')

args = parser.parse_args()


re_space = re.compile(r"  +")
re_number = re.compile(r"^\d+,\d+$")
re_categoria = re.compile(r"^\s*\d+\.\s*-\s*(.+)\s*:\s*$")
re_spip = re.compile(r"^\s*(Página:|Fecha:|\d+/\d+/20\d+|\d+ de \d+)\s*$")
re_residencia = re.compile(r"^\s*(\d+-\d+-\d+)\s+([A-Z].*)\s*$")
re_sp = re.compile(r"  +")
re_bk = re.compile(r"\s+")
re_puesto = re.compile(r"\b(\d{6,7})\b")
re_map = re.compile(
    r"http://maps.googleapis.com/maps/api/staticmap\?center=(.*?)&.*")


def parse(cell):
    if not cell:
        return None
    v = cell.value
    if isinstance(v, float):
        return int(v) if v.is_integer() else v
    if isinstance(v, str):
        v = v.strip()
        v = re_space.sub(" ", v)
        v = v.replace("PROGRAMDOR", "PROGRAMADOR")
        if re_number.match(v):
            v = float(v.replace(",", "."))
            return int(v) if v.is_integer() else v
        return v if len(v) else None
    return v


def full_attrib(attrib):
    prefix, name = attrib.split(":")
    attrib = "{%s}%s" % (ns[prefix], name)
    return attrib


def _find_rec(node, tag):
    values = []
    for r in node.findall(tag, ns):
        if r is not None:
            value = r.text
            if value is None:
                r = r.attrib.get(full_attrib("rdf:resource"), None)
                if r is not None:
                    value = unquote(r.split("/")[-1])
            if value:
                value = value.replace("-", " ")
                value = re_sp.sub(" ", value)
                value = value.strip()
                if value not in values:
                    values.append(value)
    for child in node:
        for value in _find_rec(child, tag):
            if value not in values:
                values.append(value)
    return values


def find_rec(node, *args, index=None):
    values = []
    for tag in args:
        for value in _find_rec(node, tag):
            if value not in values:
                values.append(value)
    if index is not None:
        return values[index] if len(values) > index else None
    return values if len(values) > 0 else None


def parse_dire(node):
    tipoVia = find_rec(node, "escjr:tipoVia", index=0)
    fullAddress = find_rec(node, "locn:fullAddress", "s:streetAddress",
                           "vcard:street-address", "escjr:officialName", index=0)
    postCode = find_rec(node, "locn:postCode",
                        "s:postalCode", "vcard:postal-code", index=0)
    provincia = find_rec(node, "esadm:provincia", index=0)
    autonomia = find_rec(node, "esadm:autonomia", index=0)
    pais = find_rec(node, "esadm:pais", index=0)

    direccion = (tipoVia.title() + " ") if tipoVia else ""
    direccion = direccion + fullAddress
    sufijo = [i for i in (postCode, provincia, autonomia,
                          pais) if i is not None]
    if len(sufijo) > 0:
        direccion = direccion + ", " + ", ".join(sufijo)

    return direccion.strip()

if args.rpt or args.todo:
    idde = {}
    idde["provincias"] = {}

    with open("fuentes/cod_provincia.htm", 'rb') as html:
        soup = bs4.BeautifulSoup(html, "lxml")
        for tr in soup.select("table.miTabla tr"):
            tds = [td.get_text().strip() for td in tr.findAll("td")]
            if len(tds) == 2 and tds[0].isdigit():
                cod, prov = tds
                idde["provincias"][int(cod)] = prov

    todos = []

    for xls in glob("fuentes/*.xls"):
        wb = xlrd.open_workbook(xls)
        sh = wb.sheet_by_index(0)
        for rx in range(sh.nrows):
            row = [parse(c) for c in sh.row(rx)]
            if len(row) > 1 and isinstance(row[0], int):
                p = Puesto(*row)
                todos.append(p)

    for p in todos:
        data = p.__dict__
        keys = [k for k in data.keys() if k.startswith("id")
                and data[k] is not None]
        for k1 in keys:
            sufi = k1[2:]
            k2 = "de" + sufi
            if k2 in data:
                if sufi not in idde:
                    idde[sufi] = {}
                p.remove.add(k2)
                k = data[k1]
                v = data[k2]
                idde[sufi][k] = v

    for pdf in glob("fuentes/*.pdf-nolayout.txt"):
        with open(pdf, 'r') as myfile:
            pdf = myfile.read()
            flag = False
            clave = None
            key = None
            value = None
            for line in pdf.split("\n"):
                line = line.replace(
                    "RELACIÓN DE PUESTOS DE TRABAJO DE FUNCIONARIOS", "")
                line = line.strip()
                if len(line) == 0 or re_spip.match(line):
                    continue
                if line == "CLAVES UTILIZADAS":
                    flag = True
                    continue
                if line == "ÍNDICE":
                    flag = False
                if not flag:
                    continue

                m = re_categoria.match(line)
                if m or line == "RESIDENCIA:":
                    clave = None
                    key = None
                    line = m.group(1) if m else "RESIDENCIA"
                    if line in ("GENERALES", "CODIGOS DE LA UNIDADES", "CODIGOS DE LOS PUESTOS"):
                        pass
                    elif line == "TIPO DE PUESTO":
                        key = "tipoPuesto"
                    elif line == "ADSCRIPCION A ADMINISTRACION":
                        key = "adscripcionAdministrativa"
                    elif line == "ADSCRIPCION A CUERPOS":
                        key = "adscripcionCuerpo"
                    elif line == "TITULACIONES ACADEMICAS":
                        key = "titulacionAcademica"
                    elif line == "FORMACION ESPECIFICA":
                        key = "formacionEspecifica"
                    else:
                        key = line.lower()
                    continue

                if key:
                    if clave is None:
                        m = re_residencia.match(line)
                        if m:
                            clave, value = m.groups()
                        else:
                            clave = line
                    else:
                        if value is not None and value[0] == '"':
                            value = value + " " + line
                        else:
                            value = line

                    if clave and value and (value[0] != '"' or value[-1] == '"'):
                        if value.startswith('"'):
                            value = value[1:-1]
                        if key not in idde:
                            idde[key] = {}
                        idde[key][clave] = value
                        clave = None
                        value = None

    idde = Descripciones(**idde)
    idde.save()
    Puesto.save(todos, name="destinos_all")

    puestos_ok = set()
    puestos_ko = set()

    puestos = [p for p in todos if p.isTAI(puestos_ok, puestos_ko)]
    Puesto.save(puestos)

    with open("data/puestos_ok.txt", "w") as f:
        for p in sorted(puestos_ok):
            f.write(p + "\n")

    with open("data/puestos_ko.txt", "w") as f:
        for p in sorted(puestos_ko):
            f.write(p + "\n")

    dic_puestos = {str(p.idPuesto): p for p in todos}
    convocatorias = (
        (2016, 'L', 'BOE-A-2018-991'),
        (2015, 'L', 'BOE-A-2016-12467'),
    )
    for year, tipo, nombramientos in convocatorias:
        with open("fuentes/" + nombramientos + ".pdf-layout.txt", "r") as pdf:
            destinos = []
            txt = pdf.read()
            i = 0
            for m in re_puesto.findall(txt):
                i = i + 1
                p = dic_puestos[m]
                p.ranking = i
                destinos.append(p)
            Puesto.save(destinos, name=("%s_%s" % (year, tipo)))


if args.dir3 or args.todo:

    tree = ET.parse('fuentes/Unidades.rdf')
    root = tree.getroot()

    ns = {
        'escjr': 'http://vocab.linkeddata.es/datosabiertos/def/urbanismo-infraestructuras/callejero#',
        'rdf':   'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
        'locn':  'http://www.w3.org/ns/locn#',
        's': 'http://schema.org/',
        'vcard': 'http://www.w3.org/2006/vcard/ns#',
        'esadm': 'http://vocab.linkeddata.es/datosabiertos/def/sector-publico/territorio#',
        'dcterms': 'http://purl.org/dc/terms/',
        'skos': 'http://www.w3.org/2004/02/skos/core#',
        'org': 'http://www.w3.org/ns/org#',
        'orges': 'http://datos.gob.es/def/sector-publico/organizacion/',
        'rdfs': 'http://www.w3.org/2000/01/rdf-schema#',
    }

    t_dire = "http://datos.gob.es/recurso/sector-publico/Direccion/"
    t_orga = "http://datos.gob.es/recurso/sector-publico/org/Organismo/"

    direcciones = {}
    for child in root:
        about = child.attrib[full_attrib("rdf:about")]
        if about.startswith(t_dire):
            codigo = about[len(t_dire):].upper()
            direccion = parse_dire(child)
            direcciones[codigo] = direccion

    organismos = []
    for child in root:
        about = child.attrib[full_attrib("rdf:about")]
        if about.startswith(t_orga):
            orga = about[len(t_orga):].upper()
            direccion = find_rec(child, "org:siteAddress", "s:address",
                                 "locn:address", "vcard:hasAddress", index=0)
            direccion = direcciones.get(direccion, None)
            nombre = find_rec(child, "dcterms:title", "rdfs:label",
                              "s:name", "vcard:organization-name", "skos:prefLabel", index=0)
            padre = find_rec(child, "org:subOrganizationOf")
            raiz = find_rec(child, "orges:tieneUORaiz", index=0)
            o = Organismo(orga, nombre, direccion, padre, raiz)
            organismos.append(o)

    Organismo.save(organismos, name="organismos_all")

    organismos_E0 = {}
    organismos_E = []
    for o in organismos:
        if o.idOrganismo.startswith("E0"):
            org = organismos_E0.get(o.rcp, None)
            if org is None or org.version < o.version:
                organismos_E0[o.rcp] = o
        elif o.idOrganismo.startswith("EA"):
            organismos_E.append(o)

    organismos_E.extend(organismos_E0.values())
    organismos_E = sorted(
        organismos_E, key=lambda o: (o.rcp or 999999, o.idOrganismo))

    Organismo.save(organismos_E, name="organismos_E")


def tratar_gob_es(s, organismos_E, url, raiz, padre):
    print (url)
    r = s.get(url)
    content = r.content
    soup = bs4.BeautifulSoup(content, "lxml")
    for a in soup.select("a[href]"):
        a.attrs["href"] = urljoin(url, a.attrs["href"])
    codigo = None
    hijos = []
    deDireccion = None
    latlon = None
    for div in soup.select("section div"):
        for br in div.findAll("br"):
            br.replaceWith(" ")
        txt = re_bk.sub(" ", div.get_text()).strip()
        if ":" not in txt:
            continue
        key, value = [i.strip() for i in txt.split(":", 1)]
        if key == "Código de unidad orgánica":
            codigo = value
        elif key == "Estructura orgánica":
            hijos = set([a.attrs["href"].split("&")[0]
                        for a in div.findAll("a") if "idUnidOrganica=" in a.attrs["href"]])
        elif key == "Dirección":
            deDireccion = value
    if not codigo:
        return
    org = organismos_E.get(codigo, None)
    deOrganismo = re_bk.sub(
        " ", soup.select("h1.ppg-heading")[0].get_text()).strip()
    img = soup.find("img", attrs={"src": re_map})
    if img:
        latlon = re_map.search(img.attrs["src"]).group(1)
    if org is None:
        org = Organismo(codigo)
    org.idUnidOrganica = int(url.split("=")[1])
    if deOrganismo:
        org.deOrganismo = deOrganismo
    if deDireccion:
        org.deDireccion = deDireccion
    if latlon:
        org.latlon = latlon
    idPadres = org.idPadres or []
    if padre and padre not in idPadres:
        idPadres.append(padre)
        org.idPadres = idPadres
    if raiz:
        org.idRaiz = raiz
    organismos_E[codigo] = org

    for h in hijos:
        tratar_gob_es(s, organismos_E, h, raiz, codigo)


if args.gob or args.todo:
    default_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:54.0) Gecko/20100101 Firefox/54.0',
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "Expires": "Thu, 01 Jan 1970 00:00:00 GMT",
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        "X-Requested-With": "XMLHttpRequest",
    }

    s = requests.Session()
    s.headers = default_headers

    organismos_E = {
        o.idOrganismo: o for o in Organismo.load(name="organismos_E")}

    url = "https://administracion.gob.es/pagFront/espanaAdmon/directorioOrganigramas/fichaUnidadOrganica.htm?idUnidOrganica=1"
    tratar_gob_es(s, organismos_E, url, None, None)

    Organismo.save(list(organismos_E.values()), name="organismos_E")

