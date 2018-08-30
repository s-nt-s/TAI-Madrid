#!/usr/bin/python3

import utm
import simplekml
import textwrap

from api import Descripciones, Organismo, Puesto

puestos = [p for p in Puesto.load() if p.idCentroDirectivo !=
         1301 and p.idProvision not in ("L",) and p.isTAI()]
descripciones = Descripciones.load()
organismos = Organismo.load()

kml=simplekml.Kml()
kml.document.name = "TAI"

style_unidad = simplekml.Style()
style_unidad.iconstyle.color = simplekml.Color.blue
style_unidad.iconstyle.icon.href = 'http://maps.google.com/mapfiles/ms/micons/blue.png'

kml.document.style = style_unidad

style_centro = simplekml.Style()
style_centro.iconstyle.color = simplekml.Color.green
style_centro.iconstyle.icon.href = 'http://maps.google.com/mapfiles/ms/micons/green.png'

kml.document.style = style_centro

style_sin_puestos = simplekml.Style()
style_sin_puestos.iconstyle.color = simplekml.Color.red
style_sin_puestos.iconstyle.icon.href = 'http://maps.google.com/mapfiles/ms/micons/red.png'

kml.document.style = style_sin_puestos


visto = set()

unidades = set()
centros = set()
ministerios = set()
for p in puestos:
    if p.idUnidad:
        unidades.add(p.idUnidad)
    if p.idCentroDirectivo:
        centros.add(p.idCentroDirectivo)
    if p.idMinisterio:
        ministerios.add(p.idMinisterio)

cod_tais = unidades.union(centros).union(ministerios)

latlon_org={}
for o in organismos:
    if o.latlon and (o.codigos.intersection(cod_tais) or o.nombre == "area de informatica"):
        col = latlon_org.get(o.latlon, set())
        col.add(o)
        latlon_org[o.latlon]=col

print ("Se van a crear %s puntos" % len(latlon_org))

for latlon, orgs in latlon_org.items():
    count = len(orgs)
    if count==1:
        org = next(iter(orgs))
        name = str(org.idOrganismo) + " " + org.deOrganismo
    else:
        name = str(count)+" organismos"
    flag = True
    utm_split = latlon.split(",")
    latlon = (float(utm_split[1]), float(utm_split[0]))
    pnt = kml.newpoint(name=name, coords=[latlon])
    description = ""
    direcciones = set([o.deDireccion for o in orgs])
    if len(direcciones)==1:
        description += next(iter(orgs)).deDireccion+"\n\n"
    for org in orgs:
        if count>1:
            description += "%s - %s\n" % (org.idOrganismo, org.deOrganismo)
        if len(direcciones)>1:
            description += "Dirección: %s\n" % (org.deDireccion,)
        if org.url:
            description += "URL: "+org.url
        cods = cod_tais.intersection(org.codigos)
        flag = flag and len(cods)==0
        #if len(cods)>1:
        #    print (cods)
        
        description = description + "\n\n"
    description = description.strip()
    description = description.replace("\n", "<br/>\n")
    pnt.description = description
    if flag:
        pnt.style = style_sin_puestos

kml.save("tai.kml")
