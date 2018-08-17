#!/usr/bin/python3
# -*- coding: utf-8 -*-
import io
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from glob import glob
from urllib.parse import unquote

import bs4
import requests
import xlrd

from api import Descripciones, Organismo, Puesto

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

re_space = re.compile(r"  +")
re_number = re.compile(r"^\d+,\d+$")
re_categoria = re.compile(r"^\s*\d+\.\s*-\s*(.+)\s*:\s*$")
re_spip = re.compile(r"^\s*(Página:|Fecha:|\d+/\d+/20\d+|\d+ de \d+)\s*$")
re_residencia = re.compile(r"^\s*(\d+-\d+-\d+)\s+([A-Z].*)\s*$")
re_sp = re.compile(r"  +")
re_puesto = re.compile(r"\b(\d{7})\b")


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
    'orges': 'http://datos.gob.es/def/sector-publico/organizacion/'
}

t_dire = "http://datos.gob.es/recurso/sector-publico/Direccion/"
t_orga = "http://datos.gob.es/recurso/sector-publico/org/Organismo/"


def full_attrib(attrib):
    prefix, name = attrib.split(":")
    attrib = "{%s}%s" % (ns[prefix], name)
    return attrib


def _find_rec(node, tag):
    r = node.find(tag, ns)
    if r is not None:
        if r.text is None:
            r = r.attrib.get(full_attrib("rdf:resource"), None)
            if r is not None:
                return unquote(r.split("/")[-1])
        return r.text
    for child in node:
        r = _find_rec(child, tag)
        if r is not None:
            return r
    return None


def find_rec(node, *args):
    for tag in args:
        r = _find_rec(node, tag)
        if r:
            r = r.replace("-", " ")
            r = re_sp.sub(" ", r)
            r = r.strip()
            return r
    return None


def parse_dire(node):
    tipoVia = find_rec(node, "escjr:tipoVia")
    fullAddress = find_rec(node, "locn:fullAddress", "s:streetAddress",
                           "vcard:street-address", "escjr:officialName")
    postCode = find_rec(node, "locn:postCode",
                        "s:postalCode", "vcard:postal-code")
    provincia = find_rec(node, "esadm:provincia")
    autonomia = find_rec(node, "esadm:autonomia")
    pais = find_rec(node, "esadm:pais")

    direccion = (tipoVia.title() + " ") if tipoVia else ""
    direccion = direccion + fullAddress
    sufijo = [i for i in (postCode, provincia, autonomia,
                          pais) if i is not None]
    if len(sufijo)>0:
        direccion = direccion + ", " + ", ".join(sufijo)

    return direccion.strip()

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
                             "locn:address", "vcard:hasAddress")
        if direccion is not None:
            nombre = find_rec(child, "dcterms:title", "rdfs:label",
                              "s:name", "vcard:organization-name", "skos:prefLabel")
            padre = find_rec(child, "org:subOrganizationOf")
            raiz = find_rec(child, "orges:tieneUORaiz")            
            o = Organismo(orga, nombre, direccion, direcciones[direccion], padre, raiz)
            organismos.append(o)

Organismo.save(organismos, name="organismos_all")

organismos_E0 = {}
for o in organismos:
    if o.idOrganismo.startswith("E0"):
        org = organismos_E0.get(o.rcp, None)
        if org is None or org.version < o.version:
            organismos_E0[o.rcp] = o

organismos_E0 = sorted(organismos_E0.values(), key=lambda o: o.rcp)

Organismo.save(organismos_E0, name="organismos_E0")

dic_puestos = {str(p.idPuesto): p for p in todos}
convocatorias = (
    (2016, 'L', 'BOE-A-2018-991'),
    (2015, 'L', 'BOE-A-2016-12467'),
)
for year, tipo, nombramientos in convocatorias:
    with open("fuentes/"+nombramientos+".pdf-layout.txt", "r") as pdf:
        destinos=[]
        txt = pdf.read()
        i = 0
        for m in re_puesto.findall(txt):
            i = i + 1
            p = dic_puestos[m]
            p.ranking = i
            destinos.append(p)
        Puesto.save(destinos, name=("%s_%s" % (year, tipo)))
