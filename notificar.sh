#!/bin/bash
cd "$(dirname "$0")"

URL=$(head -n 1 .ig_leer_puestos)
wget -q "$URL&raw=1" -O /tmp/tai.xlsx
python3 leer_puestos.py /tmp/tai.xlsx > /tmp/asignacion_tmp.txt
touch /tmp/asignacion.txt
if ! diff -q /tmp/asignacion.txt /tmp/asignacion_tmp.txt &>/dev/null; then
    cat /tmp/asignacion_tmp.txt | sudo say
    mv /tmp/asignacion_tmp.txt /tmp/asignacion.txt
fi
