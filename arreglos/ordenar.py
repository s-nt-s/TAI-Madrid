#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
from math import atan2, cos, radians, sin, sqrt

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)


def calcula_distancia(latlon1, latlon2):
    R = 6373.0

    lat, lon = latlon1.split(",")

    lat1 = radians(float(lat))
    lon1 = radians(float(lon))

    lat, lon = latlon2.split(",")

    lat2 = radians(float(lat))
    lon2 = radians(float(lon))

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = abs(R * c) * 1000
    return int(distance)


d = {}
latlon = None
bloque = 1
deDireccion = ""
comment = ""
with open("direcciones.txt") as y:
    for l in y.readlines():
        l = l.strip()
        if len(l) == 0 or l.startswith("#"):
            if l.startswith("#") and not l.startswith("# < "):
                comment = comment + "\n" + l
            if latlon and len(deDireccion) > 0:
                d[latlon] = (d.get(latlon, "")+deDireccion).strip()
                deDireccion = ""
                latlon = None
            bloque = 1
            continue
        if bloque == 1:
            latlon = l
            bloque = 2
            continue
        if bloque == 2:
            deDireccion = deDireccion + "\n" + l.strip()
if latlon and len(deDireccion) > 0:
    d[latlon] = (d.get(latlon, "")+deDireccion).strip()
    deDireccion = ""
    latlon = None

latlons = sorted(d.keys(), key=lambda i: [float(l) for l in i.split(",")])

last_latlon = None
metros = 30
with open("direcciones.txt", "w") as y:
    y.write(comment.strip()+"\n")
    y.write("\n")
    for l in latlons:
        if last_latlon is not None and calcula_distancia(last_latlon, l) < metros:
            y.write("# < %sm\n" % metros)
        y.write(l+"\n")
        y.write(d[l]+"\n")
        y.write("\n")
        last_latlon = l
