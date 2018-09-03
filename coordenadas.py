#!/usr/bin/python3
# -*- coding: utf-8 -*-

from geopy.geocoders import Nominatim

from api import Organismo, Puesto, yaml_from_file, yaml_to_file
import time

import requests
from bunch import Bunch

organismos = Organismo.load()


direcciones = yaml_from_file("data/coordenadas.yml") or {}

nm = Nominatim(country_bias="ESP")

def geocode(direccion):
    time.sleep(2)
    l = nm.geocode(direccion)
    if l:
        return l
    r = requests.get("https://maps.googleapis.com/maps/api/geocode/json?address="+direccion)
    j = r.json()
    r = j.get('results', None)
    if r is None or len(r)==0:
        return None
    r = r[0]
    l = r.get('geometry', {}).get('location', None)
    if l is None:
        return  None
    return Bunch(latitude=l['lat'], longitude=l['lng'], address=r['formatted_address'])

direcciones_falta = set([(o.deDireccion, o.dire, o.postCode) for o in organismos if o.postCode and o.deDireccion and not o.latlon and o.dire not in direcciones])
total = len(direcciones_falta)
count = 0
ok = 0
_ok = 0
print ("Calculando coordenadas (%s)" % total)
for d1, d2, p in direcciones_falta:
    if d2 in direcciones:
        continue
    pl1, pl2, resto = d1.split(" ", 2)
    if pl1.lower() in ("avda", "avda.", "av."):
        pl1 = "Avenida"
    d1 = " ".join([pl1, pl2, resto])
    l = geocode(d1)
    if l is None and d1.count(" ")>1:
        if pl2.lower() not in ("de", "del"):
            aux = pl1 +" de "+ pl2+" "+resto
            l = geocode(aux)
            if l is None:
                aux = pl1 +" del "+ pl2+" "+resto
                l = geocode(aux)
    if l and p in l.address:
        direcciones[d2] = str(l.latitude)+","+str(l.longitude)
        ok += 1
    count += 1
    print("%3d%% completado: %-30s (%s)" % (count * 100 / total, d1[:30], ok), end="\r")
    if ok % 10 == 0 and ok>_ok:
        yaml_to_file("data/coordenadas.yml", direcciones)
        _ok=ok

print ("")
yaml_to_file("data/coordenadas.yml", direcciones)
