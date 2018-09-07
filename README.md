Nota: El proyecto se llamaba `TAI Madrid` porque al principio era solo de Madrid, pero ahora salen todos los puestos sin importar donde esta.

La salida de este proyecto es:

* Un mapa con los sitios donde hay TAIs:
  * Ver `tai.kml` y
  * Google Maps https://www.google.com/maps/d/viewer?mid=1pv8aiDcgFZWtE7_0H8LVUupTo5z8_fM8
* Una web con información sobre posibles destinos:
  * Puestos TAIs más probables, y por provincia: https://s-nt-s.github.io/TAI-Madrid/ (salen menos que en el mapa porque aquí filtramos por nivel y en el mapa no)
  * Direcciones de los puestos que aparecen en el anterior listado: https://s-nt-s.github.io/TAI-Madrid/direcciones.html
* Una web con información de los destinos preferidos en convocatorias anteriores: https://s-nt-s.github.io/TAI-Madrid/ranking.html

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

Tanto para facilitar el paso anterior (recordar que algunas de las fusiones tienen en consideración la dirección del organismos) como para pasos posteriores se usa ficheros de `arreglos` para homogeneizar o corregir direcciones.

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

Para pasos posteriores sera útil saber la provincia de un organismo. Para aquellos que tienen código postal es trivial, ya que es sus dos primeros dígitos. Para todos los demás lo que se hace es recorrer todos sus destinos asociados (usando `destions.json`) y si todos estan en la misma provincia se asumen que esa es la provincia del organismos.

# Salida

## HTML

Usando los datos generados:

* `ranking.py` crea https://s-nt-s.github.io/TAI-Madrid/ranking.html
* `crea_htmls.py` crea https://s-nt-s.github.io/TAI-Madrid/ y https://s-nt-s.github.io/TAI-Madrid/direcciones.html

## Mapa

Usando `organismos.json` y `destinos_tai.json` el script `crear_mapa.py` genera el fichero `tai.kml` que posteriormente se exporta a https://www.google.com/maps/d/viewer?mid=1pv8aiDcgFZWtE7_0H8LVUupTo5z8_fM8

Las chinchetas se colocan de la siguiente manera:

* A cada puesto se le asocia el primer organismo (en orden: unidad, centro directivo, ministerio) que tenga coordenadas, a no ser que antes de ese organismos haya otro sin coordenadas pero con una provincia distinta a la que tiene el que si posee coordenadas, en este caso el puesto ira asociado al de la provincia diferente.
* Para cada provincia con organismos sin coordenadas se pone una chincheta en el centro de esa provincia con todos esos organismos y sus puestos asociados
* Para cada coordenada en la que hay un organismos se pone una chincheta con todos esos organismos y sus puestos

Adicionalmente se usa un sistema de carpetas y colores para dar más información (ver mapa).

---------

P.D: Este código se ha hecho deprisa y corriendo, ya lo pondré bonito para las siguientes opos.
