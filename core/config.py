from dataclasses import dataclass, field
import re

import yaml

from typing import Tuple, List, Union


re_sp = re.compile(r"\s+")


def flatten(nested_tuple):
    flat_tuple = ()
    for item in nested_tuple:
        if isinstance(item, tuple):
            flat_tuple += flatten(item)
        else:
            flat_tuple += (item,)
    return flat_tuple


def str_to_tuple(s: Union[str, List]):
    if s is None:
        return tuple()
    if isinstance(s, (list, tuple, set)):
        return tuple(sorted(flatten(map(str_to_tuple, s))))
    s = re_sp.sub(" ", s).strip()
    if len(s) == 0:
        return tuple()
    return tuple((s, ))


def str_to_tuple_re(s: Union[str, List]):
    ls = list(str_to_tuple(s))
    for i, r in enumerate(ls):
        ls[i] = re.compile(re_sp.sub(r"\\s+", r), re.IGNORECASE)
    return tuple(ls)


@dataclass(frozen=True)
class Config:
    title: str
    urls: Tuple[str]
    out: str
    search: Tuple[str]
    min_price: float = field(default=None)
    max_price: float = field(default=None)
    exclude: Tuple[re.Pattern] = field(default_factory=tuple)
    exclude_in_title: Tuple[re.Pattern] = field(default_factory=tuple)
    find: Tuple[re.Pattern] = field(default_factory=tuple)
    find_in_title: Tuple[re.Pattern] = field(default_factory=tuple)
    km: float = field(default=None)
    lat: float = field(default=None)
    lon: float = field(default=None)

    def __post_init__(self):
        for k in ("urls", "search"):
            v = object.__getattribute__(self, k)
            object.__setattr__(self, k, str_to_tuple(v))
        for k in ("exclude", "find", "find_in_title", "exclude_in_title"):
            v = object.__getattribute__(self, k)
            object.__setattr__(self, k, str_to_tuple_re(v))
        for k in ("urls", "search"):
            v = object.__getattribute__(self, k)
            if not (isinstance(v, tuple) and len(v) > 0):
                raise ValueError(f"{k} debe ser una tupla de al menos un valor")

    @classmethod
    def load(cls, path: str):
        with open(path, 'r') as f:
            obj = yaml.load(f, Loader=yaml.FullLoader)
            if not isinstance(obj, dict):
                raise ValueError()
            obj = {k: v for k, v in obj.items() if not k.startswith("_")}
            return cls(**obj)
