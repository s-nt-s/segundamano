from abc import ABC, abstractmethod
from urllib.parse import urlparse
from importlib import import_module
from urllib.parse import urljoin
from datetime import datetime
import bs4
import re

import requests

re_js = re.compile(r"/[a-z0-9]+\.js", re.IGNORECASE)
re_pid = re.compile(r'(/[a-z0-9]+\.js\?PID=[^"]+)', re.IGNORECASE)


default_headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:54.0) Gecko/20100101 Firefox/54.0',
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Expires": "Thu, 01 Jan 1970 00:00:00 GMT",
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    "X-Requested-With": "XMLHttpRequest",
}


def get_web(url):
    dom = urlparse(url).netloc
    web = dom.split(".")[-2].lower()
    return web


def build_portal(url, **kwargs):
    web = get_web(url)
    mod = import_module("portals."+web)#, package=__name__)
    mod = getattr(mod, web.title())
    return mod(url, **kwargs)


class Portal(ABC):

    def __init__(self, url, **kwargs):
        self.url = self.tune_url(url, **kwargs)
        self.web = get_web(url)
        uparse = urlparse(url)
        self.root = uparse.scheme + "://" + uparse.netloc
        self.s = requests.Session()
        self.s.headers = default_headers
        self.items = set()

    @abstractmethod
    def load(self):
        pass

    def tune_url(self, url, **kwargs):
        return url

    def __hash__(self):
        return hash(self.url)

    def __eq__(self, other):
        return self.url == other.url


class PortalDistilCaptcha(Portal):

    def get(self, url, headers=None, cookies=None, tried=0):
        response = self.s.get(url, headers=headers,cookies=cookies)
        soup = bs4.BeautifulSoup(response.content, "lxml")
        script = get_captcha(soup)
        if script and tried<2:
            r = self.s.get(self.root+script, headers={"Referer": url})
            m = re_pid.search(r.text)
            if m:
                pid = m.group(1)
                r = self.s.post(self.root+pid, headers={"Referer": url}, data={"p":""})
                cookies = r.cookies
            else:
                print (r.text)
                print (script)
            return self.get(url, headers={"Referer": url},cookies=cookies, tried=tried+1)
        else:
            body_txt = soup.find("body").get_text().strip()
            h1_txt = soup.find("h1").get_text().strip() if soup.find("h1") else None
            if h1_txt and h1_txt == body_txt:
                print (h1_txt)
        return soup

class Item():

    def __init__(self, url, web=None, title=None, image=None, images=None, description=None, price=0, publish=None, portal=None, km=None):
        self.url = url
        self.web = web or get_web(url)
        self.title = title
        self.images = {urljoin(url, i) for i in (images or set())}
        self.image = urljoin(url, image) if image else None
        self.price = price
        self.description = description
        self.publish = publish
        self.portal = portal
        self.km = km

    def __hash__(self):
        return hash(self.url)

    def __eq__(self, other):
        return self.url == other.url

    def extend(self):
        pass

def get_captcha(soup):
    script = soup.find("script", attrs={"src":re_js})
    if not script:
        return None
    script = script.attrs["src"]
    if soup.find("meta", attrs={"http-equiv":"refresh"}):
        return script
    if soup.find("div", attrs={"id": "distilCaptchaForm"}):
        return script
    if "#distilCaptchaForm" in str(soup):
        return script
    return None
