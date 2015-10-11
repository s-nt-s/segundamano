#!/bin/bash

cd "$(dirname "$0")"

python segundamano.py bicis.yaml

if [ $? -ne 0 ]; then
	exit 1
fi

cp bicis.html index.html
wput -q -nc -u index.html ftp://back.host22.com/public_html/bicis/
