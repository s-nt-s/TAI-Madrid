#!/usr/bin/python3
# -*- coding: utf-8 -*-
import argparse
import os
import re
import xml.etree.ElementTree as ET
from glob import glob
from urllib.parse import unquote, urljoin
import sys

import bs4
import xlrd

from api import Descripciones, Organismo, Puesto, soup_from_file, yaml_from_file

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
parser.add_argument('--fusion1', action='store_true',
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
re_paren=re.compile(r"\(.*$")


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
    xlss = list(sorted(glob("fuentes/*.xls")))
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
                    organismos[p.idMinisterio] = Organismo(p.idMinisterio, p.deMinisterio, isCsic=isCsic)
                if p.idCentroDirectivo and p.idCentroDirectivo not in organismos:
                    idPadres = set({p.idMinisterio,})
                    organismos[p.idCentroDirectivo] = Organismo(p.idCentroDirectivo, p.deCentroDirectivo, idPadres=idPadres, isCsic=isCsic)
                if p.idUnidad and p.idUnidad not in organismos:
                    idPadres = set({p.idCentroDirectivo or p.idMinisterio,})
                    organismos[p.idUnidad] = Organismo(p.idUnidad, p.deUnidad, idPadres=idPadres, isCsic=isCsic)

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
              (count * 100 / total, os.path.basename(xls)[:-13]), end="\r")
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
    for h in ids:
        id = int(h.strip())
        soup = soup_from_file("fuentes/csic.es/id_%06d.html" % id)
        deDireccion = None
        latlon = None
        deOrganismo = re_bk.sub(" ", soup.find("h2").get_text()).strip()
        for tr in soup.findAll("tr"):
            tds = [re_bk.sub(" ", td.get_text()).strip() for td in tr.findAll("td")]
            if len(tds)==2:
                if tds[0] == "Dirección":
                    deDireccion = tds[1].replace("(ver mapa)","").strip()
        soup = soup_from_file("fuentes/csic.es/mp_%06d.html" % id)
        a = soup.find("a", attrs={"href": re_ll})
        if a:
            latlon = re_ll.search(a.attrs["href"]).group(1)
        o = Organismo(id, deOrganismo, deDireccion, latlon=latlon, isCsic=True)
        col.append(o)
        count = count + 1
        print("%3d%% completado: %6d" %
              (count * 100 / total, id), end="\r")
    print("100%")
    Organismo.save(col, name="organismos_csic.es")
    

if args.dir3 or args.todo:

    print ("Leyendo Dir3")
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

    count = 0
    total = len(root) * 2

    direcciones = {}
    for child in root:
        count = count + 1
        about = child.attrib[full_attrib("rdf:about")]
        print("%3d%% completado" % (count * 100 / total,), end="\r")
        if about.startswith(t_dire):
            codigo = about[len(t_dire):].upper()
            direccion, postCode = parse_dire(child)
            direcciones[codigo] = (direccion, postCode)
            print("%3d%% completado: %s" %
                  (count * 100 / total, codigo), end="\r")

    organismos = []
    for child in root:
        count = count + 1
        about = child.attrib[full_attrib("rdf:about")]
        print("%3d%% completado" % (count * 100 / total,), end="\r")
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
                  (count * 100 / total, orga), end="\r")

    print ("")
    Organismo.save(organismos, name="organismos_dir3")

    print ("Obteniendo EA y E0 en última versión")
    count = 0
    ok = 0
    total = len(organismos)

    organismos_dir3_E0 = {}
    organismos_dir3_E = []
    for o in organismos:
        count += 1
        print("%3d%% completado: %-30s (%s)" %
              (count * 100 / total, o.idOrganismo, ok), end="\r")
        rcp, version = o.rcp, o.version
        if rcp is not None:
            org = organismos_dir3_E0.get(rcp, None)
            v = org.version if org else None
            if v is None or v < version:
                if v is None:
                    ok = ok + 1
                organismos_dir3_E0[rcp] = o
        elif o.idOrganismo.startswith("EA"):
            organismos_dir3_E.append(o)
            ok = ok +1

    print("")

    organismos_dir3_E.extend(organismos_dir3_E0.values())
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
    org = Organismo(codigo, deOrganismo, deDireccion, latlon=latlon, idRaiz=raiz, idUnidOrganica=id)
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
    print("100%")# completado" + (" " * 10))
    Organismo.save(list(visto.values()), name="organismos_gob.es")


if args.fusion1 or args.todo:
    organismos_dir3_E = Organismo.load(name="organismos_dir3_E")
    organismos_gob_es = Organismo.load(name="organismos_gob.es")
    dict_organi_rpt = {o.idOrganismo: o for o in Organismo.load(name="organismos_rpt")}
    for o in organismos_dir3_E + organismos_gob_es:
        orga_rpt = dict_organi_rpt.get(o.rcp, None)
        if orga_rpt:
            o.nombres = o.nombres.union(orga_rpt.nombres)

    cod_gob_es = set([o.idOrganismo for o in organismos_gob_es])

    print ("Fusionando organismo administracion.gob.es con dir3_E")
    count = 0
    ok = 0
    total = len(organismos_gob_es)

    fusionado = set()

    # Si solo hay uno que se llama igual es que es el mismo
    # si hay varios, pero solo uno de ellos esta en el mismo sitio es que es el mismo
    for o in organismos_gob_es:
        count += 1
        print("%3d%% completado: %-30s (%s)" %
              (count * 100 / total, o.idOrganismo, ok), end="\r")
        orgs = set()
        orgs_mismo_nombre = set()
        o_deDirecion = o.dire
        for n in organismos_dir3_E:
            if n.idOrganismo == o.idOrganismo:
                ok += 1
                o.idPadres = o.idPadres.union(n.idPadres)
                fusionado.add(n.idOrganismo)
                if n.postCode is not None and o.deDireccion is not None and n.postCode in o.deDireccion:
                    o.postCode = n.postCode
            elif n.idOrganismo not in cod_gob_es and o.nombres.intersection(n.nombres):
                orgs_mismo_nombre.add(n)
                if o.deDireccion is None and n.deDireccion is None:
                    orgs.add(n)
                elif o.deDireccion is not None:
                    orgs_mismo_nombre.add(n)
                    if n.deDireccion:
                        if n.postCode is None or n.postCode in o.deDireccion:
                            deDireccion = n.dire
                            deDireccion = deDireccion.split(",")[0]
                            if o_deDirecion.startswith(deDireccion):
                                orgs.add(n)
        if len(orgs)==0 and len(orgs_mismo_nombre)==1:
            orgs = orgs_mismo_nombre
        if len(orgs)==1:
            ok += 1
            n = orgs.pop()
            o.postCode = n.postCode
            o.codigos.add(n.idOrganismo)
            o.idPadres = o.idPadres.union(n.idPadres)
            if n.deDireccion is not None and o.deDireccion is None:
                o.deDireccion = n.deDireccion

    print("")

    organismos = organismos_gob_es + [o for o in organismos_dir3_E if o.idOrganismo not in fusionado]

    Organismo.save(organismos, name="organismos_dir3_E_gob.es")

codigos_tai = set()
for p in Puesto.load():
    codigos_tai.add(p.idMinisterio)
    codigos_tai.add(p.idCentroDirectivo)
    codigos_tai.add(p.idUnidad)

organismos = Organismo.load(name="organismos_dir3_E_gob.es")

organismos_rpt = [o for o in Organismo.load(name="organismos_rpt") if o.idOrganismo in codigos_tai]

# Arreglos hechos a mano
dict_organismos = {o.idOrganismo: o for o in organismos}
dict_organi_rpt = {o.idOrganismo: o for o in organismos_rpt}
arreglos = yaml_from_file("data/arreglos.yml")


print ("Añadiendo arreglos manuales")
count = 0
total = len(arreglos)
fusionados = set()

for rpt, org in arreglos.items():
    count += 1
    rpt_cod = rpt
    print("%3d%% completado: %-30s" %
          (count * 100 / total, str(rpt)+" -> "+org), end="\r")
    org = dict_organismos.get(org, None)
    rpt = dict_organi_rpt.get(rpt, None)
    if org and rpt:
        org.codigos.add(rpt.idOrganismo)
        org.idPadres = org.idPadres.union(rpt.idPadres)
        for o in organismos:
            if o!=org and rpt_cod in o.codigos:
                org.codigos = org.codigos.union(o.codigos)
                org.idPadres = org.idPadres.union(o.idPadres)
                fusionados.add(o)
print("")
organismos = [o for o in organismos if o not in fusionados]


excluir_rpt = set([o.rcp for o in organismos if o.rcp and o.latlon])
codigos_tai = codigos_tai - excluir_rpt
organismos_rpt = [o for o in organismos_rpt if o.idOrganismo in codigos_tai]

# Si con padre común solo hay un rpt con ese nombre es que es el mismo organismo

print ("Fusionando organismos dir3_E/administracion.gob.es con rpt")
total = len(organismos)
ok = 0

repetir = True
while repetir:
    repetir = False
    count = 0
    excluir_rpt_1 = set([o.rcp for o in organismos if o.rcp])
    excluir_rpt_2 = set([o.rcp for o in organismos if o.rcp and o.idUnidOrganica])
    for o in organismos:
        count += 1
        print("%3d%% completado: %-30s (%s)" %
              (count * 100 / total, o.idOrganismo, ok), end="\r")
        o.genera_codigos()
        orgs = set()
        for n in organismos_rpt:
            if o.nombres.intersection(n.nombres) and n.idPadres.intersection(o.idPadres):
                orgs.add(n)
        if len(orgs)==1:
            n = orgs.pop()
            if not n.latlon and n.idOrganismo in excluir_rpt_2:
                continue
            if not n.idUnidOrganica and n.idOrganismo in excluir_rpt_1:
                continue
            if n.idOrganismo not in o.codigos:
                ok += 1
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
arreglos = yaml_from_file("data/arreglos_csic.yml")
organismos_csic = {o.idOrganismo: o for o in Organismo.load(name="organismos_csic.es")}
codigos_csic=set([o.idOrganismo for o in organismos_rpt if o.isCsic])
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
            if len(orgs)==1:
                org_csic = orgs.pop()
        if org_csic:
            o.idCsic = org_csic.idOrganismo
            o.deOrganismo = org_csic.deOrganismo
            o.deDireccion = org_csic.deDireccion
            o.latlon = org_csic.latlon
            ok += 1
    count += 1
    print("%3d%% completado: %-30s (%s)" %
          (count * 100 / total, o.idOrganismo, ok), end="\r")
print ("")

print ("Normalizando direcciones")
organismos_gob_es = Organismo.load(name="organismos_gob.es")
organismos_csic = Organismo.load(name="organismos_csic.es")
total = len(organismos)*2 + len(organismos_gob_es)
count = 0
ok = 0
direcciones={}
for o in organismos_gob_es + organismos_csic:
    if o.latlon:
        latlon = direcciones.get(o.dire, set())
        latlon.add(o.latlon)
        direcciones[o.dire] = latlon
    count += 1
    print("%3d%% completado: %-30s (%s)" % (count * 100 / total, o.idOrganismo, ok), end="\r")

direcciones_falta = set([(o.dire, o.postCode) for o in organismos if o.postCode and o.deDireccion and o.dire not in direcciones])
total = total + len(direcciones_falta)
for d, p in direcciones_falta:
    lls = set()
    d_aux = d.split(",")[0]
    for ll, dires in direcciones.items():
        for dire in dires:
            if dire.startswith(d_aux):
                lls.add(ll)
    if len(lls)==1:
        ll = lls.pop()
        latlon = direcciones.get(d, set())
        latlon.add(ll)
        direcciones[d] = latlon
    count += 1
    print("%3d%% completado: %-30s (%s)" % (count * 100 / total, d[:30], ok), end="\r")

for k, v in list(direcciones.items()):
    if len(v)==1:
        direcciones[k]=v.pop()
    else:
        del direcciones[k]

sin_latlon=set()
for o in organismos:
    if not o.latlon and o.deDireccion:
        latlon = direcciones.get(o.dire, None)
        if latlon:
            o.latlon
            ok += 1
        else:
            sin_latlon.add(o.dire)
    count += 1
    print("%3d%% completado: %-30s (%s)" % (count * 100 / total, o.idOrganismo, ok), end="\r")

direcciones={}
for o in organismos:
    if o.latlon:
        dire = direcciones.get(o.latlon, set())
        dire.add(o.deDireccion)
        direcciones[o.latlon] = dire
    count += 1
    print("%3d%% completado: %-30s (%s)" % (count * 100 / total, o.idOrganismo, ok), end="\r")
'''
print("")
for k, v in list(direcciones.items()):
    if len(v)>1:
        print ("\n".join(sorted(v)))
        print ("----")
print("")
print ("\n".join(sorted(sin_latlon)))
'''
print("")
Organismo.save(organismos)
