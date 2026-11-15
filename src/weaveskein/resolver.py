"""Resolve imports against a static module index, never the host import machinery."""

import sys
from dataclasses import dataclass
from enum import StrEnum

from .parser import Import, Parsed
from .scanner import Discovery, Module


class Kind(StrEnum):
    INTERNAL = "internal"
    STANDARD = "standard library"
    EXTERNAL = "external"
    UNRESOLVED = "unresolved"


@dataclass(frozen=True)
class Resolution:
    kind: Kind
    name: str
    target: str | None = None
    reason: str = ""


class Resolver:
    def __init__(self, index: Discovery, parsed: dict[str, Parsed]):
        self.index = index
        self.parsed = parsed
        self.namespaces: set[str] = set()
        for name in index.modules.keys() | index.ambiguous:
            while "." in name:
                name = name.rpartition(".")[0]
                self.namespaces.add(name)

    def _blocked(self, name: str) -> bool:
        parts = name.split(".")
        for i in range(1, len(parts) + 1):
            prefix = ".".join(parts[:i])
            if prefix in self.index.ambiguous:
                return True
            parent = self.index.modules.get(prefix)
            if i < len(parts) and parent and not parent.package:
                return True
        return False

    def resolve(self, importer: Module, record: Import) -> Resolution:
        base = record.base
        if record.level:
            package = importer.parent_package.split(".") if importer.parent_package else []
            if record.level > len(package):
                path = "." * record.level + base
                return Resolution(Kind.UNRESOLVED, path, reason="beyond package")
            prefix = package[: len(package) - record.level + 1]
            base = ".".join(prefix + ([base] if base else []))
        member = record.member
        child = f"{base}.{member}" if member and member != "*" else ""
        if not record.level and base.split(".")[0] in sys.builtin_module_names:
            return Resolution(Kind.STANDARD, base)
        if self._blocked(base):
            return Resolution(Kind.UNRESOLVED, child or base, reason="ambiguous or shadowed module")
        parent = self.index.modules.get(base)
        if child and (parent is None or parent.package):
            if self._blocked(child):
                return Resolution(Kind.UNRESOLVED, child, reason="ambiguous or shadowed module")
            if child in self.index.modules:
                info = self.parsed.get(base)
                ambiguous = info is None or any(
                    name in info.bindings for name in (member, "*", "__getattr__")
                )
                if parent and ambiguous:
                    return Resolution(
                        Kind.UNRESOLVED, child, reason="package attribute or submodule"
                    )
                return Resolution(Kind.INTERNAL, child, child)
            if child in self.namespaces:
                return Resolution(Kind.INTERNAL, child)
            if parent:
                info = self.parsed.get(base)
                if not info or member not in info.bindings:
                    return Resolution(Kind.UNRESOLVED, child, reason="unknown package member")
        if parent:
            # Reading a symbol from one's own initializer need not be a self-import.
            target = None if member and importer.name == base else base
            return Resolution(Kind.INTERNAL, base, target)
        if base in self.namespaces and not child:
            return Resolution(Kind.INTERNAL, base)
        top = base.split(".")[0]
        if record.level or top in self.index.modules or top in self.namespaces:
            return Resolution(Kind.UNRESOLVED, child or base, reason="missing project module")
        if top in sys.stdlib_module_names:
            return Resolution(Kind.STANDARD, base)
        return Resolution(Kind.EXTERNAL, base)
