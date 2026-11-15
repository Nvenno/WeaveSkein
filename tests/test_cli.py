from pathlib import Path

import pytest
from typer.testing import CliRunner

from weaveskein.cli import app

runner = CliRunner()
EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "loom"


@pytest.mark.parametrize("args", [[], ["scan"], ["cycles"], ["export"]])
def test_help(args):
    response = runner.invoke(app, [*args, "--help"])
    assert response.exit_code == 0 and "Usage" in response.output


def test_example_and_export(tmp_path):
    scan = runner.invoke(app, ["scan", str(EXAMPLE)])
    assert scan.exit_code == 0
    assert "Modules: 5" in scan.output and "Direct dependencies: 4" in scan.output
    cycles = runner.invoke(app, ["cycles", str(EXAMPLE)])
    assert cycles.exit_code == 0 and "Group 1: loom.catalog, loom.labels" in cycles.output
    target = tmp_path / "report.html"
    export = runner.invoke(app, ["export", str(EXAMPLE), "-o", str(target)])
    assert export.exit_code == 0 and str(target) in export.output and target.is_file()


def test_empty_and_errors(tmp_path):
    empty = runner.invoke(app, ["cycles", str(tmp_path)])
    assert empty.exit_code == 0 and "No dependency cycles" in empty.output
    missing = runner.invoke(app, ["scan", str(tmp_path / "absent")])
    assert missing.exit_code != 0 and "Error:" in missing.output
    failed = runner.invoke(app, ["export", str(tmp_path), "-o", str(tmp_path / "missing/r.html")])
    assert failed.exit_code != 0 and "Error:" in failed.output


def test_cli_warns(repo):
    root = repo({"pkg/__init__.py": "", "broken.py": "if:", "app.py": "import pkg.unknown"})
    response = runner.invoke(app, ["scan", str(root)])
    assert response.exit_code == 0
    assert "unable to parse" in response.output and "unresolved pkg.unknown" in response.output
