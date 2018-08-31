#!/usr/bin/python3

import simplekml
import utm

from api import Descripciones, Organismo, Puesto

puestos = [p for p in Puesto.load() if p.idCentroDirectivo !=
           1301 and p.idProvision not in ("L",) and p.isTAI()]

descripciones = Descripciones.load()
organismos = Organismo.load()

kml = simplekml.Kml()
kml.document.name = "TAI"

style_unidad = simplekml.Style()
style_unidad.iconstyle.color = simplekml.Color.blue
style_unidad.iconstyle.icon.href = 'http://maps.google.com/mapfiles/ms/micons/blue.png'

kml.document.style = style_unidad

style_con_vacantes = simplekml.Style()
style_con_vacantes.iconstyle.color = simplekml.Color.green
style_con_vacantes.iconstyle.icon.href = 'http://maps.google.com/mapfiles/ms/micons/green.png'

kml.document.style = style_con_vacantes

style_sin_puestos = simplekml.Style()
style_sin_puestos.iconstyle.color = simplekml.Color.red
style_sin_puestos.iconstyle.icon.href = 'http://maps.google.com/mapfiles/ms/micons/red.png'

kml.document.style = style_sin_puestos

folderVerde = kml.newfolder(name="Con vacantes")
folderVerde.description = "Lugares en los que hay puestos vacantes según los RPT"

folderAzul = kml.newfolder(name="Sin vacantes")
folderAzul.description = "Lugares los que hay puestos TAI según los RPT pero ninguno vacante"

folderRojo = kml.newfolder(name="Añadidos porque sí")
folderRojo.description = "Lugares en los que no hay puestos TAI según RPT pero los añadimos por alguna otra consideración"


visto = set()

unidades = set()
centros = set()
ministerios = set()
vacantes = set()
for p in puestos:
    isVacante = p.estado == "V"
    if p.idUnidad:
        unidades.add(p.idUnidad)
        if isVacante:
            vacantes.add(p.idUnidad)
    if p.idCentroDirectivo:
        centros.add(p.idCentroDirectivo)
        if isVacante:
            vacantes.add(p.idCentroDirectivo)
    if p.idMinisterio:
        ministerios.add(p.idMinisterio)
        if isVacante:
            vacantes.add(p.idMinisterio)

cod_tais = unidades.union(centros).union(ministerios)

latlon_org = {}
for o in organismos:
    if o.latlon and (o.codigos.intersection(cod_tais) or o.nombre == "area de informatica"):
        col = latlon_org.get(o.latlon, set())
        col.add(o)
        latlon_org[o.latlon] = col

print ("Se van a crear %s puntos" % len(latlon_org))

for latlon, orgs in latlon_org.items():
    count = len(orgs)
    if count == 1:
        org = next(iter(orgs))
        name = "%s (%s)" % (org.deOrganismo, org.idOrganismo)
    else:
        name = str(count) + " organismos"
    flagRojo = True
    flagVerde = False
    utm_split = latlon.split(",")
    latlon = (float(utm_split[1]), float(utm_split[0]))
    description = ""
    direcciones = set([o.deDireccion for o in orgs])
    if len(direcciones) == 1:
        description += next(iter(orgs)).deDireccion + "\n\n"
    for org in orgs:
        if count > 1:
            description += "%s - %s\n" % (org.idOrganismo, org.deOrganismo)
        if len(direcciones) > 1:
            description += "Dirección: %s\n" % (org.deDireccion,)
        if org.url:
            description += "URL: " + org.url
        cods = cod_tais.intersection(org.codigos)
        flagRojo = flagRojo and len(cods) == 0
        cods = vacantes.intersection(org.codigos)
        flagVerde = flagVerde or len(cods) > 0

        description = description + "\n\n"
    description = description.strip()
    description = description.replace("\n", "<br/>\n")
    pnt = None
    if flagVerde:
        pnt = folderVerde.newpoint(name=name, coords=[latlon])
        pnt.style = style_con_vacantes
    elif flagRojo:
        pnt = folderRojo.newpoint(name=name, coords=[latlon])
        pnt.style = style_sin_puestos
    else:
        pnt = folderAzul.newpoint(name=name, coords=[latlon])
    pnt.description = description

kml.save("data/tai.kml")
