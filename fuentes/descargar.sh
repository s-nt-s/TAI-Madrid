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

./administracion.gob.es/descargar.sh
./csic.es/descargar.sh
