import re
from urllib.parse import urlparse

import bs4

from core.portal import Item, Portal
from core.util import clean_description, no_number, clean_price, time_to_epoch

nuevo_anuncio = re.compile(r"\s*Nuevo anuncio\s*",
                           re.IGNORECASE | re.MULTILINE | re.DOTALL)
re_date = re.compile(r"<!--ts:([^\-]+)-->")
re_desc = re.compile(r'"itemDescSnippet"\s*:\s*"([^"]+)"',re.IGNORECASE | re.MULTILINE | re.DOTALL)


rk = re.compile(r".*?(\d[\.\d]*)\s+km\s+.*", re.IGNORECASE | re.MULTILINE | re.DOTALL)

def getKm(_kms):
    kms = [rk.sub(r"\1", k.get_text()) for k in _kms if rk.match(k.get_text())]
    z = len(kms)
    if z == 0:
        return 9999
    km = kms[0]
    km = km.replace(".", "")
    return int(km)

class Ebay(Portal):

    def get(self, url):
        response = self.s.get(url)
        self.soup = bs4.BeautifulSoup(response.content, "lxml")
        return self.soup

    def load(self):
        r = self.get(self.url)
        aviso = r.select("p.sm-md")
        if aviso is not None and len(aviso) == 1:
            av = aviso[0].get_text().strip().lower()
            if av.startswith(u"hemos encontrado 0 resultados en la categoría") and av.endswith(u", por lo que también hemos buscado en todas las categorías"):
                return
        for ad in r.select('#ListViewInner li'):
            a = ad.select('a.vip')
            if len(a) == 0:
                continue
            a = a[0]
            i = ad.select('img.img')

            item = EbayItem(
                url=self.root + urlparse(a.attrs.get('href')).path,
                web=self.web,
                title=nuevo_anuncio.sub("", a.get_text().strip()),
                description=clean_description(ad.select('div.tx')),
                price=clean_price(ad.select('li.lvprice span')),
                image=i[0].get('src').strip() if len(i) > 0 else None,
                km = getKm(ad.select('ul.lvdetails li')),
                portal=self
            )
            self.items.add(item)

    def tune_url(self, url, word=None, min_price=None, max_price=None, km=None, **kwargs):
        if word is not None:
            url = url + "&_nkw="+word.replace(" ", "+")
        if min_price is not None:
            url = url + "&_udlo="+str(min_price)
        if max_price is not None:
            url = url + "&_udhi="+str(max_price)
        if km is not None and "&_sadis=" not in url:
            url = url + "&_sadis="+str(km)
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
        
