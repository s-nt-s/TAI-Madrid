#!/usr/bin/python3
# -*- coding: utf-8 -*-

import xlrd
import os
import re
import sys
from glob import glob

from api import Jnj2

re_space = re.compile(r"  +")

def parse(cell):
    if not cell:
        return None
    v = cell.value
    if isinstance(v, float):
        return int(v) if v.is_integer() else v
    if isinstance(v, str):
        v = v.strip()
        v = re_space.sub(" ", v)
        if v.isdigit():
            return int(v)
        return v if len(v) else None
    return v

class Org:

    def __init__(self, codigo, descripcion):
        self.codigo=codigo
        self.descripcion=descripcion
        self.hijos=set()

    def get_hijos(self):
        return sorted(self.hijos, key=lambda o: (o.descripcion, o.codigo))

    def __eq__(self, o):
        self.codigo == o.codigo

    def __hash__(self):
        return self.codigo.__hash__()
    

organismos=[]
dict_organ={}

def get_org(i, d):
    if i is None:
        return None
    o = dict_organ.get(i, None)
    if o is None:
        o=Org(i, d)
        dict_organ[i]=o
    return o

for x in glob("fuentes/RPT-*-PF*.xls"):
    org = Org(os.path.basename(x), "")
    wb = xlrd.open_workbook(x, logfile=open(os.devnull, 'w'))
    sh = wb.sheet_by_index(0)
    for rx in range(1, sh.nrows):
        r = [parse(c) for c in sh.row(rx)]
        if len(r) > 1 and isinstance(r[0], int):
            iM, dM, iC, dC, iU, dU = r[0:6]
            oM = get_org(iM, dM)
            oC = get_org(iC, dC)
            oU = get_org(iU, dU)
            org.hijos.add(oM)
            if oC:
                oM.hijos.add(oC)
                oC.hijos.add(oU)
            else:
                oM.hijos.add(oU)
    organismos.append(org)

j2 = Jnj2("j2/", "docs/")
j2.save("organigrama.html", organismos=organismos)
