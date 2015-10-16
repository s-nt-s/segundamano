#!/bin/bash

cd "$(dirname "$0")"

for f in data/*.yaml; do
	python segundamano.py "$f"
done

cd out
wput -q -nc -u *.* ftp://back.host22.com/public_html/sm/
