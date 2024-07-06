from jinja2 import Environment, FileSystemLoader

from .util import epoch_to_str

import re

re_lowercase = re.compile(r".*[a-z].*")
re_space = re.compile(r"[ \t]+")


def print_str(s: str):
    if not s:
        return ''
    if not re_lowercase.match(s):
        s = s.lower().title()
    s = re_space.sub(" ", s)
    return s


def print_flt(s: float):
    if s is not None:
        return str(s).replace(".0", "")
    return ''


def print_date(d):
    if d is None:
        return ''
    if not isinstance(d, int):
        return d
    return epoch_to_str(d)


class Jnj2():
    def __init__(self, origen, destino):
        self.j2_env = Environment(loader=FileSystemLoader(origen), trim_blocks=True)
        self.j2_env.filters['print_str'] = print_str
        self.j2_env.filters['print_flt'] = print_flt
        self.j2_env.filters['print_date'] = print_date
        self.j2_env.filters['round'] = lambda x: int(round(x))
        self.destino = destino

    def save(self, template, destino=None, parse=None, **kwargs):
        if destino is None:
            destino = template
        out = self.j2_env.get_template(template)
        html = out.render(**kwargs)
        if parse:
            html = parse(html, **kwargs)
        with open(self.destino + destino, "wb") as fh:
            fh.write(bytes(html, 'UTF-8'))
