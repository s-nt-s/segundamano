import re

from core.item import Item
from core.portal import Portal
from core.util import clean_description, clean_price, time_to_epoch
from core.config import Config
import logging
from functools import cached_property
from core.web import buildSoup
from typing import Set
import bs4

logger = logging.getLogger(__name__)

nuevo_anuncio = re.compile(r"\s*Nuevo anuncio\s*",
                           re.IGNORECASE | re.MULTILINE | re.DOTALL)
re_date = re.compile(r"<!--ts:([^\-]+)-->")
re_desc = re.compile(r'"itemDescSnippet"\s*:\s*"([^"]+)"', re.IGNORECASE | re.MULTILINE | re.DOTALL)


rk = re.compile(r".*?(\d[\.\d]*)\s+km\s+.*", re.IGNORECASE | re.MULTILINE | re.DOTALL)


def getKm(_kms):
    kms = [rk.sub(r"\1", k.get_text()) for k in _kms if rk.match(k.get_text())]
    z = len(kms)
    if z == 0:
        return 9999
    km = kms[0]
    km = km.replace(".", "")
    return int(km)


def find_price(n: bs4.Tag):
    if n is None:
        return None
    prc = set()
    for s in set(re.findall(r"[\d\.,]+", n.get_text())):
        s = s.replace(".", "")
        s = s.replace(",", ".")
        prc.add(float(s))
    p = max(prc)
    return p


class Ebay(Portal):

    def get(self, url):
        response = self.s.get(url)
        self.soup = buildSoup(url, response.content, "lxml")
        return self.soup

    @cached_property
    def items(self):
        items: Set[Item] = set()
        r = self.get(self.url)
        aviso = r.select_one("srp-save-null-search__heading")
        if aviso:
            logger.warning(aviso.get_text().strip())
            return
        for ad in r.select('ul.srp-results > li'):
            if "id" not in ad.attrs:
                if "menos palabras" in ad.get_text():
                    break
                continue
            a = ad.select_one("a.s-item__link")
            i = ad.select_one('div.s-item__image-wrapper img')

            item = Item(
                url=a.attrs["href"],
                web=self.web,
                title=nuevo_anuncio.sub("", a.get_text().strip()),
                description=None,  # clean_description(ad.select('div.tx')),
                price=find_price(ad.select_one('span.s-item__price')),
                images=[i.attrs['src'].strip()] if i else None,
                km=getKm(ad.select('ul.lvdetails li')),
            )
            items.add(item)
        return tuple(sorted(items))

    @staticmethod
    def tune_url(url, config: Config):
        if config.min_price is not None:
            url = url + "&_udlo="+str(config.min_price)
        if config.max_price is not None:
            url = url + "&_udhi="+str(config.max_price)
        if config.km is not None and "&_sadis=" not in url:
            url = url + "&_sadis="+str(config.km)
        return url


class EbayItem(Item):

    def extend(self):
        soup = self.portal.get(self.url)
        html = str(soup)
        m = re_date.search(html)
        if m:
            dt = time_to_epoch(m.group(1))
            self.publish=dt
        m = re_desc.search(html)
        if m:
            self.description = m.group(1)
        self.description = clean_description(soup.select("span.topItmCndDscMsg"))
        if not self.description:
            self.description = clean_description(soup.select("#descriptionText"))

