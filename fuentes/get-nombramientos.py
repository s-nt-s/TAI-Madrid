#!/usr/bin/python3
# -*- coding: utf-8 -*-

from urllib.parse import urljoin

import bs4
import requests
import re
from datetime import datetime, timedelta
import os
import subprocess


abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

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

re_puesto = re.compile(r"\b(\d{6,7})\b")

def get(url):
    r = s.get(url)
    soup = bs4.BeautifulSoup(r.content, "lxml")
    for a in soup.select("a[href]"):
        a.attrs["href"] = urljoin(url, a.attrs["href"])
    return soup

excluir = ("administración local", "universidades", "comunidad autónoma", "comunitat", "comunidad foral", "comunidad de")
tomorrow = datetime.today() + timedelta(days=1)
desde = "31/03/2018".replace("/", "%2F")
hasta = tomorrow.strftime("%d/%m/%Y").replace("/", "%2F")
rango = "1370" # Resolucion
query = "&dato%5B1%5D=" + rango + "&dato%5B6%5D%5B0%5D=" + desde + "&dato%5B6%5D%5B1%5D=" + hasta
url = "https://www.boe.es/buscar/personal.php?campo%5B0%5D=TIT&dato%5B0%5D=&operador%5B0%5D=and&campo%5B1%5D=ID_RNG&operador%5B1%5D=and&campo%5B2%5D=ID_DEM&dato%5B2%5D=&operador%5B2%5D=and&campo%5B3%5D=DOC&dato%5B3%5D=&operador%5B3%5D=and&campo%5B4%5D=NBO&dato%5B4%5D=&operador%5B4%5D=and&campo%5B5%5D=DOC&dato%5B5%5D=&operador%5B6%5D=and&campo%5B6%5D=FPU&operador%5B7%5D=and&campo%5B7%5D=FAP&dato%5B7%5D%5B0%5D=&dato%5B7%5D%5B1%5D=&page_hits=2000&sort_field%5B0%5D=FPU&sort_order%5B0%5D=desc&sort_field%5B1%5D=ref&sort_order%5B1%5D=asc&accion=Buscar" + query
url_boes = []
while url:
    soup = get(url)
    for p in soup.select("p.epigrafeDpto"):
        txt = p.get_text().strip().lower()
        flag = False
        for e in excluir:
            if txt.startswith(e):
                flag = True
        if flag:
            continue
        a = p.find_parent("li").find("a")
        url_boes.append(a.attrs["href"])
    sig = soup.select("span.pagSigxxx")
    if sig is None or len(sig)==0:
        url = None
    else:
        a = sig[0].find_parent("a")
        url = a.attrs["href"]
i = 0
for url in url_boes:
    _, boe = url.split("=")
    soup = get(url)
    if "Nombramientos, situaciones e incidencias" in soup.get_text():
        div = soup.select("div#DOdocText")[0]
        txt = None
        i = i +1
        name_file = "nb_%03d_%s.txt" % (i, boe)
        if div.find("img"):
            url = soup.select("li.puntoPDF a")[0].attrs["href"]
            p1 = subprocess.Popen(["curl", "-s", url], stdout=subprocess.PIPE)
            p2 = subprocess.Popen(["pdftotext", "-layout", "-", "-"], stdin=p1.stdout, stdout=subprocess.PIPE)
            p1.stdout.close()
            txt, err = p2.communicate()
            with open(name_file, "wb") as f:
                f.write(txt)
        else:
            txt = div.get_text()
            with open(name_file, "w") as f:
                f.write(txt)
        print (name_file+" "+url)
