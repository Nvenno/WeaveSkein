import os
from pathlib import Path

import pytest

from weaveskein.scanner import IGNORED, discover


def test_discovery_and_layout(repo):
    root = repo(
        {
            "tool.py": "",
            "src/pkg/__init__.py": "",
            "src/pkg/part/file.py": "",
            "bad-name.py": "",
            "ignored.txt": "",
            **{f"{folder}/noise.py": "" for folder in IGNORED},
        }
    )
    index = discover(root)
    assert list(index.modules) == ["pkg", "pkg.part.file", "tool"]
    assert index.modules["pkg"].package
    assert index.modules["pkg.part.file"].path == Path("src/pkg/part/file.py")
    assert any("bad-name" in warning for warning in index.warnings)
    assert set(discover(root / "src" / "pkg").modules) == {"pkg", "pkg.part.file"}


def test_duplicate_import_paths(repo):
    index = discover(repo({"foo.py": "", "src/foo.py": ""}))
    assert not index.modules and index.ambiguous == {"foo"}
    assert "Ambiguous module" in index.warnings[0]


def test_invalid_path(tmp_path):
    with pytest.raises(FileNotFoundError):
        discover(tmp_path / "missing")


def test_symlinks(repo):
    root = repo({"pkg/mod.py": ""})
    try:
        os.symlink(root, root / "pkg" / "loop", target_is_directory=True)
        os.symlink(root / "pkg" / "mod.py", root / "linked.py")
    except OSError:
        pytest.skip("Symlinks unavailable for this user")
    assert set(discover(root).modules) == {"pkg.mod"}
