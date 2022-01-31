**IMPORTANTE**: Ya no doy mantenimiento a este proyecto.
Si acabas de aprobar y crees que te puede ser útil, hace un fork y recluta gente entre tu promoción para actualizarlo.

---

Nota: El proyecto se llamaba `TAI Madrid` porque al principio era solo de Madrid, pero ahora salen todos los puestos sin importar donde esta.

La salida de este proyecto es:

* Un mapa con los sitios donde hay TAIs:
  * Ver `tai.kml` en este repositorio (también disponible en https://s-nt-s.github.io/TAI-Madrid/mapa/tai.kml) y
  * Google Maps https://www.google.com/maps/d/viewer?mid=1pv8aiDcgFZWtE7_0H8LVUupTo5z8_fM8
* Una [web con información](https://s-nt-s.github.io/TAI-Madrid/) sobre posibles destinos, rankings y direcciones.

Y próximamente: __Un mapa y listado con solo la oferta de destinos de la convocatoria 2017__.
**Este tema - el de la convocatoria 2017 - se trata en detalle en DESTINOS.md**

# Estructura del proyecto

Las carpetas principales son:

1. `fuentes` con los archivos que se usan como fuente de datos
2. `arreglos` con ficheros rellenos a mano para que sean usados en `crear_datos.py` como ayuda a la hora de generar los `datos`
3. `datos` con los datos que genera el script `crear_datos.py` a partir de las `fuentes`
4. `debug` con los ficheros de depuración que genera el script `crear_datos.py` cuando crea los `datos`
5. `docs` con los html que genera `crear_htmls.py` a partir de los `datos`

La mayoría de estas carpetas incluyen un README.md con más información sobre su ámbito.

# Cómo funciona

## Extracción de datos

A grosso modo, el objetivo es sacar un listado de destinos partiendo de los `RPT` y un listado de organismos partiendo de `dir3` y otras `fuentes`.

### Destinos

`crear_datos.py` lee todos los `RPT` y, entre otros, crea los ficheros `destinos_all.json` con todos los puestos y `destions_tai.json` con aquellos puestos que cremos que son `TAI`.

#### ¿Como se decide que un puesto es TAI?

Esto se hace en base al grupo, nivel y nombre del puesto.
Para verlo en código, observar la función `isTAI` de `api/core.py`.

Para revisar el resultado se generar en `debug` los ficheros `puestos_ok.txt` y `puestos_ko.txt` con los nombres de puestos que han pasado el filtro y con los que no respectivamente. Es aquí donde hay que mirar si se esta omitiendo algún puesto interesante, o se esta incluyendo algún puesto que no debería.

## Organismos

La fuente principal es `Dir3` debido a lo siguiente:

* Los `RPT` utilizan como identificador número los `RCP` (Registro Central de Personal)
* Los códigos `Dir3` que empiezan por `E0` se compienen de `E0 + código RCP + Número de versión`

Sin embargo en `Dir3` ya hay algunos organismos cutos códigos han sido migrados al tipo `EA`, el cual no cumple lo anterior.
Por otro lado, el fichero de `Unidades.rdf` (que ofrece `Dir3`) parece estar menos actualizado que la información de `administracion.gob.es`.
Y además los organismos del `CSIC` vienen mejor documentados en `www.csic.es`.

De este modo nuestra primera salida sera `organismos_rpt.json`, `organismos_dir3_E.json`, `organismso_csic.json` y luego fusionaremos todos los organismos equivalentes en uno solo para evitar duplicidades hasta obtener `organinismos.json`.

Adicionalmente, para los organismos que no tienen dirección buscamos todas sus oficinas y si estas tienen dirección y siempre es la misma suponemos que el organismo esta en esa dirección.

### Fusionando organismos

Usaremos distintos vectores de ataque:

1. La equivalencia de códigos `RCP` con códigos `E0`
2. La similitud entre nombres de distintos organismos
3. La similitud entre direcciones de distintos organismos
4. Los ficheros de `arreglos`

Muy resumidamente, dos organismos, de diferentes `.json`, se consideran que son iguales cuando obviamente:

* Tienen el mismo ćodigo
* Son códigos `E0` con mismo `RCP`

Pero además consideraremos como organismos iguales aquellos que cumplan al menos una de las siguientes condiciones (y la cumplan solo por parejas, es decir, si la cumplen tres organismos no fusionaremos ya que seria demasiado ambiguo):

* Tienen nombre similar
* Tienen nombre similar y mismo padre
* Tienen nombre similar, sus códigos postales son el mismo y sus direcciones son similares

Por último se fusiona siguiendo las indicaciones de los ficheros de `arreglos`.

Nota: En cada paso, solo nos quedaremos con los códigos `E0` en su última versión y se intenta no perder información, por lo tanto si un dato viene informado en una versión más antigua que la actual, se copiara de la versión antigua a la nueva.

### Direcciones

Tanto para facilitar el paso anterior (recordar que algunas de las fusiones tienen en consideración la dirección del organismo) como para pasos posteriores se usa ficheros de `arreglos` para homogeneizar o corregir direcciones.

La lógica es la siguiente:

* Se usa `direcciones.txt` para unificar direcciones y sus coordenadas
* Se machacan direcciones de organismos en base a `cod_dir_latlon.txt`
* Se crea un hash <dirección - coordenadas> con los datos de:
  * `dir_latlon.txt`
  * El excel https://docs.google.com/spreadsheets/d/18GC2-xHj-n2CAz84DkWVy-9c8VpMKhibQanfAjeI4Wc
* Con dicho hash se corrigen o añaden coordenadas a las direcciones de los organismos
* Se vuelve a usar el excel (en concreto las filas de unidades que tienen dirección diferente a su unidad padre) para poner dirección y coordenadas a los organismos que aún no tengan coordenadas

NOTA: Algunos de estos pasos son redundantes y confusos. Próximamente se mejorara. Lo importante por ahora es que se agradecería especialmente las siguientes colaboraciones:

* `pull requests` al fichero `direcciones.txt` para unificar y corregir direcciones (no solo una dirección viene escrita de muchas maneras, si no que no pocas veces algunas veces viene con el código postal mal y otras veces bien). Para ello ver el fichero `direcciones_duplicadas.txt` de `debug` donde se traza primero, las direcciones que aparecen asociadas a diferentes coordenadas, y luego las coordenadas que aparecen asociadas a distintas direcciones.
* `pull requests` al fichero `cod_dir_latlon.txt` para los organismos que hay que se escapan de toda heurística y hay que poner sus localizaciones a mano.
* Añadir datos al excel https://docs.google.com/spreadsheets/d/18GC2-xHj-n2CAz84DkWVy-9c8VpMKhibQanfAjeI4Wc
* Revisar los conflictos entre el excel y la salida final de este script. Ver `direcciones.csv` en `debug`

### Provincias de los organismos

Para pasos posteriores sera útil saber la provincia de un organismo. Para aquellos que tienen código postal es trivial, ya que es sus dos primeros dígitos. Para todos los demás lo que se hace es recorrer todos sus destinos asociados (usando `destions.json`) y si todos estan en la misma provincia se asumen que esa es la provincia del organismo.

# Salida

## HTML

Usando el script `crea_htmls.py` se genera el portal ttps://s-nt-s.github.io/TAI-Madrid/

## Mapa

Usando `organismos.json` y `destinos_tai.json` el script `crear_mapa.py` genera el fichero `tai.kml` que posteriormente se exporta a https://www.google.com/maps/d/viewer?mid=1pv8aiDcgFZWtE7_0H8LVUupTo5z8_fM8

Las chinchetas se colocan de la siguiente manera:

* A cada puesto se le asocia el primer organismo (en orden: unidad, centro directivo, ministerio) que tenga coordenadas, a no ser que antes de ese organismos haya otro sin coordenadas pero con una provincia distinta a la que tiene el que si posee coordenadas, en este caso el puesto ira asociado al de la provincia diferente.
* Para cada provincia con organismos sin coordenadas se pone una chincheta en el centro de esa provincia con todos esos organismos y sus puestos asociados
* Para cada coordenada en la que hay un organismos se pone una chincheta con todos esos organismos y sus puestos

Adicionalmente se usa un sistema de carpetas y colores para dar más información (ver mapa).

# ¿Quieres ayudar?

## Direcciones sin coordenadas

Hay organismos que no tienen dirección (no hay problema si resulta que están ubicados en la misma dirección que su organismo padre, pero en caso contrario se estarían colocando destinos en lugares equivocados), u organismos que si tienen dirección pero no `latlon`.

La solución es añadir o corregir `data/dir_latlon.txt` o `data/cod_dir_latlon.txt`, por lo tanto seria de mucha ayuda los `pull request` que me mandéis para modificar este archivo. O si os es más cómodo editar el [excel](https://docs.google.com/spreadsheets/d/18GC2-xHj-n2CAz84DkWVy-9c8VpMKhibQanfAjeI4Wc).

## Direcciones o coordenadas conflictivas o ausentes

En `data/direcciones.csv` se ha generado un `csv` (con tabulador por separador) donde se puede ver los organismos (indicados por su código `RCP`) que aparezcan en `organismos.json` (y por ende en el mapa) y en el [excel](https://docs.google.com/spreadsheets/d/18GC2-xHj-n2CAz84DkWVy-9c8VpMKhibQanfAjeI4Wc) con dirección y coordenadas, y la distancia en metros entre ambas direcciones.

En algunos casos son manifiestamente contradictorias. Habría que revisar cual es la buena.

La solución es añadir o corregir lineas en el fichero `data/cod_dir_latlon.txt`, por lo tanto seria de mucha ayuda los `pull request` que me mandéis par modificar este archivo. 

## Hacer un mapa interactivo de verdad

Lo dicho, hacer un mapa interactivo de verdad, con buscador, filtros, etc.
Es decir, más `pull request`.

# Modificación para la v2

En septiembre salieron los nuevos `RPT` y se modifico el directorio de organismos
de `administracion.gob.es` con el resultado de que se perdió mucha información.

Por ello se decidió mantener en `datos/v1.0` los datos generados en la v1 y usarlos
como una fuente más para la v2.

Esto se resume en que:

* A los puestos de los `RPT` actuales se les añaden los que estaban en los `RPT` de abril y han desaparecido sin saber por qué.  
Esto queda representado en los listados de destinos con filas que estan tachadas, ver por ejemplo [el de Madrid](https://s-nt-s.github.io/TAI-Madrid/724/28/index.html)
* En vez de fusionar los organismos con `dir3`, los fusiono con `organismos.json` de la v1, lo cual en la practica significa que evitamos perder los organismos que han desaparecido de `administracion.gob.es`. Esto puede provocar que haya organismos por duplicado en el [listado de direcciones](file:///home/santos/wks/TAI/docs/direcciones.html), pero hara que no se pierdan chinchetas en [el mapa](https://www.google.com/maps/d/viewer?mid=1pv8aiDcgFZWtE7_0H8LVUupTo5z8_fM8).

Por todo ello es muy importante que reviséis los datos y aportéis en los [issues](https://github.com/s-nt-s/TAI-Madrid/issues).

---------

P.D: Este código se ha hecho deprisa y corriendo, ya lo pondré bonito para las siguientes opos.
