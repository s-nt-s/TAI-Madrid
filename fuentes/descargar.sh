#!/bin/bash

cd "$(dirname "$0")"

if [ "$1" == "--borrar" ]; then
    find . -type f -not -name '*.py' -not -name '*.md' -not -name '*.sh' -delete
    find administracion.gob.es -type f -name "*.html" -delete
fi

python3 get-links.py > wget.txt

grep -v '^#' wget.txt | wget -i- --continue --no-clobber

find . -iname "*.pdf" -exec pdftotext "{}" "{}-nolayout.txt" \;
find . -iname "*.pdf" -exec pdftotext -layout "{}" "{}-layout.txt" \;

mkdir -p administracion.gob.es
cd administracion.gob.es

for i in $(seq 1 640); do
    URL="https://administracion.gob.es/pagFront/espanaAdmon/directorioOrganigramas/quienEsQuien/quienEsQuien.htm?CIdNivelAdmon=1&numPaginaActual=$i";
    printf -v OUT "pag_%03d.html" $i
    wget --no-clobber --continue -O $OUT "$URL"
done

grep -ohP '(?<=idUnidOrganica=)[0-9]+' pag_*.html | sort -n | uniq > ids.txt

while IFS='' read -r i || [[ -n "$line" ]]; do
    URL="https://administracion.gob.es/pagFront/espanaAdmon/directorioOrganigramas/fichaUnidadOrganica.htm?idUnidOrganica=$i"
    printf -v OUT "id_%06d.html" $i
    wget --no-clobber --continue -O $OUT "$URL"
done < "ids.txt"

sed -e '/^\s*$/d' -e 's/\s\s*/ /g' -i *.html

