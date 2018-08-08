#!/usr/bin/python3
# -*- coding: utf-8 -*-

import requests
import bs4
from urllib.parse import urljoin
import PyPDF2
import re
import io
from subprocess import PIPE, Popen, check_output
from api import Descripciones, Info, Jnj2, Puesto, fix_html

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

s = requests.Session()
s.headers=default_headers

re_puesto = re.compile(r"\b(\d{7})\b")

def letraDNI(dni):
    dni=int(dni)
    letras="TRWAGMYFPDXBNJZSQVHLCKEO"
    valor=int(dni/23)
    valor*=23
    valor=dni-valor;
    return letras[valor]

def get(url):
    r = s.get(url)
    soup = bs4.BeautifulSoup(r.content, "lxml")
    for a in soup.select("a[href]"):
        a.attrs["href"] = urljoin(url, a.attrs["href"])
    return soup

def get_pdf(boe, pdftotext=False):
    soup = get("http://www.boe.es/diario_boe/txt.php?id="+boe)
    url = soup.select("li.puntoPDF a")[0].attrs["href"]
    print (url)
    if pdftotext:
        ps = Popen(("curl", "-s", url), stdout=PIPE)
        output = check_output(('pdftotext', '-layout', '-', '-'), stdin=ps.stdout)
        ps.wait()
        return output.decode("utf-8")
    r = s.get(url)
    i = io.BytesIO(r.content)
    pdf = PyPDF2.PdfFileReader(i, strict=False)
    txt = ""
    for page in range(pdf.getNumPages()):
        page = pdf.getPage(page)
        txt = txt = txt + "\n\n" + page.extractText()
    return txt.strip()

convocatorias = (
    (2016, 'L', 'BOE-A-2017-7916', 'BOE-A-2018-991', []),
#    (2016, 'I', 'BOE-A-2017-10171', 'BOE-A-2018-2472'),
    (2015, 'L', 'BOE-A-2016-7318', 'BOE-A-2016-12467', []),
#    (2015, 'I', 'BOE-A-2016-7615', ),
)

descripciones = Descripciones.load().__dict__
puestos = {str(p.idPuesto): p for p in Puesto.load()}
claves = ("idMinisterio", "idCentroDirectivo", "idUnidad")

ofertas={}
destinos = []
for year, tipo, opositores, nombramientos, destinos in convocatorias:
    print ("")
    print (year, tipo)
    print ("")
    txt = get_pdf(nombramientos, pdftotext=True)
    i = 0
    for m in re_puesto.findall(txt):
        i = i+1
        p=puestos[m]
        p.ranking = i
        destinos.append(p)
        for k in claves:
            dc = ofertas.get(k,{})
            vl = p.__dict__.get(k, None)
            if vl:
                conv = dc.get(vl, set())
                conv.add(year)
                dc[vl]=conv
                ofertas[k] = dc
        

def get_ranking(provincia, destinos, pieza, campo):
    destinos = [d for d in destinos if d.provincia == provincia]
    if pieza>0:
        destinos = destinos[:pieza]
    else:
        destinos = destinos[pieza:]
    info = {}
    for d in destinos:
        valor = d.__dict__[campo]
        if valor:
            count, rank = info.get(valor, (0, []))
            rank.append(d.ranking)
            info[valor] = (count + 1, rank)
    k = campo[2:]
    k = k[0].lower() + k[1:]
    desc = descripciones[k]
    info = [(i[0], desc[str(i[0])], i[1][0], i[1][1] if pieza>0 else list(reversed(i[1][1]))) for i in info.items()]
    info = sorted(info, key=lambda i: (-i[2], i[3]))
    return info
    

pieza=15

ranking = {}
for year, _, _, _, destinos in convocatorias:
    ranking[year]={}
    for k in claves:
        ranking[year][k]={}
        ranking[year][k]["arriba"] = get_ranking(28, destinos, +pieza, k)
        ranking[year][k]["abajo"]  = get_ranking(28, destinos, -pieza, k)

j2 = Jnj2("j2/", "docs/")

j2.save(
    "ranking.html",
    convocatorias=convocatorias,
    ranking=ranking,
    textos={
        "idMinisterio": "Ministerio",
        "idCentroDirectivo": "Centro directivo",
        "idUnidad": "Unidad"
    },
    claves=claves,
    pieza=pieza,
    ofertas=ofertas,
    parse=fix_html
)
