from pathlib import Path

import requests
import typer
from pydantic import BaseModel, AnyUrl, ValidationError



class Send2ImmichParams(BaseModel):
    eagle_url: AnyUrl
    immich_url: AnyUrl
    eagle_path: Path


def check_endpoint(url: str, name: str) -> bool:
    """Controlla se un endpoint risponde correttamente con HTTP 200."""
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            typer.echo(f"✅ {name} ({url}) è raggiungibile.")
            return True
        else:
            typer.echo(f"⚠️  {name} ({url}) ha risposto con codice {response.status_code}.")
            return False
    except requests.RequestException as e:
        typer.echo(f"❌ Errore nel contattare {name} ({url}): {e}")
        return False


def handle_media(media_list: list[Path], metadata: Path | None, immich_url: str):
    if not metadata:
        typer.echo("No metadata file found, skipping upload.")
        return
    media = media_list[0]
    typer.echo(f"Checking media {media.name}..")


def execSend2Immich(params: Send2ImmichParams):

    # Controllo connessione Eagle e Immich
    typer.echo("🔍 Verifica degli endpoint...")
    ok_eagle = check_endpoint(str(params.eagle_url), "Eagle")
    ok_immich = check_endpoint(str(params.immich_url), "Immich")

    if not (ok_eagle and ok_immich):
        typer.echo("❌ Uno o più endpoint non rispondono correttamente. Interruzione.")
        raise typer.Exit(code=1)

    typer.echo(f"📂 Path Eagle valido: {params.eagle_path}")
    typer.echo("🚀 Tutto pronto per procedere con l'invio!")

    # Ciclo il catalogo eagle
    path_images = params.eagle_path / "images"
    if not path_images.exists() or not path_images.is_dir():
        typer.echo(f"❌ La cartella 'images' non esiste in {params.eagle_path}. Interruzione.")
        raise typer.Exit(code=1)

    for item in path_images.iterdir():
        if item.is_dir():
            typer.echo(f"📁 Controllo cartella: {item.name}")
            for file in item.iterdir():
                if file.is_file():
                    typer.echo(f"   📄 Trovato file: {file.name}")
                    media_files = []
                    path_metadata = None
                    name = file.name.lower()
                    if "thumbnail" in name:
                        typer.echo("Skipping thumbnail file {}".format(file.name))
                        continue
                    elif name == "metadata.json":
                        media_files.append(file)
                        typer.echo("Found metadata file: {}".format(file.name))
                    else:
                        typer.echo("Found media file: {}".format(file.name))
            typer.echo("Checking media for immich upload for directory: {}".format(item.name))