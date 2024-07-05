from urllib.parse import urljoin
from dataclasses import dataclass, field, asdict
from typing import Tuple
from .util import get_web


@dataclass(frozen=True, eq=True, order=True)
class Item:
    url: str = field(hash=True, compare=True)
    web: str = field(default=None, compare=False)
    title: str = field(default=None, compare=False)
    images: Tuple[str] = field(default_factory=tuple, compare=False)
    price: float = field(default=None, compare=False)
    description: str = field(default=None, compare=False)
    publish: str = field(default=None, compare=False)
    km: float = field(default=None, compare=False)

    def __post_init__(self):
        def _join(i):
            return urljoin(self.url, i)
        if self.web is None:
            object.__setattr__(self, 'web', get_web(self.url))
        object.__setattr__(self, 'images', tuple((map(_join, self.images))))

    @property
    def image(self):
        return self.images[0]

    def extend(self):
        pass

    def merge(self, **kwargs):
        return Item(**{**asdict(self), **kwargs})
