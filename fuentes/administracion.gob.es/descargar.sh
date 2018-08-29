#!/bin/bash

cd "$(dirname "$0")"

if [ ! -f ids.txt ]; then
    for i in $(seq 1 640); do
        URL="https://administracion.gob.es/pagFront/espanaAdmon/directorioOrganigramas/quienEsQuien/quienEsQuien.htm?CIdNivelAdmon=1&numPaginaActual=$i";
        printf -v OUT "pag_%03d.html" $i
        wget --no-clobber --continue -O $OUT "$URL"
    done

    grep -ohP '(?<=idUnidOrganica=)[0-9]+' pag_*.html | sort -n | uniq > ids.txt
fi

while IFS='' read -r i || [[ -n "$line" ]]; do
    URL="https://administracion.gob.es/pagFront/espanaAdmon/directorioOrganigramas/fichaUnidadOrganica.htm?idUnidOrganica=$i"
    printf -v OUT "id_%06d.html" $i
    wget --no-clobber --continue -O $OUT "$URL"
done < "ids.txt"

sed -e '/^\s*$/d' -e 's/\s\s*/ /g' -i *.html
