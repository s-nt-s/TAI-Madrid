#!/bin/bash

cd "$(dirname "$0")"

if [ "$1" == "--borrar" ]; then
    find . -type f -not -name '*.py' -not -name '*.md' -not -name '*.sh' -delete
    find */ -type f -name "*.html" -delete
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

cd ..
mkdir -p csic.es
cd csic.es

lynx -listonly -nonumbers -dump "http://www.csic.es/centros-de-investigacion1?p_p_id=centres_WAR_centresportlet&p_p_lifecycle=0&p_p_state=normal&p_p_mode=view&p_p_col_id=column-1&p_p_col_pos=2&p_p_col_count=3&_centres_WAR_centresportlet_action=paginate&_centres_WAR_centresportlet_gsa_index=false&_centres_WAR_centresportlet_orderByCol=name&_centres_WAR_centresportlet_orderByType=asc&_centres_WAR_centresportlet_delta=999" | grep "http://www.csic.es/centros-de-investigacion1/-/centro/" | sed -e 's/.*\///' -e 's/\?.*//' | sort -n | uniq > ids.txt

while IFS='' read -r i || [[ -n "$line" ]]; do
    URL="http://www.csic.es/centros-de-investigacion1/-/centro/$i"
    printf -v OUT "id_%06d.html" $i
    wget --no-clobber --continue -O $OUT "$URL"
    URL="http://www.csic.es/centros-de-investigacion1?p_p_id=centres_WAR_centresportlet&p_p_lifecycle=0&p_p_state=exclusive&p_p_mode=view&p_p_col_id=column-1&p_p_col_pos=2&p_p_col_count=3&_centres_WAR_centresportlet_action=location&_centres_WAR_centresportlet_id=$i"
    printf -v OUT "mp_%06d.html" $i
    wget --no-clobber --continue -O $OUT "$URL"
done < "ids.txt"

sed -e '/^\s*$/d' -e 's/\s\s*/ /g' -i *.html

