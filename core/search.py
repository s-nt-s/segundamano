from datetime import datetime
import re


from .portal import build_portal, Portal
from functools import cached_property
from typing import Dict, Any,  Set, Tuple
from .config import Config
from .item import Item
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

re_space = re.compile(r"[ \t]+")


def str_to_tuple(s):
    if s is None:
        return tuple()
    if isinstance(s, str):
        s = re_space.sub(" ", s)
        s = s.strip()
        if "\n" in s:
            return tuple(sorted(set(s.split("\n"))))
        return tuple(sorted(set(s)))
    return tuple(sorted(set(s)))


def str_to_tuple_re(yml: Dict[str, Any], key: str):
    s = str_to_tuple(yml.get(key, None))
    if len(s) == 0:
        return s
    e = next(iter(s))
    if isinstance(e, str):
        s = tuple(sorted(set(re.compile(re_space.sub("\\s+", r), re.IGNORECASE) for r in s)))
        yml[key] = s
    return s

@dataclass(frozen=True)
class Search():
    config: Config

    def __post_init__(self):
        if isinstance(self.config, str):
            object.__setattr__(self, 'config',  Config.load(self.config))

    @cached_property
    def portals(self) -> Tuple[Portal]:
        urls: Set[str] = set()
        for url in self.config.urls:
            if len(self.config.search) == 0:
                urls.add(url)
                continue
            for srch in self.config.search:
                s_url = url.replace("%%SEARCH_STRING%%", srch.replace(" ", "+"))
                urls.add(s_url)
        portals: Set[Portal] = set()
        for url in urls:
            p = build_portal(url, self.config)
            portals.add(p)
        return tuple(sorted(portals))

    @cached_property
    def webs(self):
        webs = set()
        for i in self.items:
            webs.add(i.web)
        return tuple(sorted(webs))

    @cached_property
    def items(self) -> Tuple[Item]:
        items = set()
        for p in self.portals:
            print(p.web)
            print(p.url)
            print(len(p.items))
            for i in p.items:
                if self.__isOk(i):
                    items.add(i)
        return tuple(sorted(items, key=lambda i: (i.price, -i.publish if isinstance(i.publish, int) else 0)))

    def __isOk(self, i: Item):
        if self.config.km is not None and i.km is not None and i.km > self.config.km:
            logger.debug(f"{i.km}km > {self.config.km} {i.url}")
            return False
        if self.config.exclude_in_title and re_or(self.config.exclude_in_title, i.title):
            logger.debug(f"exclude_in_title {self.config.exclude} {i.url}")
            return False
        if self.config.exclude and re_or(self.config.exclude, i.title, i.description):
            logger.debug(f"exclude {self.config.exclude} {i.url}")
            return False
        if self.config.find_in_title and not re_or(self.config.find_in_title, i.title):
            logger.debug(f"not find_in_title {self.config.find_in_title} {i.url}")
            return False
        if self.config.find and not re_or(self.config.find, i.title, i.description):
            logger.debug(f"not find {self.config.find} {i.url}")
            return False
        return True


def re_or(res: Tuple[re.Pattern], *args: str):
    for s in args:
        if s is not None and len(s) > 0:
            for r in res:
                if r.search(s):
                    return True
    return False
