#!/bin/bash

cd "$(dirname "$0")"

find . -type f -not -name '*.py' -not -name '*.md' -not -name '*.sh' -delete

python3 get-links.py > wget.txt

grep -v '^#' wget.txt | wget -i- --continue

find . -iname "*.pdf" -exec pdftotext "{}" "{}-nolayout.txt" \;
find . -iname "*.pdf" -exec pdftotext -layout "{}" "{}-layout.txt" \;
