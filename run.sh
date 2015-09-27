#!/bin/bash

cd "$(dirname "$0")"

python bici.py > body.html

if [ $? -ne 0 ]; then
	exit 1
fi

cat head.html body.html foot.html > index.html
wput -nc -u index.html ftp://back.host22.com/public_html/bicis/
