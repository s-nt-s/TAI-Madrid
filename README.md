Nota: El proyecto se llamaba `TAI Madrid` porque al principio era solo de Madrid, pero ahora salen todos los puestos sin importar donde esta.

La idea es concretar todos los puestos TAI hasta el punto que se pueda hacer un mapa geográfico con ellos.

La primera fase es generar un listado, el cual se puede ver, desglosado por provincias, en: https://s-nt-s.github.io/TAI-Madrid/

Y cuando se tengan las direcciones se generará el mapa.
BETA del mapa: https://www.google.com/maps/d/viewer?mid=1pv8aiDcgFZWtE7_0H8LVUupTo5z8_fM8

Para ver lo que se entiende por puesto TAI observar la función `isTAI` de `api/core.py` (a groso modo: son plazas C1 de nivel entre 15 y 18, que no sean de libre disposición y que contengan alguna palabra clave en su descripción).

Para entender que datos se han usado de fuente ver [fuentes/](fuentes/) y su README.md  
Para entender en que se convierten estos datos ver [data/](data/) y su README.md

# ¿Quieres ayudar?

Hay varias tareas por hacer:

## Revisar los puestos

La expresión regular `re_informatica` de `api/core.py` decide si un puesto es de informática o no.
Al hacerlo, todos los puestos que descarta son guardados en `data/puestos_ko.txt` y los aceptados en `data/puestos_ok.txt`

Habría que revisar dichos txt para comprobar que no se esta excluyendo ningún puesto que pudiera ser TAI o se este añadiendo alguno que sobre.

## Mejorar el filtro

Como anteriormente se ha dicho, `isTAI` de `api/core.py` decide si un puesto tiene posibilidades de ser TAI. Convendría revisar esta función por si se puede afinar más.

## Encontrar las localizaciones buenas

A parte de que los `RPT` a veces tienen información contradictoria sobre la localidad en la que esta el puesto, realmente lo que se quiere tener es la calle y numero del edificio donde se realizara el trabajo.

Usando `Dir3` (https://administracionelectronica.gob.es/ctt/dir3) y la alegre suposición de que los códigos `RPT` son códigos `RCP` (en base al punto 3.1.1 del [manual de atributos de dir3](https://administracionelectronica.gob.es/ctt/resources/Soluciones/238/Descargas/manual%20de%20atributos.pdf?idIniciativa=238&idElemento=12232)) he generado el siguiente listado de direcciones: https://s-nt-s.github.io/TAI-Madrid/direcciones.html

Las que encuentra parece que están bien, pero hay lagunas importantes. Por ejemplo, sabemos que el puesto `4772958` fue en la calle Aguacate gracias al [mapa de la promoción 2016](https://www.google.com/maps/d/viewer?mid=1nFluM8VkTMcFcdYipA7KpeR-7U4&ll=40.37956469758672%2C-3.7415436354164058&z=14) y por lo tanto la unidad `50132` debería estar en Aguacate, pero este dato no aparece en `Dir3`.

Por ello sería muy útil tener directamente los datos de `RCP` (Registro Central de Personal) o estudiar mejor `Dir3` a ver que se nos escapa, ya que la dirección de Aguacate si que aparece aunque no sea vinculada a la unidad `50132`.

---------

P.D: Este código se ha hecho deprisa y corriendo, ya lo pondré bonito para las siguientes opos.
