La idea es obtener todos los puestos TAI de Madrid.

El resultado se puede ver en: 

Para ver lo que se entiende por puesto TAI en Madrid observar la función isTAIMadrid de api/core.py

Como fuente de datos se usa los RPT de http://transparencia.gob.es/transparencia/transparencia_Home/index/PublicidadActiva/OrganizacionYEmpleo/Relaciones-Puestos-Trabajo.html

# ¿Quieres ayudar?

Hay varias tareas por hacer:

## Revisar los puestos

La expresión regular re_informatica de api/core.py decide si un puesto es de informática o no.
Al hacerlo, todos los puestos que descarta son guardados en data/resto_puestos.txt

Habría que revisar dicho txt para comprobar que no se esta excluyendo ningún puesto que pudiera ser TAI

## Mejorar el filtro

Como anteriormente se ha dicho, isTAIMadrid de api/core.py decide si un puesto tiene posibilidades de ser TAI y estar en Madrid. Convendría revisar esta función por si se puede afinar más.

## Encontrar las localizaciones buenas

A parte de que los RPT a veces tienen información contradictoria sobre la localidad en la que esta el puesto, realmente lo que se quiere tener es la calle y numero del edificio donde se realizara el trabajo.

La idea seria conseguir esas direcciones.
