#!/usr/bin/python3
# -*- coding: utf-8 -*-
import io
import json
import re
import sys
from subprocess import PIPE, Popen, check_output
from urllib.parse import urljoin

import bs4
import PyPDF2
import requests
import xlrd

from api import Descripciones, Puesto

re_space = re.compile(r"  +")
re_number = re.compile(r"^\d+,\d+$")
re_categoria = re.compile(r"^\s*\d+\.\s*-\s*(.+)\s*:\s*$")
re_spip = re.compile(r"^\s*(Página:|Fecha:|\d+/\d+/20\d+|\d+ de \d+)\s*$")
re_residencia = re.compile(r"^\s*(\d+-\d+-\d+)\s+([A-Z].*)\s*$")

root = "http://transparencia.gob.es/transparencia/transparencia_Home/index/PublicidadActiva/OrganizacionYEmpleo/Relaciones-Puestos-Trabajo.html"
resto = set()

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


def get(url, pdftotext=False):
    if url.endswith(".pdf"):
        if pdftotext:
            ps = Popen(("curl", "-s", url), stdout=PIPE)
            output = check_output(('pdftotext', '-', '-'), stdin=ps.stdout)
            ps.wait()
            return output.decode("utf-8")
        r = s.get(url)
        i = io.BytesIO(r.content)
        pdf = PyPDF2.PdfFileReader(i, strict=False)
        return pdf
    r = s.get(url)
    soup = bs4.BeautifulSoup(r.content, "lxml")
    for a in soup.select("a[href]"):
        a.attrs["href"] = urljoin(url, a.attrs["href"])
    return soup

soup = get(root)

puestos = []

count = 0

pdfs = set()
for i in soup.select("section#block_content_ministerios a"):
    print (i.get_text().strip())
    for li in get(i.attrs["href"]).select("article#cont_gen li"):
        if "funcionario" in li.get_text():
            pdf, xls = li.findAll("a")
            pdfs.add(pdf.attrs["href"])
            print (xls.attrs["href"])
            r = s.get(xls.attrs["href"])
            wb = xlrd.open_workbook(file_contents=r.content)
            sh = wb.sheet_by_index(0)
            for rx in range(sh.nrows):
                row = [parse(c) for c in sh.row(rx)]
                if len(row) > 1 and isinstance(row[0], int):
                    p = Puesto(*row)
                    puestos.append(p)

puestos = [p for p in puestos if p.isTAIMadrid(resto)]
idde = {}

for p in puestos:
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

idde["provincias"] = {}
soup = get("http://www.ine.es/daco/daco42/codmun/cod_provincia.htm")
for tr in soup.select("table.miTabla tr"):
    tds = [td.get_text().strip() for td in tr.findAll("td")]
    if len(tds) == 2 and tds[0].isdigit():
        cod, prov = tds
        idde["provincias"][int(cod)] = prov

for pdf in sorted(pdfs):
    pdf = get(pdf, True)
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
Puesto.save(puestos)

with open("data/resto_puestos.txt", "w") as f:
    for p in sorted(resto):
        f.write(p + "\n")
