#!/usr/bin/python3
# -*- coding: utf-8 -*-
from shutil import copyfile

import bs4

from api import Descripciones, Info, Jnj2, Organismo, Puesto, fix_html

j2 = Jnj2("j2/", "docs/")

# Excluir CENTROS PENITENCIARIOS, y volver a comprobar que es TAI
# Excluir nivel 18 (puede que salta alguno pero serán tan pocos...)
todos = [p for p in Puesto.load() if p.idCentroDirectivo !=
         1301 and p.idProvision not in ("L",) and p.isTAI()]
descripciones = Descripciones.load()

organismos = {}
for o in Organismo.load():
    for c in o.codigos:
        organismos[c] = o

nf = Info(todos, descripciones, organismos)
j2.save("direcciones.html", info=nf, parse=fix_html)

paths = []
for pais in set([p.pais for p in todos]):
    for provincia in set([p.provincia for p in todos if p.pais == pais]):

        puestos = [p for p in todos if p.pais ==
                   pais and p.provincia == provincia]

        path = "%03d/%02d/index.html" % (pais or "XXX", provincia or "XXX")

        nf = Info(puestos, descripciones, organismos)

        j2.save("table.html", destino=path, info=nf, parse=fix_html)
        paths.append((nf.deProvincia, path, len(
            [p for p in puestos if p.estado == "V"])))

total_vacantes = len([p for p in todos if p.estado == "V"])

paths = sorted(paths)
j2.save("index.html", paths=paths, total_vacantes=total_vacantes)
copyfile("docs/index.html", "docs/tabla.html")
