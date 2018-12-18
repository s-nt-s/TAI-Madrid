#!/usr/bin/python3

import os
import sys
import textwrap
import re
import xlrd
import requests
from datetime import datetime

from api import (Descripciones, Organismo, Puesto, dict_from_txt,
                 get_direcciones_txt, simplificar_dire, soup_from_file,
                 yaml_from_file, get_cod_dir_latlon, Jnj2, money)

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)


re_etiqueta=re.compile(r"^(\S+)\s+\[(\d+),\s*(\d+)\]\s*$")
re_space = re.compile(r"  +")
re_number = re.compile(r"^\d+,\d+$")

if not os.path.isfile(".ig_leer_puestos"):
    sys.exit("Ha de crear un fichero .ig_leer_puestos")

def parse(cell, parse_number=True):
    if not cell:
        return None
    v = cell.value
    if isinstance(v, float):
        return int(v) if v.is_integer() else v
    if isinstance(v, str):
        v = v.strip()
        v = re_space.sub(" ", v)
        if parse_number and re_number.match(v):
            v = float(v.replace(",", "."))
            return int(v) if v.is_integer() else v
        return v if len(v) else None
    return v

puestos = Puesto.load(name="2017_L")
unidades = {p.ranking: p.idUnidad for p in puestos}
url=None
with open(".ig_leer_puestos") as f:
    lineas=[l.strip() for l in f.readlines() if l.strip()]
    url=lineas[0]


def get_ok_index(idUnidad, *arg):
    last_unidad = None
    index = 0
    for a in arg:
        unidad = unidades[a]
        if last_unidad is None or unidad!=last_unidad:
            last_unidad = unidad
            index = index + 1
        if unidad==idUnidad:
            return index
    return -1

def contar(*arg):
    i = 0
    for a in arg:
        if a is None:
            return i
        i = i +1
    return i

r = requests.get(url+"&raw=1")
wb = xlrd.open_workbook(file_contents=r.content)
sh = wb.sheet_by_index(2)

renuncias=0
opositores=0
oks={}
for rx in range(1, sh.nrows):
    row = [parse(c) for c in sh.row(rx)]
    asignacion = row[1]
    if asignacion is None or asignacion<1:
        continue
    peticion = [abs(int(i)) for i in row[3:] if i is not None and abs(int(i))!=0]
    opositores = opositores + 1
    if asignacion not in unidades:
        renuncias = renuncias + 1
        continue
    unidad = unidades[asignacion]
    index = get_ok_index(unidad, *peticion)
    ok = oks.get(index, 0) + 1
    oks[index] = ok

j2 = Jnj2("j2/", "docs/")
j2.save("asignacion.html",
    oks=oks,
    now=datetime.now().strftime("%d-%m-%Y %H:%M"),
    opositores = opositores,
    renuncias = renuncias
    )
