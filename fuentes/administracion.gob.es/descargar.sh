#!/bin/bash

cd "$(dirname "$0")"

if [ ! -f ids.txt ]; then
    for i in $(seq 1 626); do
        URL="https://administracion.gob.es/pagFront/espanaAdmon/directorioOrganigramas/quienEsQuien/quienEsQuien.htm?CIdNivelAdmon=1&numPaginaActual=$i";
        printf -v OUT "pag_%03d.html" $i
        wget --no-clobber --continue -O $OUT "$URL"
        echo -ne "$OUT\r"
    done
    echo ""
    grep -ohP '(?<=idUnidOrganica=)[0-9]+' pag_*.html | sort -n | uniq > ids.txt
fi

while IFS='' read -r i || [[ -n "$line" ]]; do
    URL="https://administracion.gob.es/pagFront/espanaAdmon/directorioOrganigramas/fichaUnidadOrganica.htm?idUnidOrganica=$i"
    printf -v OUT "id_%06d.html" $i
    wget -q --no-clobber --continue -O $OUT "$URL"
    echo -ne "$OUT\r"
    for j in $(grep "listarOficinas.htm" "$OUT" | sed -e 's/.*href="//' -e 's/".*//'); do
        printf -v OUT_OFI "of_%06d.html" $i
        URL="https://administracion.gob.es$j"
        wget -q --no-clobber --continue -O $OUT_OFI "$URL"
        echo "$OUT + $OUT_OFI"
    done
done < "ids.txt"
echo ""

sed -e '/^\s*$/d' -e 's/\s\s*/ /g' -i *.html

#wc -l *.html | grep " 0 " | sed 's/.* //' | xargs rm
