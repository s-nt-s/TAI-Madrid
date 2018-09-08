Cuando salga la oferta de destinos tendremos dos tipos de puestos:

* Los que ya aparecen en los `RPT` y
* los que no

Con los primeros no hay problema, ya que con su ID nos vamos a nuestros `json` y sacamos toda la información.

Pero los otros... son una movida.

## ¡El problema!

Si observamos las convocatorias pasadas (para los ejemplos usare la última, es decir, la de 2016), vemos que:

1. Primero, sale la oferta de destinos https://www.boe.es/diario_boe/txt.php?id=BOE-A-2017-14022
2. Segundo, se eligen los destinos con esa información
3. Tercero, sale la asignación de destinos https://www.boe.es/diario_boe/txt.php?id=BOE-A-2018-991

Si nos fijamos en el puesto `4772958` vemos que en la oferta de destinos aparece con la siguiente información:

* Puesto número: 30
* Ministerio: AG. ESTATAL DE ADMON. TRIBUTARIA
* Centro directivo: DELEGACION ESPECIAL DE MADRID
* Centro destino: AREA DE INFORMATICA 
* Provincia: Madrid
* Puesto de trabajo: GESTOR/A INFORMATICA ENTRADA
* Nivel: 16
* Complemento: 3.940,72

Como vemos, con esta información no podemos saber donde esta el puesto
(si no esta ya en los `RPT`) ya que no viene el ID del centro destino
(el equivalente a la `unidad` en nuestros datos) ni del centro directivo.

Podríamos intentar buscar la unidad en nuestros datos, pero `AREA DE INFORMATICA`
hay a patadas, así que nos tendríamos que contentar con encontrar el centro directivo
de la cual sabemos que esta en
[Calle Guzmán el Bueno 139](https://www.google.com/maps?q=40.4454613,-3.7131352)

Sin embargo, y para cuando ya sería tarde, veríamos que en la asignación de destinos
este mismo puesto `4772958` aparece como (no repito, solo pongo lo nuevo e interesante):

* Centro destino: ADMON.SUROESTE - AREA DE INFORMATICA

Y si lo buscamos en nuestros datos tampoco lo encontraremos ya que no
aparece con ese nombre, pero podemos intuir que es la `EA0014197` que según
[su ficha](https://administracion.gob.es/pagFront/espanaAdmon/directorioOrganigramas/fichaUnidadOrganica.htm?idUnidOrganica=94440)
esta en [Calle Aguacate 27](https://www.google.com/maps?q=40.3705287,-3.7457446),
es decir, en la otra punta de Madríd

Cuando finalmente salga el puesto en la `RPT` veremos que sus datos son:

* Ministerio: 44 - AGENCIA ESTATAL DE ADMINISTRACION TRIBUTARIA
* Centro directivo: 40777 - DELEGACION ESPECIAL DE MADRID
* Unidad: 50132 - AREA DE INFORMATICA

Lo cual confirma que el destino es en [Calle Aguacate 27](https://www.google.com/maps?q=40.3705287,-3.7457446), pero también
vemos que aunque hubiéramos tenido el detalle de `ADMON.SUROESTE - AREA DE INFORMATICA` a tiempo no se habría podido mapear automáticamente con
nuestros datos porque en el `RPT` entre `40777 - DELEGACION ESPECIAL DE MADRID` y `50132 - AREA DE INFORMATICA` falta el eslabón
`EA0014197 - Administración de la AEAT de Carabanchel` que es el que
correspondería a `ADMON.SUROESTE`. En fin, un desastre.

Por lo tanto, no tener los códigos de las unidades y centros directivos
de los puestos tal y como saldrían en los `RPT` es el cuello de botella
principal, ya que:

* los nombres no tienen porque ser igual a nuestros datos
* ni siquiera tienen que ser igual entre la oferta de destinos y la asignación

es mucho esperar que los nombres estén normalizados.

## Propuesta de solución

### Intentar obtener los códigos

Los códigos que usan los `RPT` son códgos `RCP` (Registro Central de Personal) por lo tanto lo primero sera mandar un mail a secretaria.rcp@correo.gob.es con el siguiente texto (o similar):

```
Buenos días,

Necesito saber los códigos RCP y nombres de las unidades y centros directivos de los siguientes puestos de trabajo:

<<aquí la lista de puestos con su código y descripción>>

¿Pueden facilitármela?

Gracias.
```

Si sabeis otras direcciones de gobierno donde sería interesante mandar
esto, hacer `pull requests` a este `DESTINOS.md` para añadirlo.

### Heurística (por script)

Si algún nombre coincide exactamente (ignorando mayúsculas/minúsculas y tildes) con uno y solo uno de nuestros organismos daremos por bueno que
es ese

### Creación de mapa y excel (por script)

Se genera un excel con lo que se sabe y se publica de esta manera https://www.google.com/earth/outreach/learn/mapping-from-a-google-spreadsheet/ (se le añade columas para reflejar otra información útil [como hicieron
en 2016](https://docs.google.com/spreadsheets/d/1bhw4tgHI_IuTOgWEucVWjM8dR6lsjfO4o88otW_jtt8))

### Trabajo manual

El resto ya hay que hacerlo a mano

## Coordinación

- El primero que vea los destinos que mande el mail y avise (que tampoco
es plan reventarles el buzón de correo)

- Lanzamos el script sin esperar respuesta, que vete tu a saber cuanto tardan

- Se empieza ya a rellenara a mano el excel

- Si responde se vuelve a lanzar y se actualiza el excel

y poco más
