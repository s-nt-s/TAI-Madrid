#!/usr/bin/python3
# -*- coding: utf-8 -*-

import time

import requests
from bunch import Bunch
from geopy.geocoders import Nominatim
from stem import Signal
from stem.control import Controller

from api import (Descripciones, Organismo, Puesto, dict_from_txt,
                 simplificar_dire, yaml_from_file, yaml_to_file, get_cod_dir_latlon)

proxies = {'http': 'socks5://127.0.0.1:9050',
           'https': 'socks5://127.0.0.1:9050'}


def get_new_ip():
    with Controller.from_port(port=9051) as controller:
        controller.authenticate()
        controller.signal(Signal.NEWNYM)
        time.sleep(controller.get_newnym_wait())


def save_coordenadas(coordenadas):
    with open("arreglos/dir_latlon.txt", "w") as f:
        for k, v in sorted(coordenadas.items()):
            f.write(v + "    " + k + "\n")

organismos = Organismo.load()

direcciones = dict_from_txt("arreglos/dir_latlon.txt",
                            rever=True, parse_key=simplificar_dire)

nm = Nominatim(country_bias="ESP")

def geocode(direccion, intento=0):
    if intento == 0:
        # time.sleep(3)
        l = nm.geocode(direccion)
        if l:
            return l
    r = requests.get(
        "http://maps.googleapis.com/maps/api/geocode/json?address=" + direccion, proxies=proxies)
    j = r.json()
    r = j.get('results', None)
    if r is None or len(r) == 0:
        if intento < 3 and "error_message" in j:
            get_new_ip()
            return geocode(direccion, intento=intento + 1)
        return None
    r = r[0]
    l = r.get('geometry', {}).get('location', None)
    if l is None:
        return None
    return Bunch(latitude=l['lat'], longitude=l['lng'], address=r['formatted_address'])

cod_dir_latlon = [(k, v[1]) for k, v in get_cod_dir_latlon().items() if v[0] is None]
if len(cod_dir_latlon)>0:
    print ("Calculando coordenadas faltantes en cod_dir_latlon (%s)" % len(cod_dir_latlon))
    for k, d in sorted(cod_dir_latlon):
        l = geocode(d)
        if l:
            l = str(l.latitude) + "," + str(l.longitude)
        else:
            l = ""
        print ("%s    %s    %s" % (k, l, d))
    print ("")

codigos_tai = set()
for p in Puesto.load():
    codigos_tai.add(p.idMinisterio)
    codigos_tai.add(p.idCentroDirectivo)
    codigos_tai.add(p.idUnidad)

provincias = Descripciones.load().provincias

total = len(provincias)
count = 0
ok = 0
_ok = 0
last_ok = ""
print ("Calculando coordenadas de provincias (%s)" % total)
for cod, prov in provincias.items():
    if cod not in direcciones:
        l = geocode(prov + ", España")
        if l:
            direcciones[cod] = str(l.latitude) + "," + str(l.longitude)
            last_ok = prov
            ok += 1
    count += 1
    print("%3d%% completado: %-25s (%s) %-25s" %
          (count * 100 / total, prov, ok, last_ok + "   "), end="\r")
print ("")

save_coordenadas(direcciones)

direcciones_falta = set([(o.deDireccion, o.dire, o.postCode)
                         for o in organismos if o.postCode and o.deDireccion and not o.latlon and o.dire not in direcciones and o.codigos.intersection(codigos_tai)])
total = len(direcciones_falta)
count = 0
ok = 0
_ok = 0
last_ok = ""
print ("Calculando coordenadas de organismos (%s)" % total)
for d1, d2, p in direcciones_falta:
    count += 1
    print("%3d%% completado: %-25s (%s) %-25s" %
          (count * 100 / total, d1[:30], ok, last_ok + "   "), end="\r")
    if d2 in direcciones:
        continue
    pl1, pl2, resto = d1.split(" ", 2)
    if pl1.lower() in ("avda", "avda.", "av."):
        pl1 = "Avenida"
    d1 = " ".join([pl1, pl2, resto])
    l = geocode(d1)
    if l is None and d1.count(" ") > 1:
        if pl2.lower() not in ("de", "del"):
            aux = pl1 + " de " + pl2 + " " + resto
            l = geocode(aux)
            if l is None:
                aux = pl1 + " del " + pl2 + " " + resto
                l = geocode(aux)
    if l and p in l.address:
        last_ok = d2
        direcciones[d2] = str(l.latitude) + "," + str(l.longitude)
        ok += 1
    if ok > _ok and ok % 10 == 0:
        save_coordenadas(direcciones)
        _ok = ok

print ("")
save_coordenadas(direcciones)
