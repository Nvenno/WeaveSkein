from pathlib import Path

import pytest


@pytest.fixture
def repo(tmp_path):
    """Write a miniature repository and return its root."""

    def create(files: dict[str, str | bytes]) -> Path:
        for filename, content in files.items():
            path = tmp_path / filename
            path.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(content, bytes):
                path.write_bytes(content)
            else:
                path.write_text(content, encoding="utf-8")
        return tmp_path

    return create
