from weaveskein.parser import parse
from weaveskein.resolver import Kind, Resolver
from weaveskein.scanner import discover


def test_import_forms(repo):
    root = repo(
        {
            "src/pkg/__init__.py": "FLAG = True",
            "src/pkg/core.py": "value = 1",
            "src/pkg/nested/worker.py": (
                "import pkg.core as core\n"
                "from pkg import core\n"
                "from .. import core\n"
                "from ..core import value\n"
                "from . import helper\n"
                "from ..nested import helper\n"
                "def task():\n    import pkg\n"
                "import pathlib\nimport vendor_xyz\n"
                "import pkg.absent\nfrom .... import missing\n"
                "from pkg import FLAG\nfrom pkg import missing\n"
            ),
            "src/pkg/nested/helper.py": "",
        }
    )
    index = discover(root)
    parsed = {name: parse(root / mod.path) for name, mod in index.modules.items()}
    resolver = Resolver(index, parsed)
    mod = index.modules["pkg.nested.worker"]
    results = [resolver.resolve(mod, item) for item in parsed[mod.name].imports]
    internal = [r.target for r in results if r.kind == Kind.INTERNAL]
    assert internal.count("pkg.core") == 4
    assert internal.count("pkg.nested.helper") == 2
    assert internal.count("pkg") == 2
    assert sum(r.kind == Kind.UNRESOLVED for r in results) == 3
    assert any(r.name == "pathlib" and r.kind == Kind.STANDARD for r in results)
    assert any(r.name == "vendor_xyz" and r.kind == Kind.EXTERNAL for r in results)


def test_ambiguous_attribute_and_shadowed_submodule(repo):
    root = repo(
        {
            "pkg/__init__.py": "child = object()",
            "pkg/child.py": "",
            "single.py": "",
            "single/hidden.py": "",
            "caller.py": "from pkg import child\nimport single.hidden",
        }
    )
    index = discover(root)
    parsed = {name: parse(root / mod.path) for name, mod in index.modules.items()}
    resolver = Resolver(index, parsed)
    for item in parsed["caller"].imports:
        result = resolver.resolve(index.modules["caller"], item)
        assert result.kind == Kind.UNRESOLVED
        assert result.target is None


def test_package_reexports_its_child(repo):
    root = repo(
        {
            "pkg/__init__.py": "from . import child",
            "pkg/child.py": "",
            "caller.py": "from pkg import child",
        }
    )
    index = discover(root)
    parsed = {name: parse(root / mod.path) for name, mod in index.modules.items()}
    resolver = Resolver(index, parsed)
    for name in ("pkg", "caller"):
        assert resolver.resolve(index.modules[name], parsed[name].imports[0]).target == "pkg.child"
