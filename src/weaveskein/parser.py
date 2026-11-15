"""Extract syntactic import records and potential package-level name bindings."""

import ast
import tokenize
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Import:
    base: str
    member: str | None
    level: int
    line: int


@dataclass
class Parsed:
    imports: list[Import] = field(default_factory=list)
    bindings: set[str] = field(default_factory=set)


def _bindings(node: ast.AST, names: set[str]) -> None:
    """Collect possible module bindings, stopping at nested lexical scopes."""
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        names.add(node.name)
        return
    if isinstance(node, (ast.Lambda, ast.ListComp, ast.DictComp, ast.SetComp, ast.GeneratorExp)):
        return
    if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
        names.add(node.id)
    if isinstance(node, (ast.Import, ast.ImportFrom)):
        for alias in node.names:
            if (
                isinstance(node, ast.ImportFrom)
                and node.level == 1
                and node.module is None
                and alias.asname in (None, alias.name)
            ):
                # An initializer binding its own child preserves that child's identity.
                if alias.name != "*":
                    continue
            names.add(alias.asname or alias.name.split(".")[0])
    for child in ast.iter_child_nodes(node):
        _bindings(child, names)


def parse(path: Path) -> Parsed:
    """Honor Python encoding cookies. Never import, compile to bytecode, or run the file."""
    with tokenize.open(path) as source:
        tree = ast.parse(source.read(), filename=str(path))
    result = Parsed()
    _bindings(tree, result.bindings)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                result.imports.append(Import(alias.name, None, 0, node.lineno))
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                result.imports.append(
                    Import(node.module or "", alias.name, node.level, node.lineno)
                )
    return result
