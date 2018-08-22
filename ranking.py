#!/usr/bin/python3
# -*- coding: utf-8 -*-

from subprocess import PIPE, Popen, check_output

import bs4
import requests

from api import Descripciones, Info, Jnj2, Puesto, fix_html


def letraDNI(dni):
    dni = int(dni)
    letras = "TRWAGMYFPDXBNJZSQVHLCKEO"
    valor = int(dni / 23)
    valor *= 23
    valor = dni - valor
    return letras[valor]

convocatorias = (
    (2016, 'L', 'BOE-A-2018-991', []),
    (2015, 'L', 'BOE-A-2016-12467', []),
)

descripciones = Descripciones.load().__dict__
puestos = {str(p.idPuesto): p for p in Puesto.load()}
claves = ("idMinisterio", "idCentroDirectivo", "idUnidad")

ofertas = {}
for year, tipo, nombramientos, destinos in convocatorias:
    destinos.extend(Puesto.load(name=("%s_%s" % (year, tipo))))
    for p in destinos:
        for k in claves:
            dc = ofertas.get(k, {})
            vl = p.__dict__.get(k, None)
            if vl:
                conv = dc.get(vl, set())
                conv.add(year)
                dc[vl] = conv
                ofertas[k] = dc


def get_ranking(provincia, destinos, pieza, campo):
    destinos = [d for d in destinos if d.provincia == provincia]
    if pieza > 0:
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
    info = [(i[0], desc[str(i[0])], i[1][0], i[1][1] if pieza >
             0 else list(reversed(i[1][1]))) for i in info.items()]
    info = sorted(info, key=lambda i: (-i[2], i[3]))
    return info


pieza = 15

ranking = {}
for year, _, _, destinos in convocatorias:
    ranking[year] = {}
    for k in claves:
        ranking[year][k] = {}
        ranking[year][k]["arriba"] = get_ranking(28, destinos, +pieza, k)
        ranking[year][k]["abajo"] = get_ranking(28, destinos, -pieza, k)

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
