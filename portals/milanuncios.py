import re
import requests

from core.item import Item
from core.portal import Portal
from core.util import clean_description, clean_price, time_to_epoch
from core.config import Config
from requests.exceptions import JSONDecodeError
from typing import Set
from functools import cached_property
import logging
import json
import time
from core.web import FFWire

logger = logging.getLogger(__name__)


re_date = re.compile(r'"create_date"\s*:\s*"([^"]+)"\s*,\s*"publish_date"\s*:\s*"([^"]+)"')


def get_item(_id):
    r = requests.post("https://www.milanuncios.com/api/v2/vip/anuncio.php?id="+str(id), headers={"mav": "3"})
    try:
        return r.json()
    except JSONDecodeError:
        pass
    return None


class Milanuncios(Portal):

    def __find_json(self):
        for i in range(2):
            time.sleep(i*2)
            with FFWire() as f:
                for y in range(2):
                    time.sleep(y*2)
                    f.get(self.url)
                    time.sleep(2)
                    f.get_soup()
                    for s in f.get_soup().select("body script"):
                        txt = s.get_text().strip()
                        if not txt.startswith("window.__INITIAL_PROPS__ = JSON.parse("):
                            continue
                        obj = txt.split("(", 1)[-1].rsplit(")", 1)[0]
                        while isinstance(obj, str):
                            obj = json.loads(obj)
                        return obj

    @cached_property
    def items(self):
        js = self.__find_json()
        if js is None:
            return tuple()
        items: Set[Item] = set()
        for ad in js['adListPagination']['adList']['ads']:
            item = Item(
                url=self.root + ad['url'],
                web=self.web,
                title=ad['title'],
                description=ad['description'],
                price=ad['price']['cashPrice'],
                images=ad['images'],
                publish=time_to_epoch(ad['publishDate']),
            )
            items.add(item)
        logger.debug(str(len(items))+" items")
        return tuple(sorted(items))

    @staticmethod
    def tune_url(url: str, config: Config):
        prm = []
        if config.min_price not in (None, 0) and "&desde=" not in url:
            prm.append("desde="+str(config.min_price))
        if config.max_price is not None and "&hasta=" not in url:
            prm.append("hasta="+str(config.max_price))
        if prm:
            url = url.rstrip("?&")
            prm = "&".join(prm)
            if "?" in url:
                url = url + "&" + prm
            else:
                url = url + "?" + prm
        return url
