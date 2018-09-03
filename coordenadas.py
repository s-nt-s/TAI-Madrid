#!/usr/bin/python3
# -*- coding: utf-8 -*-

from geopy.geocoders import Nominatim

from api import Organismo, Puesto, yaml_from_file, yaml_to_file
import time

organismos = Organismo.load()

print ("Calculando coordenadas")
direcciones = yaml_from_file("data/coordenadas.yml") or {}

nm = Nominatim(country_bias="ESP")
direcciones_falta = set([(o.deDireccion, o.dire, o.postCode) for o in organismos if o.postCode and o.deDireccion and not o.latlon])
total = len(direcciones_falta)
count = 0
ok = 0
for d1, d2, p in direcciones_falta:
    if d2 in direcciones:
        continue
    l = nm.geocode(d1)
    if l is None and d1.count(" ")>1:
        pl1, pl2, resto = d1.split(" ", 2)
        if pl2.lower() not in ("de", "del"):
            aux = pl1 +" de "+ pl2+" "+resto
            l = nm.geocode(d1)
            if l is None:
                aux = pl1 +" de "+ pl2+" "+resto
                time.sleep(2)
                l = nm.geocode(d1)
    if l and p in l.address:
        direcciones[d2] = str(l.latitude)+","+str(l.longitude)
        ok += 1
    count += 1
    print("%3d%% completado: %-30s (%s)" % (count * 100 / total, d1[:30], ok), end="\r")
    time.sleep(2)
    if ok % 10 == 0:
        yaml_to_file("data/coordenadas.yml", direcciones)

print ("")
yaml_to_file("data/coordenadas.yml", direcciones)
