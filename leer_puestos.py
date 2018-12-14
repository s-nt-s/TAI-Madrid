#!/usr/bin/python3

import os
import sys
import textwrap
import re
import xlrd
import requests

re_etiqueta=re.compile(r"^(\S+)\s+\[(\d+),\s*(\d+)\]\s*$")
re_space = re.compile(r"  +")
re_number = re.compile(r"^\d+,\d+$")

if not os.path.isfile(".ig_leer_puestos"):
    sys.exit(textwrap.dedent('''
        Ha de crear un fichero .ig_leer_puestos con el siguiente formato

        URL al excel de dropbox
        Tu posición
        etiqueta1 [puestoA, puestoZ]
        etiqueta2 [puestoA, puestoZ]
        etiqueta_por_defecto

        Ejemplo:

        https://www.dropbox.com/s/********/***************.xlsx?dl=0
        28
        giss [246, 268]
        sanidad [304, 310]
        cultura [125, 130]
        aeat [19, 90]
    ''').strip())

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


config={}
with open(".ig_leer_puestos") as f:
    lineas=[l.strip() for l in f.readlines() if l.strip()]
    config['URL']=lineas[0]
    config['PUESTO']=int(lineas[1])
    config['ETIQUETAS']={}
    for e in lineas[2:]:
        e, ini, fin = re_etiqueta.match(e).groups()
        config['ETIQUETAS'][e]=list(range(int(ini), int(fin)+1))

r = requests.get(config['URL']+"&raw=1")
wb = xlrd.open_workbook(file_contents=r.content)
sh = wb.sheet_by_index(2)

posibilidades = {k: (0 ,0) for k in config['ETIQUETAS'].keys()}
orden=[]
pesimista = set()

for rx in range(1, sh.nrows):
    row = [parse(c) for c in sh.row(rx)]
    if row[0] == config['PUESTO']:
        print ("Faltan %s por delante" % row[2])
        asignacion = row[1]
        for r in row[3:]:
            if r is not None and r>0:
                r=int(r)
                ok = False
                for k, v in config['ETIQUETAS'].items():
                    if r in v:
                        pesi = posibilidades[k][1]
                        posibilidades[k]=(posibilidades[k][0]+1, pesi+1 if r not in pesimista else pesi)
                        ok = True
                        if k not in orden:
                            orden.append(k)
                if not ok:
                    print ("Puesto no encontrado en las etiquetas: %s" % r)
        s_max=max([len(s) for s in orden])
        for o in orden:
            print(("%"+str(s_max)+"s %s") % (o, posibilidades[o][0]))
        sys.exit()
    else:
        count = 0
        for i in row[3:]:
            if i is not None and i>0 and count<max(5, row[2]-5):
                pesimista.add(int(i))
                count = count + 1
