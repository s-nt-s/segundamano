import re
from urllib.parse import urlparse

import bs4

from core.portal import Item, Portal, PortalDistilCaptcha
from core.util import clean_description, clean_price, no_number, time_to_epoch

re_date = re.compile(r'"(create_date|publish_date)"\s*:\s*"([^"]+)"')

class Vibbo(PortalDistilCaptcha):

    def load(self):
        r = self.get(self.url)
        for ad in r.select('div.basicList.list_ads_row'):
            a = ad.select("a.subjectTitle")[0]
            i = ad.select('img.lazy')

            item = VibboItem(
                url=self.root + urlparse(a.attrs.get('href')).path,
                web=self.web,
                title=a.get_text().strip(),
                price=clean_price(ad.select('a.subjectPrice')),
                image=i[0].attrs.get('title').strip() if len(i) > 0 else None,
                publish=ad.select("p.date a")[0].get_text().strip(),
                portal=self
            )
            self.items.add(item)

    def tune_url(self, url, word=None, min_price=None, max_price=None, **kwargs):
        if word is not None:
            url = url.replace("/?", "/" + word.replace(" ","-")+".htm?")
        if min_price is not None and "&ps=" not in url:
            url = url + "&ps="+str(min_price)
        if max_price is not None and "&pe=" not in url:
            url = url + "&pe="+str(max_price)
        return url

class VibboItem(Item):

    def extend(self):
        soup = self.portal.get(self.url)
        for m in re_date.findall(str(soup)):
            dt = time_to_epoch(m[1])
            if not self.publish or isinstance(self.publish, str) or self.publish>dt:
                self.publish=dt
        self.description = clean_description(soup.select("#descriptionText"))
