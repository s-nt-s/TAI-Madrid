#!/usr/bin/python3
# -*- coding: utf-8 -*-
import os

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

d = {}
latlon = None
bloque = 1
deDireccion = ""
comment = ""
with open("direcciones.txt") as y:
    for l in y.readlines():
        l = l.strip()
        if len(l) == 0 or l.startswith("#"):
            if l.startswith("#"):
                comment = comment + "\n" + l
            if latlon and len(deDireccion)>0:
                d[latlon]=(d.get(latlon, "")+deDireccion).strip()
                deDireccion=""
                latlon=None
            bloque = 1
            continue
        if bloque == 1:
            latlon = l
            bloque = 2
            continue
        if bloque == 2:
            deDireccion = deDireccion + "\n" + l.strip()
if latlon and len(deDireccion)>0:
    d[latlon]=(d.get(latlon, "")+deDireccion).strip()
    deDireccion=""
    latlon=None

latlons = sorted(d.keys(), key=lambda i: [float(l) for l in i.split(",")])

with open("direcciones.txt", "w") as y:
    y.write(comment.strip()+"\n")
    y.write("\n")
    for l in latlons:
        y.write(l+"\n")
        y.write(d[l]+"\n")
        y.write("\n")
