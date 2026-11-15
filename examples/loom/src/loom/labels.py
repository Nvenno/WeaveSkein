"""Normalize labels and lazily look up their canonical pattern."""


def normalize(name: str) -> str:
    return name.strip().lower()


def canonical(name: str) -> str:
    from .catalog import lookup

    return lookup(name).name
