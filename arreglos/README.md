Ficheros escritos a mano para ayudar al script `crear_datos.py` a crear los `datos` a partir de las `fuentes`:

1. `rpt_dir3.yml` relaciona un código rpt con el dir3 con el que tiene que fusionarse
2. `rpt_csic.yml` relaciona un código rpt con el csic con el que tiene que fusionarse
3. `dir_latlon.txt` relaciona una dirección con sus coordenadas geográficas (*)
4. `cod_dir_latlon.txt` relaciona un código rpt con la dirección y las coordenadas que debe tener
5. `direcciones.txt` relaciona direcciones equivalentes entre si, e indica sus coordenadas

Adicionalmente se pude considerar el excel https://docs.google.com/spreadsheets/d/18GC2-xHj-n2CAz84DkWVy-9c8VpMKhibQanfAjeI4Wc
como otro fichero de arreglos. En concreto nos interesa la pestaña `direcciones`.

(*) `dir_latlon.txt` realmente no se genera a mano, si no que lo crea el script `coordenadas.py` consultando en `Open Street Maps` y `Google Maps` las direcciones de los organismos que aún no tienen coordenadas. Sin embargo situó aquí este fichero por su propósito.
