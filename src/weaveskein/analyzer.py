"""Coordinate discovery, parsing, resolution and graph analysis."""

from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import networkx as nx

from .graph import Dependencies
from .parser import Parsed, parse
from .resolver import Kind, Resolver
from .scanner import Discovery, discover


@dataclass
class Analysis:
    index: Discovery
    dependencies: Dependencies
    counts: Counter[Kind]


def analyze(directory: Path) -> Analysis:
    """Analyze a local tree. Preserve unreadable modules as nodes with diagnostics."""
    index = discover(directory)
    parsed: dict[str, Parsed] = {}
    for module in index.modules.values():
        try:
            parsed[module.name] = parse(index.root / module.path)
        except (SyntaxError, UnicodeError, OSError, ValueError, RecursionError) as exc:
            if isinstance(exc, SyntaxError):
                message = exc.msg
            elif isinstance(exc, OSError):
                message = exc.strerror or str(exc)
            else:
                message = str(exc)
            line = getattr(exc, "lineno", None)
            location = f"{module.path.as_posix()}:{line}" if line else module.path.as_posix()
            index.warnings.append(f"{location}: unable to parse: {message}")

    resolver = Resolver(index, parsed)
    graph = nx.DiGraph()
    graph.add_nodes_from(index.modules)
    counts: Counter[Kind] = Counter()
    for name, source in parsed.items():
        for record in source.imports:
            answer = resolver.resolve(index.modules[name], record)
            counts[answer.kind] += 1
            if answer.target is not None:
                graph.add_edge(name, answer.target)
            if answer.kind == Kind.UNRESOLVED:
                location = index.modules[name].path.as_posix()
                index.warnings.append(
                    f"{location}:{record.line}: unresolved {answer.name} ({answer.reason})"
                )
    return Analysis(index, Dependencies(graph), counts)
