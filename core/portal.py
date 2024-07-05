from urllib.parse import urlparse
from importlib import import_module
import bs4
import re
from .util import get_web
from dataclasses import dataclass, field
from functools import cached_property
from .config import Config
from core.web import buildSoup

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


@dataclass(frozen=True, eq=True)
class Portal:
    url: str = field(hash=True, compare=True)

    @cached_property
    def web(self):
        return get_web(self.url)

    @cached_property
    def root(self):
        uparse = urlparse(self.url)
        return uparse.scheme + "://" + uparse.netloc

    @cached_property
    def s(self):
        s = requests.Session()
        s.headers = default_headers
        return s

    @staticmethod
    def tune_url(url, config: Config):
        return url

    @cached_property
    def items(self):
        return tuple()

    def __lt__(self, other):
        if not isinstance(other, Portal):
            return NotImplemented
        return self.url < other.url

    def __le__(self, other):
        if not isinstance(other, Portal):
            return NotImplemented
        return self.url <= other.url

    def __gt__(self, other):
        if not isinstance(other, Portal):
            return NotImplemented
        return self.url > other.url

    def __ge__(self, other):
        if not isinstance(other, Portal):
            return NotImplemented
        return self.url >= other.url


class PortalDistilCaptcha(Portal):
    def get(self, url, headers=None, cookies=None, tried=0):
        response = self.s.get(url, headers=headers, cookies=cookies)
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
                print(r.text)
                print(script)
            return self.get(url, headers={"Referer": url},cookies=cookies, tried=tried+1)
        else:
            body_txt = soup.find("body").get_text().strip()
            h1_txt = soup.find("h1").get_text().strip() if soup.find("h1") else None
            if h1_txt and h1_txt == body_txt:
                print(h1_txt)
        return buildSoup(url, soup)


def get_captcha(soup: bs4.Tag):
    script = soup.find("script", attrs={"src": re_js})
    if not script:
        return None
    script = script.attrs["src"]
    if soup.find("meta", attrs={"http-equiv": "refresh"}):
        return script
    if soup.find("div", attrs={"id": "distilCaptchaForm"}):
        return script
    if "#distilCaptchaForm" in str(soup):
        return script
    return None


def build_portal(url, config: Config) -> Portal:
    web = get_web(url)
    mod = import_module("portals."+web)
    cls = getattr(mod, web.title())
    if not issubclass(cls, Portal):
        raise ValueError("Portal "+web+" desconocido")
    url = cls.tune_url(url, config)
    obj = cls(url)
    return obj
