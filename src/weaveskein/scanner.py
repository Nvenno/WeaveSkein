"""Discover source modules without importing anything from the target project."""

import keyword
import os
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

IGNORED = frozenset(
    {
        ".git",
        ".hg",
        ".svn",
        ".venv",
        "venv",
        "node_modules",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        ".tox",
        ".nox",
        "build",
        "dist",
    }
)


@dataclass(frozen=True)
class Module:
    name: str
    path: Path  # Relative to the selected project
    package: bool

    @property
    def parent_package(self) -> str:
        return self.name if self.package else self.name.rpartition(".")[0]


@dataclass
class Discovery:
    root: Path
    modules: dict[str, Module] = field(default_factory=dict)
    ambiguous: set[str] = field(default_factory=set)
    warnings: list[str] = field(default_factory=list)


def discover(directory: Path) -> Discovery:
    """Index a repository, its top-level src tree, or a selected package directory."""
    root = directory.resolve(strict=True)
    if not root.is_dir():
        raise NotADirectoryError(f"Expected a directory: {root}")
    result = Discovery(root)
    candidates: dict[str, list[Module]] = defaultdict(list)
    root_package = (root / "__init__.py").is_file()

    def visit(folder: Path, prefix: tuple[str, ...]) -> None:
        try:
            with os.scandir(folder) as entries:
                children = sorted(entries, key=lambda item: item.name)
        except OSError as exc:
            if folder == root:
                raise
            result.warnings.append(f"{folder.relative_to(root)}: {exc.strerror}")
            return
        for entry in children:
            path = Path(entry.path)
            try:
                if entry.is_symlink() or path.is_junction():
                    continue
                if entry.is_dir(follow_symlinks=False):
                    if entry.name in IGNORED or entry.name.startswith("."):
                        continue
                    source_root = (
                        folder == root
                        and entry.name == "src"
                        and not root_package
                        and not (path / "__init__.py").is_file()
                    )
                    visit(path, () if source_root else (*prefix, entry.name))
                elif path.suffix == ".py" and entry.is_file(follow_symlinks=False):
                    package = path.name == "__init__.py"
                    parts = prefix if package else (*prefix, path.stem)
                    if not parts or any(
                        not p.isidentifier() or keyword.iskeyword(p) for p in parts
                    ):
                        result.warnings.append(f"{path.relative_to(root)}: invalid module name")
                        continue
                    name = ".".join(parts)
                    candidates[name].append(Module(name, path.relative_to(root), package))
            except OSError as exc:
                result.warnings.append(f"{path.relative_to(root)}: {exc.strerror}")

    visit(root, (root.name,) if root_package else ())
    for name, choices in sorted(candidates.items()):
        if len(choices) > 1:
            result.ambiguous.add(name)
            paths = ", ".join(m.path.as_posix() for m in choices)
            result.warnings.append(f"Ambiguous module {name}: {paths}")
        else:
            result.modules[name] = choices[0]
    return result
