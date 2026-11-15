"""Render a pattern preview."""

from .catalog import lookup


def preview(name: str) -> str:
    return f"Pattern: {lookup(name).name}"
