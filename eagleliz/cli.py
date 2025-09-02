import json
from pathlib import Path
from typing import List

import rich
import typer

from eagleliz.system.metadata import get_tags_from_metadata, Metadata

app = typer.Typer(help="Eagle.cool utilities.")



@app.command()
def send2Immich(
        eagle_url: str = typer.Option("http://localhost:41595/", "--eagle-url", callback=validate_url, help="Eagle.cool valid url."),
        immich_url: str = typer.Option(..., "--immich-url", callback=validate_url, help="Immich server URL."),
        ignore_deleted: bool = typer.Option(True, "--ignore-deleted", help="Ignore Eagle.cool deleted items. Default: True"),
        eagle_path: Path = typer.Option(..., "--eagle-path", exists=True, file_okay=False, dir_okay=True, help="Catalogue path in Eagle.cool"),
        immich_api: str = typer.Option(..., "--immich-api", help="Immich API key."),
        ignore_tag: List[str] = typer.Option([], "--ignore-tag", help="List of tags to ignore. Can be specified multiple times."),
        pause_on_each: bool = typer.Option(False, "--pause-on-each", help="Require user input before processing next item."),
        tag_on_uploaded: str = typer.Option("immich-uploaded", "--tag-on-uploaded", help="Tag to add to items that have been uploaded to Immich. Default: 'immich-uploaded'."),
        ignore_uploaded: bool = typer.Option(True, "--ignore-uploaded", help="Ignore items that have already been uploaded to Immich (i.e., have the tag specified in --tag-on-uploaded). Default: True"),
):

    # Print parameters
    rich.print(f"Eagle URL: {eagle_url}")
    rich.print(f"Immich URL: {immich_url}")
    rich.print(f"Eagle Path: {eagle_path}")
    rich.print(f"Ignore Deleted: {ignore_deleted}")
    rich.print(f"Immich API Key: {'*' * len(immich_api)}")
    rich.print(f"Ignore Tags: {ignore_tag}")
    rich.print("\n")

    # Checking immich URL
    ok_immich = check_endpoint(str(params.immich_url))
    ok_eagle = check_endpoint(str(params.eagle_url))
    if not ok_immich:
        rich.print("[red]Error:[/red] Immich URL is not reachable.")
        raise typer.Exit(code=1)
    if not ok_eagle:
        rich.print("[red]Error:[/red] Eagle URL is not reachable.")
        raise typer.Exit(code=1)

    # Starting scanning
    rich.print("[green]All set. Starting processing...[/green]")
    path_images = eagle_path / "images"

    # Check if images folder exists
    if not path_images.exists() or not path_images.is_dir():
        rich.print(f"[red]Error:[/red] Images folder does not exist in {eagle_path}. Exiting.")
        raise typer.Exit(code=1)

    # Scanning eagle folders
    for folder in path_images.iterdir():
        if not folder.is_dir():
            continue
        rich.print(f"Checking folder[magenta]: {folder} + [/magenta]")

        # Scanning folder content
        media_files = []
        path_metadata: Path | None = None
        for item in folder.iterdir():
            if not item.is_file():
                continue
            name = item.name.lower()
            if "thumbnail" in name:
                continue
            elif name == "metadata.json":
                path_metadata = item
                rich.print(f"Found metadata file: {path_metadata.name}")
            else:
                rich.print(f"Found media file: {item.name}")
                media_files.append(item)

        # Checking found media files
        if not path_metadata:
            rich.print(f"[yellow]No metadata file found, skipping upload of media inside folder {folder}.[/yellow]")
            continue
        if len(media_files) == 0:
            rich.print(f"[yellow]No media files found in folder {folder}, skipping upload.[/yellow]")
            continue

        # Handling media files
        media = media_files[0]
        try:
            with path_metadata.open('r', encoding='utf-8') as f:
                media_json = json.load(f)
            media_obj = Metadata.from_json(media_json)
        except json.decoder.JSONDecodeError:
            rich.print("[red]Error:[/red] Invalid JSON in metadata file, skipping upload.")
            continue

        # Check ignore conditions
        to_ignore = False
        for tag in ignore_tag:
            if tag in media_obj.tags:
                rich.print(f"[yellow]Tag '{tag}' found in media {media.name}, skipping upload.[/yellow]")
                to_ignore = True
                break
        if ignore_uploaded and tag_on_uploaded in media_obj.tags:
            rich.print(f"[yellow]Media {media.name} already uploaded to Immich (tag '{tag_on_uploaded}' found), skipping.[/yellow]")
            to_ignore = True
        if to_ignore:
            continue

        # Upload to Immich
        rich.print(f"Uploading {media.name} to Immich...")


if __name__ == "__main__":
    app()