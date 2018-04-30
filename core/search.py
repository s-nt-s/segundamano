from abc import ABC, abstractmethod
from urllib.parse import urlparse
from importlib import import_module
from urllib.parse import urljoin
from datetime import datetime
import bs4
import re

import requests
import yaml

from .util import epoch_to_str
from .portal import build_portal
from functools import lru_cache


re_space = re.compile(r"[ \t]+")

def str_to_set(s):
    if s is None:
        return set()
    if isinstance(s, str):
        s = re_space.sub(" ", s)
        s=s.strip()
        if "\n" in s:
            return set(s.split("\n"))
        return {s}
    return set(s)

def str_to_set_re(yml, key):
    s = str_to_set(yml.get(key, None))
    if len(s)==0:
        return s
    e = next(iter(s))
    if isinstance(e,str):
        s = set(re.compile(re_space.sub("\\s+", r), re.IGNORECASE) for r in s)
        yml[key] = s
    return s

class Search():

    def __init__(self, yml):
        if isinstance(yml, str):
            with open(yml, 'r') as f:
                yml=yaml.load(f)
        self.yml = yml
        self.title = yml['title']
        self.min_price=yml.get('min_price', None)
        self.max_price = yml.get('max_price', None)
        self.words = str_to_set(yml.get('search', None))
        self.out = yml['out']
        self.km = yml.get('km', None)
        self.exclude = str_to_set_re(yml, 'exclude')
        self.find = str_to_set_re(yml, 'find')
        self.portals = set()
        self.items = set()
        self.date = datetime.now()
        for url in str_to_set(yml['urls']):
            if len(self.words)>0:
                for word in self.words:
                    p = build_portal(url, word=word, **yml)
                    self.portals.add(p)
            else:
                p = build_portal(url, **yml)
                self.portals.add(p)

    def load(self):
        self.items = set()
        self.date = datetime.now()
        for p in self.portals:
            p.load()
            print (p.web)
            print (p.url)
            print (str(len(p.items)))
            self.items = self.items.union(p.items)
        return self.items

    def filter_and_sort(self):
        items = set()
        for i in self.items:
            if filter(self, i):
                items.add(i)
        self.items = sorted(items, key=lambda i: i.publish if isinstance(i.publish, int) else 0, reverse=True)
                

    @property
    @lru_cache(maxsize=None)
    def webs(self):
        webs = set()
        for i in self.items:
            webs.add(i.web)
        return sorted(webs)


def filter(search, item):
    if search.km is not None and item.km is not None and item.km > search.km:
        return False
    if re_or(search.exclude, item.title, item.description):
        return False
    val = str_to_set_re(search.yml, "exclude_"+item.web)
    if re_or(val, item.title, item.description):
        return False
    val = str_to_set_re(search.yml, "exclude_"+item.web+"_title")
    if re_or(val, item.title):
        return False
    val = str_to_set_re(search.yml, "exclude_"+item.web+"_description")
    if re_or(val, item.description):
        return False
    val = str_to_set_re(search.yml, "find_"+item.web+"_title")
    if len(val)>0 and not re_or(val, item.title):
        return False
    item.extend()
    if re_or(search.exclude, item.title, item.description):
        return False
    val = str_to_set_re(search.yml, "exclude_"+item.web)
    if re_or(val, item.title, item.description):
        return False
    val = str_to_set_re(search.yml, "exclude_"+item.web+"_description")
    if re_or(val, item.description):
        return False
    val = str_to_set_re(search.yml, "find_"+item.web)
    if len(val)>0 and not re_or(val, item.title, item.description):
        return False
    val = str_to_set_re(search.yml, "find_"+item.web+"_description")
    if len(val)>0 and not re_or(val, item.description):
        return False
    return True

def re_or(res, *args):
    for s in args:
        if s is not None and len(s)>0:
            for r in res:
                if r.search(s):
                    return True
    return False
