# Contributing to WeaveSkein

Open an issue with a minimal Python package layout, the command you ran, the Python version and the expected graph. Reduce private repositories to a small reproducible example before sharing.

For a change, create a virtual environment and install the checkout with `python -m pip install -e ".[dev]"`. Keep import resolution independent of the target environment. The scanner must never execute repository code.

Add a small test repository under a pytest temporary directory when changing analysis behavior. For report changes, open an exported HTML file locally with networking disabled and exercise search, module selection, cycle highlighting and zoom. Preserve licenses when updating bundled assets.

Run the following before opening a pull request:

```sh
python -m ruff format .
python -m ruff check .
python -m pytest
weaveskein scan examples/loom
weaveskein scan src
weaveskein export examples/loom -o report.html
```

Describe any changes to edge semantics, diagnostics or the report format in the pull request and update the README when user-visible behavior changes.
