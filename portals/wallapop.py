from core.portal import Portal
from core.item import Item
from core.web import FFWire
from core.config import Config
from typing import Set
from functools import cached_property
import logging
import time
from core.util import time_to_epoch
from seleniumwire.proxy.client import ProxyException
from core.cache import HashCache
from typing import List, Dict


logger = logging.getLogger(__name__)

URL_API = "api.wallapop.com/api/v3/"


class Wallapop(Portal):

    @HashCache("data/wallapop/url-to-api/{}.json")
    def __find_api_url(self, url):
        if URL_API in url:
            return url
        for i in range(3):
            time.sleep(i*2)
            try:
                with FFWire() as f:
                    f.get(url)
                    time.sleep(2)
                    while True:
                        for requests, js in f.iter_json(URL_API):
                            if not isinstance(js, dict):
                                continue
                            search_objects = js.get("search_objects")
                            if isinstance(search_objects, list):
                                return requests.path
            except ProxyException:
                pass

    @cached_property
    def items(self):
        items: Set[Item] = set()
        item_url = self.root + "/item/"
        url = self.__find_api_url(self.url)
        search_objects = self.__get_search_objects(url)
        for i in search_objects:
            f = i['flags']
            if True in (f['reserved'], f['sold']):
                continue
            item = Item(
                url=item_url + i["web_slug"],
                web=self.web,
                title=i["title"],
                description=i["description"],
                price=i["price"],
                images=[c["small"] for c in i["images"]],
                publish=time_to_epoch(i["creation_date"]),
                km=i["distance"]
            )
            items.add(item)
        logger.debug(str(len(items))+" items")
        return tuple(sorted(items))

    @HashCache("data/wallapop/{}.json")
    def __get_search_objects(self, url: str) -> List[Dict]:
        search_objects = []
        root = url.split("?")[0]
        cur = str(url)
        while True:
            logger.debug(cur)
            r = self.s.get(cur)
            arr = r.json().get("search_objects", [])
            if len(arr) == 0:
                break
            search_objects.extend(arr)
            nxt = r.headers.get('X-NextPage')
            if not isinstance(nxt, str):
                break
            cur = root + "?" + nxt
        return search_objects

    @staticmethod
    def tune_url(url: str, config: Config):
        prm = []
        if config.min_price not in (None, 0) and "&min_sale_price=" not in url:
            prm.append("min_sale_price="+str(config.min_price))
        if config.max_price is not None and "&max_sale_price=" not in url:
            prm.append("max_sale_price="+str(config.max_price))
        if config.lat is not None and "&latitude=" not in url:
            prm.append("latitude="+str(config.lat))
        if config.lon is not None and "&longitude=" not in url:
            prm.append("longitude="+str(config.lon))
        if config.km is not None and "&distance=" not in url:
            prm.append("distance="+str(config.km*1000))
        if prm:
            url = url.rstrip("?&")
            prm = "&".join(prm)
            if "?" in url:
                url = url + "&" + prm
            else:
                url = url + "?" + prm
        return url
