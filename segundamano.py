#!/usr/bin/python3

from core.portal import build_portal
from core.j2 import Jnj2
from core.search import Search

import os

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

if False:
    import http.client as http_client
    import logging
    http_client.HTTPConnection.debuglevel = 1

    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)
    requests_log = logging.getLogger("requests.packages.urllib3")
    requests_log.setLevel(logging.DEBUG)
    requests_log.propagate = True


j2 = Jnj2("templates/", "out/")

for yml in ("data/robot.yaml", "data/pendrive.yaml"):
    s = Search(yml)
    s.load()
    s.filter_and_sort()
    j2.save("listado.html", s.out, data=s)
