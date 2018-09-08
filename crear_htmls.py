#!/usr/bin/python3
# -*- coding: utf-8 -*-
import argparse

import bs4

from api import Descripciones, Info, Jnj2, Organismo, Puesto, fix_html

parser = argparse.ArgumentParser(
    description='Crea el portal html')
parser.add_argument('--todo', action='store_true', help='Autoexplicativo')
parser.add_argument('--direcciones', action='store_true',
                    help='Solo genera la parte de las direcciones')
parser.add_argument(
    '--destinos', action='store_true', help='Solo genera la parte de destinos')
parser.add_argument(
    '--ranking', action='store_true', help='Solo genera la parte del ranking')

args = parser.parse_args()

j2 = Jnj2("j2/", "docs/")

# Excluir CENTROS PENITENCIARIOS, y volver a comprobar que es TAI
# Excluir nivel 18 (puede que salta alguno pero serán tan pocos...)
todos = [p for p in Puesto.load() if p.nivel < 19 and p.idCentroDirectivo !=
         1301 and p.idProvision not in ("L",) and p.isTAI()]
descripciones = Descripciones.load()

organismos = {}
for o in Organismo.load():
    for c in o.codigos:
        organismos[c] = o

if args.todo or args.direcciones:
    nf = Info(todos, descripciones, organismos)
    j2.save("direcciones.html", info=nf, parse=fix_html)

if args.todo or args.destinos:
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
    j2.save("destinos.html", paths=paths, total_vacantes=total_vacantes)

if args.todo or args.ranking:
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

j2.save("index.html")
