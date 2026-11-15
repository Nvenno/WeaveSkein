from weaveskein.analyzer import analyze


def test_scc_and_impact(repo):
    result = analyze(
        repo(
            {
                "a.py": "import b",
                "b.py": "import c",
                "c.py": "import a",
                "outside.py": "import b",
                "top.py": "import outside",
                "loop.py": "import loop",
                "alone.py": "",
            }
        )
    )
    graph = result.dependencies
    assert graph.cycles == [["a", "b", "c"], ["loop"]]
    assert graph.direct("b") == ["c"]
    assert graph.reverse("b") == ["a", "outside"]
    assert graph.impact("b") == ["a", "c", "outside", "top"]
    assert graph.hubs(1) == [("b", 3)]
    assert graph.isolates == 1


def test_partial_analysis_never_executes_code(repo):
    root = repo(
        {
            "bad.py": "if:",
            "bad_bytes.py": b"\xff\n",
            "good.py": "raise RuntimeError('never execute')\nimport bad",
            "codec.py": b"# coding: latin-1\nname = 'caf\xe9'\n",
        }
    )
    result = analyze(root)
    assert len(result.index.warnings) == 2
    assert result.dependencies.direct("good") == ["bad"]
    assert len(result.dependencies.graph) == 4


def test_unreadable_file(repo, monkeypatch):
    from weaveskein import parser

    root = repo({"one.py": ""})

    def denied(*args):
        raise PermissionError("access denied")

    monkeypatch.setattr(parser.tokenize, "open", denied)
    result = analyze(root)
    assert "access denied" in result.index.warnings[0]
    assert result.dependencies.direct("one") == []


def test_two_node_cycle_and_duplicate_edges(repo):
    result = analyze(repo({"a.py": "import b\nimport b", "b.py": "import a"}))
    assert result.dependencies.cycles == [["a", "b"]]
    assert result.dependencies.graph.number_of_edges() == 2
