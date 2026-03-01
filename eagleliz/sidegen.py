"""
Command line interface for generating sidecar files.

Provides the 'sidegen' command for the pylizmedia CLI tool.
"""
from pathlib import Path
from typing import List, Optional
import os
import typer
from pylizlib.media.util.metadata import MetadataHandler
from rich import print
from rich.console import Console
from tqdm import tqdm

from eagleliz import eagleliz_app
from eagleliz.controller.searcher_eagle import EagleCatalogSearcher


@eagleliz_app.command()
def sidegen(
        path: str = typer.Argument(
            None,
            dir_okay=True,
            readable=True,
            help="Source path of Eagle catalog",
            envvar="PYL_M_SIDEGEN_PATH"
        ),
        eagletag: Optional[List[str]] = typer.Option(
            None,
            "--eagletag", "-et",
            help="Eagle tags to filter by (can be repeated: -et tag1 -et tag2)",
            envvar="PYL_M_SIDEGEN_EAGLETAG"
        ),
        dry: bool = typer.Option(
            False,
            "--dry",
            help="Run in dry-run mode (preview only)",
            envvar="PYL_M_SIDEGEN_DRY"
        )
):
    """
    Generate XMP sidecar files for media items in an Eagle catalog.

    Scans the catalog, finds images and videos, and creates/recreates
    .xmp sidecar files in the same directory as the source media.
    If the sidecar already exists, it is deleted and recreated.
    
    Args:
        path (str): The source path of the Eagle catalog (usually ending in .library).
        eagletag (Optional[List[str]]): Eagle tags to filter the generation by.
        dry (bool): Flag to run the command in dry-run mode without modifying any files.
    """

    # Basic validations
    if not path:
        typer.echo("❌ Error: path cannot be empty", err=True)
        raise typer.Exit(code=1)

    path_obj = Path(path)
    if not path_obj.exists() or not path_obj.is_dir():
        typer.echo(f"❌ Error: path '{path}' does not exist or is not a directory", err=True)
        raise typer.Exit(code=1)

    # Log parameters
    typer.echo("\n" + "─" * 50)
    typer.echo(f"🦅 Eagle Catalog: {path}")
    typer.echo(f"🏷️  Eagle Tags: {', '.join(eagletag) if eagletag else 'None'}")
    typer.echo(f"🔍 Dry-run: {'Yes' if dry else 'No'}")
    typer.echo("─" * 50 + "\n")

    # Search for media in Eagle catalog using EagleCatalogSearcher
    searcher = EagleCatalogSearcher(path)

    with Console().status("[bold cyan]Searching Eagle catalog...[/bold cyan]"):
        searcher.search(eagletag)

    search_result = searcher.get_result()
    media_list = search_result.accepted

    if not media_list:
        print("[yellow]No media files found in the Eagle catalog matching the criteria.[/yellow]")
        raise typer.Exit(code=0)

    print(f"\nFound [bold cyan]{len(media_list)}[/bold cyan] media files.")

    # Process files
    processed_count = 0
    error_count = 0

    pbar = tqdm(media_list, desc="Generating XMP sidecars", unit="files")
    for item in pbar:
        if not item.media:
            continue

        media = item.media
        pbar.set_description(f"Processing {media.file_name}")

        # Sidecar path: same folder, .xmp extension
        # Using with_suffix(".xmp") replaces the current extension.
        # This is consistent with common sidecar naming (e.g., image.jpg -> image.xmp).
        xmp_path = media.path.with_suffix(".xmp")

        if dry:
            processed_count += 1
            continue

        try:
            # Delete if exists
            if xmp_path.exists():
                xmp_path.unlink()

            handler = MetadataHandler(media.path)

            # 1. Generate XMP from source file
            if handler.generate_xmp(xmp_path):
                # 2. Set creation date in XMP (robust extraction from EXIF/Video/File)
                creation_date = media.creation_date_from_exif_or_file_or_sidecar
                handler.set_creation_date(creation_date, xmp_path)

                # 3. Append Eagle metadata (tags, annotation)
                if media.eagle_metadata:
                    handler.append_eagle_to_xmp(media.eagle_metadata, xmp_path)

                processed_count += 1
            else:
                print(f"[red]Failed to generate XMP for {media.file_name}[/red]")
                error_count += 1

        except Exception as e:
            print(f"[red]Error processing {media.file_name}: {e}[/red]")
            error_count += 1

    print("\n" + "─" * 50)
    if dry:
        print(f"🔍 [bold]Dry-run complete.[/bold]")
        print(f"Total files that would be processed: {processed_count}")
    else:
        print(f"✅ [bold]Processing complete.[/bold]")
        print(f"Successfully generated/updated: {processed_count}")
        if error_count > 0:
            print(f"Errors: {error_count}")
    print("─" * 50 + "\n")
