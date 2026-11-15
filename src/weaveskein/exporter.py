"""Render the report with locally bundled assets and inert JSON data."""

from __future__ import annotations

import json
import os
from importlib.resources import files
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .analyzer import Analysis


def report_data(result: Analysis) -> dict:
    deps = result.dependencies
    return {
        "project": result.index.root.name,
        "modules": [
            {
                "name": name,
                "path": module.path.as_posix(),
                "cycle": deps.cycle_index.get(name),
            }
            for name, module in result.index.modules.items()
        ],
        "edges": sorted(deps.graph.edges),
        "cycles": len(deps.cycles),
        "warnings": result.index.warnings,
    }


def render_report(data: dict) -> str:
    """Escape HTML-sensitive characters before embedding JSON in a raw-text element."""
    assets = files("weaveskein").joinpath("assets")

    def read(name: str) -> str:
        return assets.joinpath(name).read_text(encoding="utf-8")

    payload = json.dumps(data, ensure_ascii=True, separators=(",", ":")).translate(
        {60: r"\u003c", 62: r"\u003e", 38: r"\u0026"}
    )
    # Insert the untrusted payload last so its contents are never treated as placeholders.
    return (
        read("report.html")
        .replace("/* STYLE */", read("report.css"))
        .replace("/* CYTOSCAPE */", read("cytoscape.min.js"))
        .replace("/* APP */", read("report.js"))
        .replace("<!-- DATA -->", payload)
    )


def export_report(result: Analysis, output: Path) -> Path:
    """Write atomically in the destination directory. Never overwrite Python source."""
    if output.suffix.lower() not in {".htm", ".html"} or output.is_symlink():
        raise ValueError("Choose a regular .html or .htm output path.")
    destination = output.absolute()
    report = render_report(report_data(result))
    temporary = None
    try:
        with NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=destination.parent, delete=False
        ) as stream:
            temporary = Path(stream.name)
            stream.write(report)
        os.replace(temporary, destination)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return destination
