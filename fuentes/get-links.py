#!/usr/bin/python3
# -*- coding: utf-8 -*-

from urllib.parse import urljoin

import bs4
import requests
import re
from datetime import datetime

re_sp = re.compile(r"\s+")

root = "http://transparencia.gob.es/transparencia/transparencia_Home/index/PublicidadActiva/OrganizacionYEmpleo/Relaciones-Puestos-Trabajo.html"

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


def get(url):
    r = s.get(url)
    soup = bs4.BeautifulSoup(r.content, "lxml")
    for a in soup.select("a[href]"):
        a.attrs["href"] = urljoin(url, a.attrs["href"])
    return soup


def get_pdf_boe(boe, descripcion=None):
    print ('')
    soup = get("http://www.boe.es/diario_boe/txt.php?id=" + boe)
    if descripcion is None:
        descripcion = re_sp.sub(" ", soup.find("h3").get_text()).strip()
    print ('# %s - %s' % (boe, descripcion))
    url = soup.select("li.puntoPDF a")[0].attrs["href"]
    print(url)

soup = get(root)

print ('# Códigos de provincia')
print ('http://www.ine.es/daco/daco42/codmun/cod_provincia.htm')
print ('')
print ('# Dir3')
print ('http://dir3rdf.redsara.es/Unidades.rdf')
print ('http://dir3rdf.redsara.es/Oficinas.rdf')

# get_pdf_boe('BOE-A-2017-7916', '2016 Libre Opositores')
get_pdf_boe('BOE-A-2018-991',  '2016 Libre Nombramientos')

# get_pdf_boe('BOE-A-2017-10171', '2016 Interna Opositories')
# get_pdf_boe('BOE-A-2018-2472',  '2016 Interna Nombramientos')

# get_pdf_boe('BOE-A-2016-7318',  '2015 Libre Opositories')
get_pdf_boe('BOE-A-2016-12467', '2015 Libre Nombramientos')

# get_pdf_boe('BOE-A-2016-7615', '2015 Interna Opositories')

'''
print ('# Puestos que ya no son vacantes')
get_pdf_boe('BOE-A-2018-10329')
get_pdf_boe('BOE-A-2018-10302')
get_pdf_boe('BOE-A-2018-9733')
get_pdf_boe('BOE-A-2018-9564')
'''

visto = set()
suprimidos = soup.find("a", attrs={"href": re.compile(r".*MinisteriosSuprimidos.html")})
if suprimidos is None:
    suprimidos=[]
else:
    suprimidos=[suprimidos]
for i in suprimidos + soup.select("section#block_content_ministerios a"):
    page = get(i.attrs["href"])
    for li in page.select("article#cont_gen li"):
        print ('')
        print ('# ' + i.get_text().strip())
        if "funcionario" in li.get_text().lower():
            pdf, xls = li.findAll("a")
            xls = xls.attrs["href"]
            pdf = pdf.attrs["href"]
            if xls in visto:
                print ('#', end=' ')
            print (xls)
            if pdf in visto:
                print ('#', end=' ')
            print (pdf)

            visto.add(xls)
            visto.add(pdf)
