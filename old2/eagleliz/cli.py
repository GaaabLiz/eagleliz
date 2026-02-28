import sys
import os
from pathlib import Path

# Add the project root to sys.path to allow running this script directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import typer

from old2.eagleliz.exporg import ExportOrganizedWorkflow

app = typer.Typer(help="General utility scripts.")


@app.command("exporg")
def export_organized(
    eagle_path: Path = typer.Option(..., "--catalogue-path", exists=True, file_okay=False, dir_okay=True, help="Catalogue path in Eagle.cool"),
    tag: str = typer.Option(..., "--tag", help="Source tag to use when exporting media."),
    output_path: Path = typer.Option(..., "--output-path", exists=True, file_okay=False, dir_okay=True, help="Output path."),
    xmp: bool = typer.Option(False, help="Generate XMP sidecar files.")
):
    workflow = ExportOrganizedWorkflow(eagle_path, output_path, tag, xmp)
    workflow.run()


if __name__ == "__main__":
    app()