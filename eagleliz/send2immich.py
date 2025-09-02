import json
import os
from datetime import datetime
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


def get_tags_from_metadata(metadata: Path) -> list[str]:
    # Apri e leggi il contenuto del file JSON
    with metadata.open('r', encoding='utf-8') as file:
        data = json.load(file)
    # Estrai la lista di tags
    tags_list = data.get('tags', [])
    # Controlla che sia una lista e ritorna la lista di stringhe
    if not isinstance(tags_list, list):
        print("Warning: 'tags' is not a list in metadata.")
        return []
    return [str(tag) for tag in tags_list]



def update_immich_asset(asset_id: str, description: str):
    API_KEY = 'qXsLbkKJqnkuDexLRyOe71SZsnB6ivBejRmaQNTnss'                # replace with a valid api key
    BASE_URL = f'http://truenas.local:30041/api/assets/{asset_id}'

    typer.echo(f"Updating Immich asset {asset_id} with description '{description}'")

    payload = json.dumps({
        "description": description,
    })

    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'x-api-key': API_KEY
    }

    response = requests.request("PUT", BASE_URL, headers=headers, data=payload)
    print(response.text)




def upload_to_immich(media: Path, immich_url: str, tags: list[str]) -> tuple[bool, str | None]:
    API_KEY = 'qXsLbkKJqnkuDexLRyOe71SZsnB6ivBejRmaQNTnss'                # replace with a valid api key
    BASE_URL = 'http://truenas.local:30041/api'  # replace as needed

    stats = os.stat(media)

    headers = {
        'Accept': 'application/json',
        'x-api-key': API_KEY
    }

    data = {
        'deviceAssetId': f'{media}-{stats.st_mtime}',
        'deviceId': 'python',
        'fileCreatedAt': datetime.fromtimestamp(stats.st_mtime),
        'fileModifiedAt': datetime.fromtimestamp(stats.st_mtime),
        'isFavorite': 'false',
    }

    files = {
        'assetData': open(media, 'rb')
    }

    response = requests.post(
        f'{BASE_URL}/assets', headers=headers, data=data, files=files)

    print(response.json())

    return response.status_code == 200, response.json().get('id', None)



def handle_media(media_list: list[Path], metadata: Path | None, immich_url: str):
    if not metadata:
        typer.echo("No metadata file found, skipping upload.")
        return
    if len(media_list) == 0:
        typer.echo("No media files found, skipping upload.")
        return
    media = media_list[0]
    typer.echo(f"Checking media {media.name}...")
    tag_list = get_tags_from_metadata(metadata)
    typer.echo(f"Tags found: {tag_list}")
    if "immich-uploaded" in tag_list:
        typer.echo(f"Media {media.name} already uploaded to Immich, skipping.")
        return

    # Upload to Immich
    typer.echo(f"Uploading {media.name} to Immich...")
    success, asset_id = upload_to_immich(media, immich_url, tag_list)
    update_immich_asset(asset_id, "Uploaded from Eagle")


def execSend2Immich(params: Send2ImmichParams):

    # Controllo connessione Eagle e Immich
    typer.echo("Checking endpoints...")
    ok_eagle = check_endpoint(str(params.eagle_url), "Eagle")
    ok_immich = check_endpoint(str(params.immich_url), "Immich")

    if not (ok_eagle and ok_immich):
        typer.echo("One or more endpoints are not reachable. Exiting.", err=True)
        raise typer.Exit(code=1)

    typer.echo(f"Eagle path to scan: {params.eagle_path}")
    typer.echo("All set. Starting processing...")

    # Ciclo il catalogo eagle
    path_images = params.eagle_path / "images"
    if not path_images.exists() or not path_images.is_dir():
        typer.echo(f"Images folder does not exist in {params.eagle_path}. Exiting.", err=True)
        raise typer.Exit(code=1)

    for folder in path_images.iterdir():
        if not folder.is_dir():
            continue
        typer.echo(f"📁 Checking folder: {folder.name}")
        media_files = []
        path_metadata = None
        for item in folder.iterdir():
            if not item.is_file():
                continue
            name = item.name.lower()
            if "thumbnail" in name:
                typer.echo(f"Skipping thumbnail file: {item}")
                continue
            elif name == "metadata.json":
                path_metadata = item
                typer.echo(f"Found metadata file: {path_metadata}")
            else:
                typer.echo(f"Found media file: {item}")
                media_files.append(item)
        typer.echo(f"Checking media for immich upload for directory: {folder}")
        handle_media(media_files, path_metadata, str(params.immich_url))
        input("Press Enter to continue...")