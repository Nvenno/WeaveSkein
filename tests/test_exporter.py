import json
from html.parser import HTMLParser
from pathlib import Path

from weaveskein.exporter import render_report


class InspectHTML(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []
        self.in_data = False
        self.data_text = ""

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        self.tags.append((tag, attributes))
        self.in_data = attributes.get("id") == "report-data"

    def handle_endtag(self, tag):
        if tag == "script":
            self.in_data = False

    def handle_data(self, data):
        if self.in_data:
            self.data_text += data


def test_inert_json_and_bundled_assets():
    hostile = '</script><img src="//evil.invalid/x">\u2028&<!-- DATA -->'
    payload = {
        "project": hostile,
        "modules": [{"name": hostile, "path": hostile, "cycle": None}],
        "edges": [],
        "warnings": [hostile],
        "cycles": 0,
    }
    html = render_report(payload)
    page = InspectHTML()
    page.feed(html)
    assert json.loads(page.data_text) == payload
    assert hostile not in html
    assert all("src" not in attrs and "href" not in attrs for _, attrs in page.tags)
    assert sum(tag == "script" for tag, _ in page.tags) == 3
    assert "Cytoscape.js 3.34.1" in html and "The Cytoscape Consortium" in html
    assert "globalThis.cytoscape=" in html and "connect-src 'none'" in html


def test_safe_output(repo):
    import pytest

    from weaveskein.analyzer import analyze
    from weaveskein.exporter import export_report

    root = repo({"source.py": "import os"})
    result = analyze(root)
    with pytest.raises(ValueError):
        export_report(result, root / "source.py")
    assert (root / "source.py").read_text() == "import os"
    path = export_report(result, root / "map.html")
    assert path == Path(root / "map.html").absolute()
    assert "source.py" in path.read_text(encoding="utf-8")


def test_report_exploration_controls_and_paths(repo):
    from weaveskein.analyzer import analyze
    from weaveskein.exporter import export_report

    root = repo({"src/app/main.py": "", "tests/test_main.py": "", "examples/demo.py": ""})
    page = InspectHTML()
    page.feed(export_report(analyze(root), root / "map.html").read_text(encoding="utf-8"))
    controls = {attrs["id"]: (tag, attrs) for tag, attrs in page.tags if "id" in attrs}
    for name in ("hide-tests", "hide-examples"):
        assert controls[name][1]["type"] == "checkbox"
    assert controls["focus-mode"][0] == "select"
    assert {"all", "out", "in", "both"} == {a["value"] for t, a in page.tags if t == "option"}
    for name in ("filters", "reset", "fit", "zoom-in", "zoom-out", "cycles"):
        assert controls[name][0] == "button"
    assert {"visible-count", "total-isolated", "total-modules", "total-edges", "total-cycles"} <= (
        controls.keys()
    )
    payload = json.loads(page.data_text)
    assert {m["name"]: m["path"] for m in payload["modules"]} == {
        "app.main": "src/app/main.py",
        "tests.test_main": "tests/test_main.py",
        "examples.demo": "examples/demo.py",
    }


def test_empty_report(tmp_path):
    from weaveskein.analyzer import analyze
    from weaveskein.exporter import export_report

    page = InspectHTML()
    page.feed(export_report(analyze(tmp_path), tmp_path / "empty.html").read_text(encoding="utf-8"))
    data = json.loads(page.data_text)
    assert data["modules"] == data["edges"] == [] and data["cycles"] == 0
    assert {"empty-title", "empty-help", "empty-reset"} <= {a.get("id") for _, a in page.tags}
