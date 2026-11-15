"""Command-line entry points for WeaveSkein."""

from pathlib import Path
from typing import Annotated

import typer

from .analyzer import Analysis, analyze
from .exporter import export_report
from .resolver import Kind

app = typer.Typer(
    help="Untangle your codebase. Explore local Python module dependencies.",
    no_args_is_help=True,
    add_completion=False,
    rich_markup_mode=None,
)
Project = Annotated[Path, typer.Argument(help="Python repository, src tree or package directory.")]
Output = Annotated[Path, typer.Option("--output", "-o", help="Destination HTML file.")]
CURRENT = Path(".")
DEFAULT_REPORT = Path("report.html")


def _printable(message: str) -> str:
    return "".join(char if char.isprintable() else ascii(char)[1:-1] for char in message)


def _analyze(project: Path) -> Analysis:
    try:
        result = analyze(project)
    except (OSError, RuntimeError, ValueError) as exc:
        typer.echo(f"Error: {_printable(str(exc))}", err=True)
        raise typer.Exit(1) from exc
    for warning in result.index.warnings:
        typer.echo(f"Warning: {_printable(warning)}", err=True)
    return result


@app.command()
def scan(project: Project = CURRENT) -> None:
    """Summarize modules, direct edges, import categories and connectivity."""
    result = _analyze(project)
    deps = result.dependencies
    typer.echo(f"Modules: {len(deps.graph)}")
    typer.echo(f"Direct dependencies: {deps.graph.number_of_edges()}")
    typer.echo(f"Isolated modules: {deps.isolates}")
    typer.echo(f"Circular groups: {len(deps.cycles)}")
    typer.echo("Imports: " + ", ".join(f"{k.value} {result.counts[k]}" for k in Kind))
    if deps.graph:
        typer.echo("Most connected (incoming + outgoing):")
        for name, degree in deps.hubs():
            typer.echo(f"  {name}  {degree}")
    else:
        typer.echo("No Python modules discovered.")


@app.command()
def cycles(project: Project = CURRENT) -> None:
    """List strongly connected groups, including explicit self-imports."""
    groups = _analyze(project).dependencies.cycles
    if not groups:
        typer.echo("No dependency cycles found.")
    for number, members in enumerate(groups, 1):
        typer.echo(f"Group {number}: {', '.join(members)}")


@app.command()
def export(project: Project = CURRENT, output: Output = DEFAULT_REPORT) -> None:
    """Write a standalone interactive report that opens directly in a browser."""
    result = _analyze(project)
    try:
        destination = export_report(result, output)
    except (OSError, ValueError, RuntimeError) as exc:
        typer.echo(f"Error: {_printable(str(exc))}", err=True)
        raise typer.Exit(1) from exc
    typer.echo(f"Report: {_printable(str(destination))}")
