#!/usr/bin/python3

from core.j2 import Jnj2
from core.search import Search
from core.log import config_log
import logging
from datetime import datetime
import sys

import os

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

config_log("log/segundamano.log")
logger = logging.getLogger(__name__)

j2 = Jnj2("templates/", "out/")

for yml in sys.argv[1:]:
    s = Search(yml)
    list(s.items)
    j2.save("listado.html", s.config.out, data=s, now=datetime.now())
