"""Look up patterns by their display names."""

from . import labels
from .model import Pattern


def lookup(name: str) -> Pattern:
    return Pattern(labels.normalize(name))
