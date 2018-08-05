Nota: El proyecto se llamaba `TAI Madrid` porque al principio era solo de Madrid, pero ahora salen todos los puestos sin importar donde esta.

La idea es concretar todos los puestos TAI hasta el punto que se pueda hacer un mapa geográfico con ellos.

La primera fase es generar un listado, el cual se puede ver, desglosado por provincias, en: https://s-nt-s.github.io/TAI-Madrid/

Y cuando se tengan las direcciones se generará el mapa.

Para ver lo que se entiende por puesto TAI observar la función `isTAI` de `api/core.py` (a groso modo: son plazas C1 de nivel entre 15 y 18, que no sean de libre disposición y que contengan alguna palabra clave en su descripción).

Como fuente de datos se usa los `RPT` de http://transparencia.gob.es/transparencia/transparencia_Home/index/PublicidadActiva/OrganizacionYEmpleo/Relaciones-Puestos-Trabajo.html

# ¿Quieres ayudar?

Hay varias tareas por hacer:

## Revisar los puestos

La expresión regular re_informatica de `api/core.py` decide si un puesto es de informática o no.
Al hacerlo, todos los puestos que descarta son guardados en `data/resto_puestos.txt`

Habría que revisar dicho txt para comprobar que no se esta excluyendo ningún puesto que pudiera ser TAI

## Mejorar el filtro

Como anteriormente se ha dicho, `isTAI` de `api/core.py` decide si un puesto tiene posibilidades de ser TAI. Convendría revisar esta función por si se puede afinar más.

## Encontrar las localizaciones buenas

A parte de que los RPT a veces tienen información contradictoria sobre la localidad en la que esta el puesto, realmente lo que se quiere tener es la calle y numero del edificio donde se realizara el trabajo.

La idea seria conseguir esas direcciones.