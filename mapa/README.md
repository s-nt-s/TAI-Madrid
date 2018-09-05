El mapa se puede ver en https://www.google.com/maps/d/viewer?mid=1pv8aiDcgFZWtE7_0H8LVUupTo5z8_fM8

Para entender como se ha hecho lease lo siguiente:

# Organismos

## Leer Dir3

1- Se obtienen los organismos de [Unidades.rdf](
http://dir3rdf.redsara.es/Unidades.rdf)
2- Se les asocia las direcciones que vienen en dicho `rdf`
4- Para los organismos que no tengan dirección se lee [Oficinas.rdf](http://dir3rdf.redsara.es/Oficinas.rdf) y si el organismo tiene todas sus oficinas en una misma dirección, se asume que esa es la dirección de dicho organismo
5- Del resultado de lo anterior se selecciona unicamente los organismo con código `EA` o `E0`, y de estos últimos se toma solo su última versión intentando no perder información de una versión a otra (es decir, si en el organismo X v1 tenemos su dirección pero en el organismo X v2 no la tenemos, preservaremos ese dato de la v1 aunque todos los demás datos sean de la v2)

## Leer administracion.gob.es

Básicamente se hace lo mismo que en el apartado anterior, pero usando como fuente el buscador https://administracion.gob.es/pagFront/espanaAdmon/directorioOrganigramas/quienEsQuien/quienEsQuien.htm

## Fusionar los datos anteriores

Recorremos las dos colecciones de organismos que hemos obtenido anteriormente y identificamos como un mismo organismos aquellos que:

1- tienen el mismo código (o mismo `rcp` si son `E0`)
2- tienen similar nombre y solo hay dos organismos (uno en cada colección) que cumplen dicha condición
3- tienen similar nombre y están en la misma dirección y solo hay dos organismos (uno en cada colección) que cumplen dicha condición. Si estan en distintas direcciones, nos quedamos con la que figure en administracion.gob.es ya que parece ser un dato más actualizado

Al resultado de esta fusión se le hace una nueva pasada en la que:

1- si solo dos organismos hermanos (es decir, que tienen un padre en común) tienen similar nombre, uno de ellos sin dirección y el otro con dirección, al primero se le copia la dirección del segundo.
2- lo mismo para dos organismos con similar nombre, aunque no tengan padre en común, si solo hay dos en toda la colección que cumplan tal similitud.

## Fusionar con arreglos manuales

Aquí se fusionan organismos basándose en la tabla rellenada manualmente en `data/arreglos.yml`

## Fusionar con RPT

1- Si hay un organismo `E0` con `rcp` igual al codigo del `RPT`, ese es el organismo buscado.
2- En caso contrarío, si solo hay un organismo con nombre similar, ese es el organismo buscado.
3- En caso contrarío, si solo hay un organismo con nombre similar entre los organismos que comparten padre con ese `RPT`, ese es el organismo buscado.

## Fusionar con csic.es

Previamente se han obtenido organismos de csic.es, los cuales pasamos a fusionar con lo que ya tenemos de manera similar a como se ha hecho en el paso anterior pero restringiendo el proceso a los organismos que penden del ministerio con id `47811`.

## Normalizar direcciones

Se machaca las direcciones y `latlon` de los organismos que aparezcan en `data/cod_dir_latlon.txt` con los datos ahí reflejados.

Se crea una tabla `hash` en el que la clave es una versión simplificada de una dirección y el valor es su posición en `latitud, longitud`. Esta tabla se rellena con los datos de `data/dir_latlon.txt` (obtenidos vía script `coordenadas.py` consultando en `Open Street Maps` y `Google Maps`), los datos del excel https://docs.google.com/spreadsheets/d/18GC2-xHj-n2CAz84DkWVy-9c8VpMKhibQanfAjeI4Wc y los datos de los organismos que ya tienen incorporado el atributo latlon.

Con este hash se rellena el campo `latlon` de todos los organismos (en la medida de lo posible) que aún teniendo dirección aún no tenían coordenadas.

## Guardar resultado en json

El resultado de todo esto es `data/organismos.json`

# Destinos TAI

## Leer RPTs

Se leen los excel de http://transparencia.gob.es/transparencia/transparencia_Home/index/PublicidadActiva/OrganizacionYEmpleo/Relaciones-Puestos-Trabajo.html y se guarda la información en `data/destinos_all.json`.

Se filtra por grupo, nivel, nombre del puesto, etc. y se genera `data/destinos_tai.json` con solo la información de lo que se cree que son puestos `TAI`.

# Crear Mapa

## Generar KML

Se lee `data/organismos.json` y `destinos_tai.json` para generar un punto en el mapa por dirección en la que hay al menos un organismo donde hay algún puesto `TAI` o un organismo que parezca relevante por su nombre (por ejemplo: Área de informática) aunque no tenga puestos `TAI`.

Al ser un mapa, obviamente solo se muestran organismos que tengan el atributo `latlon` (incluso aquellos que tengan dirección pero no `latlon` no aparecerán).

A cada item de `destino_tai.json` se le asigna como ubicación el primer organismo asociado que tenga atributo `latlon`, siendo el orden de consulta este: unidad, centro directivo, ministerio.

Con ello se crea `mapa/tai.kml`.

## Visualizar mapa en Google Maps

Se exporta `mapa/tai.kml` a Google Maps para que se pueda ver en https://www.google.com/maps/d/viewer?mid=1pv8aiDcgFZWtE7_0H8LVUupTo5z8_fM8

# Mejoras

## Direcciones sin coordenadas

Por otro lado hay organismos que no tienen dirección (no hay problema si resulta que están ubicados en la misma dirección que su organismo padre, pero en caso contrario se estarían colocando destinos en lugares equivocados), u organismos que si tienen dirección pero no `latlon`.

La solución es añadir o corregir `data/dir_latlon.txt`, por lo tanto seria de mucha ayuda los `pull request` que me mandéis par modificar este archivo.

## Direcciones o coordenadas conflictivas o ausentes

En `data/direcciones.csv` se ha generado un `csv` (con tabulador por separador) donde se puede ver los organismos (indicados por su código `rcp`) que aparezcan en `organismos.json` (y por ende en el mapa) y en el (excel)[https://docs.google.com/spreadsheets/d/18GC2-xHj-n2CAz84DkWVy-9c8VpMKhibQanfAjeI4Wc] con dirección y coordenadas, y la distancia en metros entre ambas direcciones.

En algunos casos son manifiestamente contradictorias. Habría que revisar cual es la buena.

La solución es añadir o corregir lineas en el fichero `data/cod_dir_latlon.txt`, por lo tanto seria de mucha ayuda los `pull request` que me mandéis par modificar este archivo. 

## Hacer un mapa interactivo de verdad

Lo dicho, hacer un mapa interactivo de verdad, con buscador, filtros, etc.
Es decir, más `pull request`.
