#!/usr/bin/python3
# -*- coding: utf-8 -*-
import re
import sys
import os

import bs4
from shutil import copyfile

from api import Descripciones, Info, Jnj2, Puesto, fix_html

j2 = Jnj2("j2/", "docs/")

#Exclur CENTROS PENITENCIARIOS, y volver a comprobar que es TAI
todos = [p for p in Puesto.load() if p.idCentroDirectivo!=1301 and p.idProvision not in ("L",) and p.isTAI()]
descripciones = Descripciones.load()

paths=[]

for pais in set([p.pais for p in todos]):
    for provincia in set([p.provincia for p in todos if p.pais==pais]):

        puestos = [p for p in todos if p.pais==pais and p.provincia==provincia]
        
        path = "%03d/%02d/index.html" %(pais or "XXX", provincia or "XXX")
        
        nf = Info(puestos, descripciones)

        j2.save("table.html", destino=path, info=nf, parse=fix_html)
        paths.append((nf.deProvincia, path, len([p for p in puestos if p.estado=="V"])))

paths = sorted(paths)
j2.save("index.html", paths=paths)
copyfile("docs/index.html", "docs/tabla.html")
