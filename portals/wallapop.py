import re

from core.portal import Item, Portal
from core.util import clean_description, no_number


class Wallapop(Portal):

    def get(self, url):
        r = self.s.get(url)
        return r.json()

    def load(self):
        r = self.get(self.url)
        item_url = self.root + "/item/"
        for i in r.get("items", []):
            item = Item(
                url=item_url + i["url"],
                web=self.web,
                title=i["title"],
                description=i["description"],
                price=float(no_number.sub("", i["price"])),
                images=set([c["smallURL"] for c in i["images"]]),
                image=i["mainImage"]["smallURL"],
                publish=i["publishDate"],
                portal=self
            )
            self.items.add(item)

    def tune_url(self, url, word=None, min_price=None, max_price=None, lat=None, lng=None, km=None, **kwargs):
        if word is not None and "&kws=" not in url and "?kws=" not in url:
            url = url + "&kws=" + word.replace(" ","+")
        if min_price is not None and "&minPrice=" not in url:
            url = url + "&minPrice="+str(min_price)
        if max_price is not None and "&maxPrice=" not in url:
            url = url + "&maxPrice="+str(max_price)
        if max_price is not None and "&lat=" not in url:
            url = url + "&lat="+str(lat)
        if max_price is not None and "&lng=" not in url:
            url = url + "&lng="+str(lng)
        if km is not None and "&dist=" not in url:
            url = url + "&dist="+str(km)
        return url
