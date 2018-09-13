#!/usr/bin/python3
# -*- coding: utf-8 -*-
import argparse
import sys
import os
import re
import xml.etree.ElementTree as ET
from glob import glob
from math import atan2, cos, radians, sin, sqrt
from urllib.parse import unquote, urljoin

import bs4
import requests
import xlrd

from api import (Descripciones, Organismo, Puesto, dict_from_txt,
                 get_direcciones_txt, simplificar_dire, soup_from_file,
                 yaml_from_file, get_cod_dir_latlon)

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

parser = argparse.ArgumentParser(
    description='Pasa los datos fuentes a json o similares')
parser.add_argument('--todo', action='store_true', help='Autoexplicativo')
parser.add_argument('--puestos', action='store_true',
                    help='Solo genera la parte de los puestos (RPT)')
parser.add_argument(
    '--dir3', action='store_true', help='Solo genera la parte de Dir3')
parser.add_argument(
    '--csic', action='store_true', help='Solo genera la parte de Csic')
parser.add_argument('--gob', action='store_true',
                    help='Solo genera la parte de administracion.gob.es')
parser.add_argument('--fusion', action='store_true',
                    help='Fusionar organismo administracion.gob.es con dir3_E')

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
re_ll = re.compile(r"https://maps.google.es/maps\?.*&ll=([\d\.,\-]+).*")
re_ll2 = re.compile(
    r"https://www.google.com/maps/search/\?api=1&query=([\d\.,\-]+)")
re_paren = re.compile(r"\(.*$")

arregla_direcciones = get_direcciones_txt()


def parse(cell, parse_number=True):
    if not cell:
        return None
    v = cell.value
    if isinstance(v, float):
        return int(v) if v.is_integer() else v
    if isinstance(v, str):
        v = v.strip()
        v = re_space.sub(" ", v)
        v = v.replace("PROGRAMDOR", "PROGRAMADOR")
        if parse_number and re_number.match(v):
            v = float(v.replace(",", "."))
            return int(v) if v.is_integer() else v
        return v if len(v) else None
    return v

def get_sepe():
    d = {}
    with open("fuentes/sepe.txt") as y:
        for l in y.readlines():
            l = l.strip()
            if len(l)>0:
                values = []
                values = l[1:].replace('", "', '","').split('","')
                if "," in values[-1]:
                    values = values[:-1] + values[-1].split(",")
                else:
                    values = values[:-1] + [values[-1].replace('"', '')]
                d[int(values[-1])] = tuple(values[:-1])
    return d

def get_inss():
    d={}
    wb = xlrd.open_workbook("fuentes/ss.xls", logfile=open(os.devnull, 'w'))
    sh = wb.sheet_by_index(0)
    for rx in range(sh.nrows):
        row = [parse(c, parse_number=False) for c in sh.row(rx)]
        if len(row)>19 and row[3] == "INSTITUTO NACIONAL DE LA SEGURIDAD SOCIAL" and row[4]=="Direcciones Provinciales":
            cp = row[7]
            direccion = "%s, %s %s, %s" % (row[8], cp, row[2], row[1])
            latlon = "%s,%s" % (row[19], row[18])
            d[int(cp[0:2])] = (latlon, direccion, cp)
    return d

def clean_organismos(organismos, msg="Eliminando versiones antiguas de E0", otros=None):
    organismos_E = {}
    organismos_X = []

    print (msg)
    count = 0
    ok = 0
    total = len(organismos)

    for o in organismos:
        count += 1
        print("%3d%% completado: %-30s (%s)" %
              (count * 100 / total, o.idOrganismo, ok), end="\r")
        rcp, version = o.rcp, o.version
        if rcp is not None:
            orgs = organismos_E.get(rcp, set())
            orgs.add(o)
            organismos_E[rcp] = orgs
        elif otros is None or o.idOrganismo.startswith(otros):
            organismos_X.append(o)

    for rcp, orgs in organismos_E.items():
        orgs = sorted(orgs, key=lambda i: i.version, reverse=True)
        org = orgs.pop(0)
        for o in orgs:
            if org.deDireccion is None:
                org.set_lugar(o.deDireccion, o.postCode)
                org.latlon = o.latlon
            org.idPadres = org.idPadres.union(o.idPadres)
            org.codigos = org.codigos.union(o.codigos)
            if org.idRaiz is None:
                org.idRaiz = o.idRaiz
        ok += len(orgs)
        print("%3d%% completado: %-30s (%s)" %
              (count * 100 / total, o.idOrganismo, ok), end="\r")
        organismos_X.append(org)

    print("")

    return organismos_X


def clean_direccion(d):
    if not d:
        return d
    d = d.replace("Avda ", "Avenida ")

    return d

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
    return values


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
    return direccion.strip(), postCode

if args.puestos or args.todo:
    xlss = list(sorted(glob("fuentes/RPT*.xls")))
    pdfs = list(sorted(glob("fuentes/*.pdf-nolayout.txt")))

    convocatorias = (
        (2016, 'L', 'BOE-A-2018-991'),
        (2015, 'L', 'BOE-A-2016-12467'),
    )

    total = 1 + len(xlss) + len(pdfs) + len(convocatorias)
    count = 1
    print ("Leyendo puestos")
    print("%3d%% completado: cod_provincia.htm" %
          (count * 100 / total,), end="\r")

    idde = {}
    idde["provincias"] = {}

    soup = soup_from_file("fuentes/cod_provincia.htm")
    for tr in soup.select("table.miTabla tr"):
        tds = [td.get_text().strip() for td in tr.findAll("td")]
        if len(tds) == 2 and tds[0].isdigit():
            cod, prov = tds
            idde["provincias"][int(cod)] = prov

    todos = []
    organismos = {}

    for xls in xlss:
        count = count + 1
        print("%3d%% completado: %-30s" %
              (count * 100 / total, os.path.basename(xls)), end="\r")
        wb = xlrd.open_workbook(xls)
        sh = wb.sheet_by_index(0)
        for rx in range(sh.nrows):
            row = [parse(c) for c in sh.row(rx)]
            if len(row) > 1 and isinstance(row[0], int):
                p = Puesto(*row)
                todos.append(p)
                isCsic = p.idMinisterio == 47811
                if p.idMinisterio and p.idMinisterio not in organismos:
                    organismos[p.idMinisterio] = Organismo(
                        p.idMinisterio, p.deMinisterio, isCsic=isCsic)
                if p.idCentroDirectivo and p.idCentroDirectivo not in organismos:
                    idPadres = set({p.idMinisterio, })
                    organismos[p.idCentroDirectivo] = Organismo(
                        p.idCentroDirectivo, p.deCentroDirectivo, idPadres=idPadres, isCsic=isCsic)
                if p.idUnidad and p.idUnidad not in organismos:
                    idPadres = set({p.idCentroDirectivo or p.idMinisterio, })
                    organismos[p.idUnidad] = Organismo(
                        p.idUnidad, p.deUnidad, idPadres=idPadres, isCsic=isCsic)
    print("100%% completado")

    Organismo.save(list(organismos.values()), name="organismos_rpt")

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

    for pdf in pdfs:
        count = count + 1
        print("%3d%% completado: %-30s" %
              (count * 100 / total, os.path.basename(pdf)[:-13]), end="\r")
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
    print("100%% completado")
    
    idde = Descripciones(**idde)
    idde.save()
    Puesto.save(todos, name="destinos_all")

    puestos_ok = set()
    puestos_ko = set()

    puestos = [p for p in todos if p.isTAI(puestos_ok, puestos_ko)]
    print ("Comprobando vacantes")
    vacantes = [p for p in puestos if p.estado=="V"]
    id_vacantes = [str(p.idPuesto) for p in vacantes]
    re_puesto_vacante = re.compile(r"\b(" + "|".join(id_vacantes) + r")\b")
    nombramientos = list(sorted(glob("fuentes/nb_*.txt")))
    concursos = list(sorted(glob("fuentes/oc_*.txt")))
    visto_en={}
    count = 0
    ok = 0
    total = len(nombramientos) + len(concursos)
    for nb in nombramientos + concursos:
        boe = nb.split("_")[-1][:-4]
        with open(nb, "r") as txt:
            for m in re_puesto_vacante.findall(txt.read()):
                m = int(m)
                if m not in visto_en:
                    visto_en[int(m)]=boe
                    ok = ok + 1
                    print("%3d%% completado: %s (%s)" %
                          (count * 100 / total, boe, ok), end="\r")
        count = count + 1
        print("%3d%% completado: %s (%s)   " %
              (count * 100 / total, boe, ok), end="\r")
    print ("")
    total = len(vacantes)
    count = 0
    ok = 0
    with open("debug/falsas_vacantes.txt", "w") as f:
        for p in vacantes:
            boe = visto_en.get(p.idPuesto, None)
            if boe:
                f.write("%s    %s\n" % (boe, p.idPuesto))
                p.estado = boe
                ok = ok +1
            count = count + 1
            print("%3d%% completado: %s (%s)   " %
                  (count * 100 / total, p.idPuesto, ok), end="\r")
    print ("")
    
    Puesto.save(puestos)

    with open("debug/puestos_ok.txt", "w") as f:
        for p in sorted(puestos_ok):
            f.write(p + "\n")

    with open("debug/puestos_ko.txt", "w") as f:
        for p in sorted(puestos_ko):
            f.write(p + "\n")

    print ("Filtrando convocatorias")
    dic_puestos = {str(p.idPuesto): p for p in todos}
    for year, tipo, nombramientos in convocatorias:
        count = count + 1
        print("%3d%% completado: %-30s" %
              (count * 100 / total, nombramientos + ".pdf"), end="\r")
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
    print ("")


if args.csic or args.todo:
    print ("Leyendo csic.es")

    ids = []
    with open("fuentes/csic.es/ids.txt", "r") as f:
        ids = f.readlines()

    col = []
    total = len(ids)
    count = 0
    latlons = {}
    for h in ids:
        id = int(h.strip())
        soup = soup_from_file("fuentes/csic.es/id_%06d.html" % id)
        deDireccion = None
        latlon = None
        deOrganismo = re_bk.sub(" ", soup.find("h2").get_text()).strip()
        for tr in soup.findAll("tr"):
            for br in tr.findAll("br"):
                br.replaceWith(" ")
            tds = [re_bk.sub(" ", td.get_text()).strip()
                   for td in tr.findAll("td")]
            if len(tds) == 2:
                if tds[0] == "Dirección":
                    deDireccion = tds[1].replace("(ver mapa)", "").strip()
        soup = soup_from_file("fuentes/csic.es/mp_%06d.html" % id)
        a = soup.find("a", attrs={"href": re_ll})
        if a:
            latlon = re_ll.search(a.attrs["href"]).group(1)
            latlons[deDireccion] = latlon
        else:
            latlon = latlons.get(deDireccion, None)
        o = Organismo(id, deOrganismo, deDireccion, latlon=latlon, isCsic=True)
        col.append(o)
        count = count + 1
        print("%3d%% completado: %6d" %
              (count * 100 / total, id), end="\r")
    print("100%")
    Organismo.save(col, name="organismos_csic.es")


if args.dir3 or args.todo:

    print ("Leyendo Dir3 (unidades.rdf)")

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

    tree = ET.parse('fuentes/Unidades.rdf')
    root = tree.getroot()

    count = 0
    total = len(root) * 2

    direcciones = {}
    for child in root:
        count = count + 1
        codigo = None
        about = child.attrib[full_attrib("rdf:about")]
        if about.startswith(t_dire):
            codigo = about[len(t_dire):].upper()
            direccion, postCode = parse_dire(child)
            direcciones[codigo] = (direccion, postCode)
        print("%3d%% completado: %s" %
              (count * 100 / total, codigo or ""), end="\r")

    organismos = []
    for child in root:
        count = count + 1
        about = child.attrib[full_attrib("rdf:about")]
        orga = None
        if about.startswith(t_orga):
            orga = about[len(t_orga):].upper()
            direccion = find_rec(child, "org:siteAddress", "s:address",
                                 "locn:address", "vcard:hasAddress", index=0)
            direccion, postCode = direcciones.get(direccion, (None, None))
            nombre = find_rec(child, "dcterms:title", "rdfs:label",
                              "s:name", "vcard:organization-name", "skos:prefLabel", index=0)
            padre = set(find_rec(child, "org:subOrganizationOf"))
            raiz = find_rec(child, "orges:tieneUORaiz", index=0)
            o = Organismo(orga, nombre, direccion, postCode, padre, raiz)
            organismos.append(o)
        print("%3d%% completado: %s" %
              (count * 100 / total, orga or ""), end="\r")

    print ("")

    print ("Leyendo Dir3 (oficinas.rdf)")

    tree = ET.parse('fuentes/Oficinas.rdf')
    root = tree.getroot()

    ok = 0
    count = 0
    total = len(root) * 2

    direcciones = {}
    for child in root:
        count = count + 1
        codigo = None
        about = child.attrib[full_attrib("rdf:about")]
        if about.startswith(t_dire):
            codigo = about[len(t_dire):].upper()
            direccion, postCode = parse_dire(child)
            direcciones[codigo] = (direccion, postCode)
        print("%3d%% completado: %s" %
              (count * 100 / total, codigo or ""), end="\r")

    orga_dire = {}
    for child in root:
        count = count + 1
        ofic = None
        about = child.attrib[full_attrib("rdf:about")]
        if about.startswith(t_orga):
            ofic = about[len(t_orga):].upper()
            orga = find_rec(child, "org:unitOf", index=0)
            direccion = find_rec(child, "org:siteAddress", "s:address",
                                 "locn:address", "vcard:hasAddress", index=0)
            direccion, postCode = direcciones.get(direccion, (None, None))
            if direccion and orga:
                dires = orga_dire.get(orga, set())
                dires.add((direccion, postCode))
                orga_dire[orga] = dires
                ok = ok + 1
        print("%3d%% completado: %-30s (%s)" %
              (count * 100 / total, ofic or "", ok), end="\r")
    print ("")

    ok = 0
    count = 0
    total = len(organismos)

    print ("Pasando direcciones de oficinas Dir3 a organismos Dir3")
    for o in organismos:
        if o.deDireccion is None:
            dires = orga_dire.get(o.idOrganismo, None)
            if dires and len(dires) == 1:
                direccion, postCode = dires.pop()
                o.set_lugar(direccion, postCode)
                ok = ok + 1
        count = count + 1
        print("%3d%% completado: %-30s (%s)" %
              (count * 100 / total, o.idOrganismo, ok), end="\r")
    print ("")

    Organismo.save(organismos, name="organismos_dir3")

    organismos_dir3_E = clean_organismos(
        organismos, msg="Obteniendo EA y E0 en última versión", otros="EA")
    Organismo.save(organismos_dir3_E, name="organismos_dir3_E")


def tratar_gob_es(total, visto, id, raiz, padre):
    if id in visto:
        org = visto[id]
        if padre:
            org.idPadres.add(padre)
        return
    print("%3d%% completado: %6d" %
          (len(visto.keys()) * 100 / total, id), end="\r")
    soup = soup_from_file("fuentes/administracion.gob.es/id_%06d.html" % id)
    for n in soup.select(".hideAccessible"):
        n.extract()
    codigo = None
    hijos = []
    deDireccion = None
    latlon = None
    for div in soup.select("section div"):
        for br in div.findAll("br"):
            br.replaceWith(" ")
        txt = div.get_text()
        txt = re_bk.sub(" ", txt)
        txt = txt.strip()
        if ":" not in txt:
            continue
        key, value = [i.strip() for i in txt.split(":", 1)]
        if key == "Código de unidad orgánica":
            codigo = value
        elif key == "Estructura orgánica":
            hijos = set([int(a.attrs["href"].split("&")[0].split("=")[1]) for a in div.select(
                "a[href]") if "idUnidOrganica=" in a.attrs["href"]])
        elif key == "Dirección":
            deDireccion = value
    if not codigo:
        return
    deOrganismo = re_bk.sub(
        " ", soup.select("h1.ppg-heading")[0].get_text()).strip()
    img = soup.find("img", attrs={"src": re_map})
    if img:
        latlon = re_map.search(img.attrs["src"]).group(1)
    org = Organismo(codigo, deOrganismo, deDireccion,
                    latlon=latlon, idRaiz=raiz, idUnidOrganica=id)
    visto[id] = org
    for h in hijos:
        tratar_gob_es(total, visto, h, raiz, codigo)

if args.gob or args.todo:
    print ("Leyendo administracion.gob.es")

    ids = []
    with open("fuentes/administracion.gob.es/ids.txt", "r") as f:
        ids = f.readlines()

    visto = {}
    total = len(ids)
    for h in ids:
        id = int(h.strip())
        tratar_gob_es(total, visto, id, None, None)
    print("100%")  # completado" + (" " * 10))

    organismos = list(visto.values())
    total = len(organismos)
    count = 0
    ok = 0
    print ("Sacando direcciones de oficinas")
    for o in organismos:
        if o.deDireccion is None:
            fname = "fuentes/administracion.gob.es/of_%06d.html" % o.idUnidOrganica
            if os.path.isfile(fname):
                soup = soup_from_file(
                    "fuentes/administracion.gob.es/of_%06d.html" % o.idUnidOrganica)
                latlons = set()
                direcis = set()
                for a in soup.findAll("a", attrs={"href": re_ll2}):
                    latlon = re_ll2.search(a.attrs["href"]).group(1)
                    latlons.add(latlon)
                for h4 in soup.findAll("h4", text="Dirección:"):
                    ul = h4.find_parent("ul")
                    h4.extract()
                    a = ul.find("a")
                    if a:
                        a.extract()
                    for br in ul.findAll("br"):
                        br.replaceWith(" ")
                    txt = ul.get_text()
                    txt = re_bk.sub(" ", txt)
                    txt = txt.strip()
                    direcis.add(txt)
                if len(latlons) == 1 and len(direcis) == 1:
                    deDireccion = direcis.pop()
                    o.set_lugar(deDireccion)
                    o.latlon = latlons.pop()
                    ok = ok + 1
        count = count + 1
        print("%3d%% completado: %6d (%s)" %
              (count * 100 / total, id, ok), end="\r")
    print ("")
    organismos = clean_organismos(organismos)
    Organismo.save(organismos, name="organismos_gob.es")


if args.fusion or args.todo:
    print ("Fusionando organismo administracion.gob.es con dir3_E")

    organismos_dir3_E = Organismo.load(
        name="organismos_dir3_E", arregla_direcciones=arregla_direcciones)
    organismos_gob_es = Organismo.load(
        name="organismos_gob.es", arregla_direcciones=arregla_direcciones)

    organismos_dir3_E_dict = {o.idOrganismo: o for o in organismos_dir3_E}
    organismos_gob_es_dict = {o.idOrganismo: o for o in organismos_gob_es}
    organismos_dir3_E_dict2 = {o.rcp: o for o in organismos_dir3_E if o.rcp}
    organismos_gob_es_dict2 = {o.rcp: o for o in organismos_gob_es if o.rcp}

    codigos_dir3_E = set([o.idOrganismo for o in organismos_dir3_E])
    codigos_gob_es = set([o.idOrganismo for o in organismos_gob_es])
    codigos_comun = codigos_dir3_E.intersection(codigos_gob_es)

    rcp_dir3_E = set(
        [o.rcp for o in organismos_dir3_E if o.rcp and o.idOrganismo not in codigos_comun])
    rcp_gob_es = set(
        [o.rcp for o in organismos_gob_es if o.rcp and o.idOrganismo not in codigos_comun])
    rcp_comun = rcp_dir3_E.intersection(rcp_gob_es)

    count = 0
    ok = 0
    total = len(codigos_comun) + len(rcp_comun)

    organismos = set()
    for id in list(codigos_comun.union(rcp_comun)):
        org_dir3_E = organismos_dir3_E_dict[id] if isinstance(
            id, str) else organismos_dir3_E_dict2[id]
        org_gob_es = organismos_gob_es_dict[id] if isinstance(
            id, str) else organismos_gob_es_dict2[id]
        codigos_comun.add(org_dir3_E.idOrganismo)
        codigos_comun.add(org_gob_es.idOrganismo)

        org_gob_es.idPadres = org_gob_es.idPadres.union(org_dir3_E.idPadres)
        if org_gob_es.idRaiz is None:
            org_gob_es.idRaiz = org_dir3_E.idRaiz
        if org_gob_es.deDireccion is None:
            org_gob_es.set_lugar(org_dir3_E.deDireccion, org_dir3_E.postCode)
        elif org_dir3_E.postCode is not None and org_dir3_E.postCode in org_gob_es.deDireccion:
            org_gob_es.postCode = org_dir3_E.postCode
        organismos.add(org_gob_es)
        ok += 1
        count += 1
        print("%3d%% completado: %-30s (%s)" %
              (count * 100 / total, org_gob_es.idOrganismo, ok), end="\r")
    print ("")

    organismos_dir3_E = [
        o for o in organismos_dir3_E if o.idOrganismo not in codigos_comun]
    organismos_gob_es = [
        o for o in organismos_gob_es if o.idOrganismo not in codigos_comun]

    dict_organi_rpt = {
        o.idOrganismo: o for o in Organismo.load(name="organismos_rpt")}
    for o in organismos_dir3_E + organismos_gob_es:
        orga_rpt = dict_organi_rpt.get(o.rcp, None)
        if orga_rpt:
            o.nombres = o.nombres.union(orga_rpt.nombres)

    count = 0
    ok = 0
    total = len(organismos_gob_es)

    descartar = set()
    candidatas = {}

    # Si solo hay uno que se llama igual es que es el mismo
    # si hay varios, pero solo uno de ellos esta en el mismo sitio es que es
    # el mismo
    for o in organismos_gob_es:
        count += 1
        print("%3d%% completado: %-30s (%s)" %
              (count * 100 / total, o.idOrganismo, ok), end="\r")
        orgs = set()
        orgs_mismo_nombre = set()
        o_deDirecion = o.dire
        for n in organismos_dir3_E:
            if o.nombres.intersection(n.nombres):
                orgs_mismo_nombre.add(n)
                if o.deDireccion is None and n.deDireccion is None:
                    orgs.add(n)
                elif o.deDireccion is not None and n.deDireccion:
                    if n.postCode is None or n.postCode in o.deDireccion:
                        deDireccion = n.dire
                        deDireccion = deDireccion.split(",")[0]
                        if o_deDirecion.startswith(deDireccion):
                            orgs.add(n)
        if len(orgs) == 0 and len(orgs_mismo_nombre) == 1:
            orgs = orgs_mismo_nombre
        if len(orgs) == 1:
            n = orgs.pop()
            orgs = candidatas.get(n, set())
            orgs.add(o)
            candidatas[n] = orgs
    for n, orgs in candidatas.items():
        if len(orgs) == 1:
            o = orgs.pop()
            o.postCode = n.postCode
            o.codigos.add(n.idOrganismo)
            o.idPadres = o.idPadres.union(n.idPadres)
            if o.deDireccion is None:
                o.set_lugar(n.deDireccion, n.postCode)
            descartar.add(o)
            descartar.add(n)
            organismos.add(o)
            ok += 1
            print("%3d%% completado: %-30s (%s)" %
                  (count * 100 / total, o.idOrganismo, ok), end="\r")
    print("")
    for o in organismos_gob_es + organismos_dir3_E:
        if o not in descartar:
            organismos.add(o)

    count = 0
    ok = 0
    orgs_con_dire = []
    orgs_sin_dire = []

    for o in organismos:
        o.genera_codigos()
        if o.deDireccion:
            orgs_con_dire.append(o)
        else:
            orgs_sin_dire.append(o)

    total = len(orgs_sin_dire)
    for o in orgs_sin_dire:
        orgs_mismo_nombre = set()
        orgs_mismo_padre = set()
        dires = set()
        for n in orgs_con_dire:
            if n != o and n.nombres.intersection(o.nombres):
                orgs_mismo_nombre.add(n)
                dires.add(n.deDireccion)
                if o.idPadres.intersection(n.idPadres):
                    orgs.add(n)
        orgs = orgs_mismo_padre if len(
            orgs_mismo_padre) == 1 else orgs_mismo_nombre
        if len(orgs) == 1:
            n = orgs.pop()
            deDireccion = n.deDireccion
            postCode = o.postCode or n.postCode
            o.set_lugar(deDireccion, postCode)
            n.set_lugar(deDireccion, postCode)
            if o.latlon is None or n.latlon is None:
                latlon = o.latlon or n.latlon
                o.latlon = latlon
                n.latlon = latlon
            ok += 1
        elif len(dires) == 1:
            deDireccion = dires.pop()
            o.set_lugar(deDireccion)
            ok += 1
        count += 1
        print("%3d%% completado: %-30s (%s)" %
              (count * 100 / total, o.idOrganismo, ok), end="\r")
    print ("")
    Organismo.save(organismos, name="organismos_dir3_E_gob.es",
                   arregla_direcciones=arregla_direcciones)

codigos_tai = set()
for p in Puesto.load():
    codigos_tai.add(p.idMinisterio)
    codigos_tai.add(p.idCentroDirectivo)
    codigos_tai.add(p.idUnidad)

organismos = Organismo.load(name="organismos_dir3_E_gob.es")

organismos_rpt = [o for o in Organismo.load(
    name="organismos_rpt") if o.idOrganismo in codigos_tai]

# Arreglos hechos a mano
dict_organismos = {o.idOrganismo: o for o in organismos}
dict_organi_rpt = {o.idOrganismo: o for o in organismos_rpt}
arreglos = yaml_from_file("arreglos/rpt_dir3.yml")



rcp_organi = {}
for o in organismos:
    o.genera_codigos()
    for c in o.codigos:
        if isinstance(c, int):
            rcp_organi[c] = o

print ("Añadiendo arreglos manuales")
count = 0
total = len(arreglos)
fusionados = set()

for rpt, org in arreglos.items():
    count += 1
    rpt_cod = rpt
    org = dict_organismos.get(org, None)
    rpt = dict_organi_rpt.get(rpt, None)
    rcp_org = rcp_organi.get(rpt_cod, None)
    if org and rpt:
        '''
        if rcp_org:
            if org.deDireccion and rcp_org.deDireccion and org.deDireccion!=rcp_org.deDireccion:
                print (org.latlon or rcp_org.latlon)
                print (org.deDireccion)
                print (rcp_org.deDireccion)
                print("")
        if rpt.idOrganismo in org.codigos:
            print ("%s: %s" % (rpt_cod, org.idOrganismo))
        '''
        
        org.codigos.add(rpt.idOrganismo)
        org.idPadres = org.idPadres.union(rpt.idPadres)
        for o in organismos:
            if o != org and rpt_cod in o.codigos:
                org.codigos = org.codigos.union(o.codigos)
                org.idPadres = org.idPadres.union(o.idPadres)
                fusionados.add(o)
    print("%3d%% completado: %-30s" % (count * 100 / total, str(rpt_cod) + " -> " + org.idOrganismo), end="\r")
print("")
#sys.exit()
organismos = [o for o in organismos if o not in fusionados]

rcp_ok = set()
for o in organismos:
    o.genera_codigos()
    for c in o.codigos:
        if isinstance(c, int):
            rcp_ok.add(c)

excluir_rpt = set([o.rcp for o in organismos if o.rcp and o.latlon])
codigos_tai = codigos_tai - excluir_rpt
organismos_rpt = [
    o for o in organismos_rpt if o.isCsic or o.idOrganismo in codigos_tai]

# Si con padre común solo hay un rpt con ese nombre es que es el mismo
# organismo

print ("Fusionando organismos dir3_E/administracion.gob.es con rpt")
total = len(organismos)
ok = 0

repetir = True
while repetir:
    repetir = False
    count = 0
    excluir_rpt_1 = set([o.rcp for o in organismos if o.rcp])
    excluir_rpt_2 = set(
        [o.rcp for o in organismos if o.rcp and o.idUnidOrganica])
    candidatas = {}
    for o in organismos:
        count += 1
        print("%3d%% completado: %-30s (%s)" %
              (count * 100 / total, o.idOrganismo, ok), end="\r")
        o.genera_codigos()
        orgs = set()
        for n in organismos_rpt:
            if o.nombres.intersection(n.nombres) and n.idPadres.intersection(o.idPadres):
                orgs.add(n)
        if len(orgs) == 1:
            n = orgs.pop()
            if not n.latlon and n.idOrganismo in excluir_rpt_2:
                continue
            if not n.idUnidOrganica and n.idOrganismo in excluir_rpt_1:
                continue
            orgs = candidatas.get(n, set())
            orgs.add(o)
            candidatas[n] = orgs

    for n, orgs in candidatas.items():
        if len(orgs) == 1:
            ok += 1
            print("%3d%% completado: %-30s (%s)" %
                  (count * 100 / total, o.idOrganismo, ok), end="\r")
            o = orgs.pop()
            o.codigos.add(n.idOrganismo)
            antes = len(o.idPadres)
            o.idPadres = o.idPadres.union(n.idPadres)
            o.genera_codigos()
            if antes < len(o.idPadres):
                repetir = True
    print ("")

for o in organismos:
    o.genera_codigos()

print ("Fusionando organismos con csic.es")
arreglos = yaml_from_file("arreglos/rpt_csic.yml")
organismos_csic = {o.idOrganismo: o for o in Organismo.load(
    name="organismos_csic.es", arregla_direcciones=arregla_direcciones)}
codigos_csic = set([o.idOrganismo for o in organismos_rpt if o.isCsic])
total = len(organismos)
ok = 0
count = 0
for o in organismos:
    if o.codigos.intersection(codigos_csic):
        o.isCsic = True
        org_csic = arreglos.get(o.rcp, None)
        org_csic = organismos_csic.get(org_csic, None)
        if org_csic is None:
            orgs = set()
            for n in organismos_csic.values():
                if o.nombres.intersection(n.nombres):
                    orgs.add(n)
            if len(orgs) == 1:
                org_csic = orgs.pop()
        if org_csic:
            o.idCsic = org_csic.idOrganismo
            o.deOrganismo = org_csic.deOrganismo
            o.set_lugar(org_csic.deDireccion, org_csic.postCode)
            o.latlon = org_csic.latlon
            ok += 1
    count += 1
    print("%3d%% completado: %-30s (%s)" %
          (count * 100 / total, o.idOrganismo, ok), end="\r")
print ("")


rcp_organi = {}
for o in organismos:
    o.genera_codigos()
    for c in o.codigos:
        if isinstance(c, int):
            rcp_organi[c] = o

print ("Seteando provincias")
puestos = Puesto.load("destinos_all")
total = len(puestos)
count = 0
unidades_provincia = {}
for p in puestos:
    if p.idUnidad:
        provincias = unidades_provincia.get(p.idUnidad, set())
        provincias.add(p.provincia)
        unidades_provincia[p.idUnidad] = provincias
    if p.idCentroDirectivo:
        provincias = unidades_provincia.get(p.idCentroDirectivo, set())
        provincias.add(p.provincia)
        unidades_provincia[p.idCentroDirectivo] = provincias
    if p.idMinisterio:
        provincias = unidades_provincia.get(p.idMinisterio, set())
        provincias.add(p.provincia)
        unidades_provincia[p.idMinisterio] = provincias
    count += 1
    print("%3d%% completado: %s" % (count * 100 / total, p.idPuesto), end="\r")
print ("")

total = len(unidades_provincia)
count = 0
ok = 0
for unidad, provincias in unidades_provincia.items():
    if len(provincias) == 1:
        provincia = provincias.pop()
        if provincia is not None:
            org = rcp_organi.get(unidad, None)
            if org and org.idProvincia is None:
                org.idProvincia = provincia
                ok += 1
    count += 1
    print("%3d%% completado: %-30s (%s)" %
          (count * 100 / total, o.idOrganismo, ok), end="\r")
print ("")

sepe=get_sepe()
total = len(organismos)
ok = 0
count = 0
print ("Fusionando con sepe.es")
for o in organismos:
    if o.deOrganismo.startswith("Direccion Provincial del SEPE de ") and o.idProvincia:
        s = sepe.get(o.idProvincia, None)
        if s:
            latlon, _, dire, codpostal, prov = s[:5]
            o.set_lugar(dire+", "+codpostal+" "+prov, codpostal)
            o.latlon = latlon
            ok += 1
    count += 1
    print("%3d%% completado: %-30s (%s)" %
          (count * 100 / total, o.idOrganismo, ok), end="\r")
print("")

inss=get_inss()
total = len(organismos)
ok = 0
count = 0
print ("Fusionando con INSS")
for o in organismos:
    if o.deOrganismo.startswith("Direccion Provincial del Inss de ") and not o.idProvincia:
        print(o.deOrganismo)
    if o.deOrganismo.startswith("Direccion Provincial del Inss de ") and o.idProvincia:
        s = inss.get(o.idProvincia, None)
        if s:
            latlon, dire, codpostal = s[:5]
            o.set_lugar(dire, codpostal)
            o.latlon = latlon
            ok += 1
    count += 1
    print("%3d%% completado: %-30s (%s)" % (count * 100 / total, o.idOrganismo, ok), end="\r")
print("")

print ("Asignando direcciones manuales")
cod_dir_latlon = get_cod_dir_latlon()
total = len(cod_dir_latlon)
count = 0
ok = 0
for k, v in cod_dir_latlon.items():
    org = rcp_organi.get(k, None)
    if org:
        latlon, deDireccion = v
        org.latlon = latlon
        org.set_lugar(deDireccion)
        ok = ok + 1
    count = count + 1
    print("%3d%% completado: %-30s (%s)" %
          (count * 100 / total, k, ok), end="\r")
print ("")

print ("Normalizando direcciones")
organismos_gob_es = Organismo.load(name="organismos_gob.es")
organismos_csic = Organismo.load(name="organismos_csic.es")
total = len(organismos_gob_es) + len(organismos_csic)
count = 0
ok = 0

direcciones = dict_from_txt("arreglos/dir_latlon.txt",
                            rever=True, parse_key=simplificar_dire)
direcciones = {k: set((v,)) for k, v in direcciones.items()}
for o in organismos_gob_es + organismos_csic:
    if o.latlon:
        latlon = direcciones.get(o.dire, set())
        latlon.add(o.latlon)
        direcciones[o.dire] = latlon
        ok += 1
    count += 1
    print("%3d%% completado: %-30s (%s)" %
          (count * 100 / total, o.idOrganismo, ok), end="\r")
print ("")

for k, v in list(direcciones.items()):
    if len(v) == 1:
        direcciones[k] = v.pop()
    else:
        del direcciones[k]

print ("Completando latlon con excel")
xls_info = {}
url = "https://docs.google.com/spreadsheet/ccc?key=18GC2-xHj-n2CAz84DkWVy-9c8VpMKhibQanfAjeI4Wc&output=xls"
r = requests.get(url)
wb = xlrd.open_workbook(file_contents=r.content)
sh = wb.sheet_by_index(1)
total = sh.nrows
count = 0
ok = 0
ok2 = 0
dire_xls = set()
for rx in range(sh.nrows):
    row = [parse(c) for c in sh.row(rx)]
    dire, latlon, machacar = row[10], row[12], row[17]
    if dire and latlon:
        idMinisterio, idCentroDirectivo, idUnidad = row[2], row[6], row[8]
        if idMinisterio:
            xls_info[idMinisterio] = (dire, latlon, None)
        if idCentroDirectivo:
            xls_info[idCentroDirectivo] = (dire, latlon, idMinisterio)
        if idUnidad:
            xls_info[idUnidad] = (dire, latlon, idCentroDirectivo or idMinisterio)
            if machacar == "SI":
                org = rcp_organi.get(idUnidad, None)
                org.set_lugar(dire)
                org.latlon=latlon
                ok2 += 1
        dire = simplificar_dire(dire)
        if dire not in direcciones:
            direcciones[dire] = latlon
            dire_xls.add(dire)
            ok += 1
    count += 1
    print("%3d%% completado: %-30s (%s / %s)" %
          (count * 100 / total, (dire or "")[:30], ok, ok2), end="\r")
print ("")

count = 0
ok = 0
total = len(xls_info)
for k, v in xls_info.items():
    org = rcp_organi.get(k, None)
    if org:
        dire, latlon, padre = v
        x_p = xls_info.get(padre, None)
        o_p = rcp_organi.get(padre, None)
        if not(x_p is not None and x_p[1] == latlon):
            # Si la dirección es la misma que el organismos padre
            # no puedo saber si se le ha asignado porque es suya
            # o porque es del padre y él realmente no tiene
            if not org.latlon:
                org.set_lugar(dire)
                org.latlon = latlon
                ok += 1
    count += 1
    print("%3d%% completado: %-30s (%s)" %
          (count * 100 / total, k, ok), end="\r")
print ("")

print ("Seteando latlon")
total = len(organismos)
count = 0
ok = 0
sin_latlon = set()
for o in organismos:
    if not o.latlon and o.deDireccion:
        latlon = direcciones.get(o.dire, None)
        if latlon:
            o.latlon = latlon
            ok += 1
        else:
            sin_latlon.add(o.dire)
    count += 1
    print("%3d%% completado: %-30s (%s)" %
          (count * 100 / total, o.idOrganismo, ok), end="\r")
print ("")

Organismo.save(organismos, arregla_direcciones=arregla_direcciones)

tai_latlons = set(
    [o.latlon for o in organismos if o.latlon and o.codigos.intersection(codigos_tai)])
latlons = {}
direcis = {}
for o in organismos:
    # if o.latlon:
    if o.latlon in tai_latlons:
        dires = latlons.get(o.latlon, set())
        dires.add(o.deDireccion)
        latlons[o.latlon] = dires
        lls = direcis.get(o.dire, set())
        lls.add(o.latlon)
        direcis[o.dire] = lls

with open("debug/direcciones_duplicadas.txt", "w") as f:
    for dire, lls in sorted(direcis.items()):
        if len(lls) > 1:
            f.write(dire + "\n")
            for ll in sorted(lls):
                f.write(ll + "\n")
            f.write("\n")
    for latlon, dires in sorted(latlons.items()):
        if len(dires) > 1:
            f.write(latlon + "\n")
            for d in sorted(dires):
                f.write(d + "\n")
            f.write("\n")

with open("debug/direcciones_ko.txt", "w") as f:
    for d in sorted(sin_latlon):
        f.write(d + "\n")


def calcula_distancia(latlon1, latlon2):
    R = 6373.0

    lat, lon = latlon1.split(",")

    lat1 = radians(float(lat))
    lon1 = radians(float(lon))

    lat, lon = latlon2.split(",")

    lat2 = radians(float(lat))
    lon2 = radians(float(lon))

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = abs(R * c) * 1000
    return int(distance)

rcp_organi = {}
for o in organismos:
    o.genera_codigos()
    if o.latlon:
        for c in o.codigos:
            if isinstance(c, int):
                rcp_organi[c] = o

with open("debug/direcciones.csv", "w") as f:
    f.write("\t".join(["Metros", "ID", "Dir3",
                       "LATLON", "EXCEL", "LATLON"]) + "\n")
    for id, dirll in xls_info.items():
        org = rcp_organi.get(id, None)
        if org:
            dire, ll, _ = dirll
            distancia = calcula_distancia(ll, org.latlon)
            f.write("\t".join([str(distancia), str(id),
                               org.deDireccion, org.latlon, dire, ll]) + "\n")

direcciones = sorted(set([o.deDireccion for o in organismos if o.deDireccion]))
with open("debug/direcciones.txt", "w") as f:
    for d in direcciones:
        f.write(d + "\n")

metros = 30
last_latlon = None
latlons = sorted(tai_latlons, key=lambda i: [float(l) for l in i.split(",")])
with open("debug/latlons.txt", "w") as f:
    for l in latlons:
        if last_latlon and calcula_distancia(l, last_latlon)<metros:
            f.write("<%sm\n" % metros)
        f.write(l + "\n")
        for d in sorted(set([o.deDireccion for o in organismos if o.latlon==l])):
            f.write(d + "\n")
        f.write("\n")
        last_latlon = l
