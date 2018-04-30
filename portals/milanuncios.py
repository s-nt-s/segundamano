import re
from urllib.parse import urlparse

import bs4

from core.portal import Item, Portal, PortalDistilCaptcha
from core.util import clean_description, no_number, clean_price, time_to_epoch

re_date = re.compile(r'"create_date"\s*:\s*"([^"]+)"\s*,\s*"publish_date"\s*:\s*"([^"]+)"')

class Milanuncios(PortalDistilCaptcha):

    def load(self):
        r = self.get(self.url)
        for ad in r.select('div.aditem'):
            a = ad.select("a.aditem-detail-title")[0]
            i = ad.select('img.ef')

            item = MilanunciosItem(
                url=self.root + a.attrs.get('href'),
                web=self.web,
                title=a.get_text().strip(),
                description=clean_description(ad.select('div.tx')),
                price=clean_price(ad.select('div.aditem-price')),
                image=i[0].get('src').strip() if len(i) > 0 else None,
                publish=ad.select("div.x6")[0].get_text().strip(),
                portal=self
            )
            self.items.add(item)


    def tune_url(self, url, word=None, min_price=None, max_price=None, **kwargs):
        if word is not None:
            url = url.replace("/?", "/" + word.replace(" ","-")+".htm?")
        if min_price is not None and "&desde=" not in url:
            url = url + "&desde="+str(min_price)
        if max_price is not None and "&hasta=" not in url:
            url = url + "&hasta="+str(max_price)
        return url

class MilanunciosItem(Item):

    def extend(self):
        soup = self.portal.get(self.url)
        m = re_date.search(str(soup))
        if m:
            d1 = time_to_epoch(m.group(1))
            d2 = time_to_epoch(m.group(2))
            self.publish = d1 if d1 < d2 else d2
        if not self.image:
            img = soup.find("link", attrs={"rel":'image_src'})
            if img is not None:
                self.image = img.attrs['href']
