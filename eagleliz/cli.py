from pathlib import Path

import requests
import typer
from pydantic import BaseModel, AnyUrl, ValidationError

from eagleliz.send2immich import Send2ImmichParams, execSend2Immich

app = typer.Typer(help="Eagle.cool utilities.")




@app.command()
def send2Immich(
        eagle_url: str = typer.Option(..., "--eagle-url", help="URL valido di Eagle"),
        immich_url: str = typer.Option(..., "--immich-url", help="URL valido di Immich"),
        eagle_path: Path = typer.Option(..., "--eagle-path", exists=True, file_okay=False, help="Path locale valido di Eagle"),
):
    # Check parameters
    try:
        params = Send2ImmichParams(eagle_url=eagle_url, immich_url=immich_url, eagle_path=eagle_path)
    except ValidationError as e:
        typer.echo(f"Errore di validazione: {e}")
        raise typer.Exit(code=1)

    typer.echo(f"Eagle URL: {params.eagle_url}")
    typer.echo(f"Immich URL: {params.immich_url}")
    typer.echo(f"Eagle Path: {params.eagle_path}")

    # Executing script
    execSend2Immich(params)



if __name__ == "__main__":
    app()