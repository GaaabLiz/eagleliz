"""
Command line interface for the media organizer script.

Provides the 'organizer' command for the pylizmedia CLI tool.
"""
from pathlib import Path
from typing import List, Optional
import os
import typer
from rich import print
from rich.console import Console
from rich.table import Table

from eagleliz import eagleliz_app
from eagleliz.controller.searcher import MediaSearcher
from eagleliz.controller.media_org import MediaOrganizer
from eagleliz.domain import OrganizerOptions


@eagleliz_app.command()
def organizer(
        path: str = typer.Argument(
            None,
            dir_okay=True,
            readable=True,
            help="Source path of files to organize",
            envvar="PYL_M_ORG_PATH"
        ),
        output: str = typer.Argument(
            None,
            dir_okay=True,
            writable=True,
            readable=True,
            help="Destination path for organized files",
            envvar="PYL_M_ORG_OUTPUT"
        ),
        eaglecatalog: bool = typer.Option(
            False,
            "--eaglecatalog",
            help="Import metadata from Eagle catalog",
            envvar="PYL_M_ORG_EAGLECATALOG"
        ),
        eagletag: Optional[List[str]] = typer.Option(
            None,
            "--eagletag", "-et",
            help="Eagle tags to apply (can be repeated: -et tag1 -et tag2)",
            envvar="PYL_M_ORG_EAGLETAG"
        ),
        xmp: bool = typer.Option(
            False,
            "--xmp",
            help="Generate XMP files for metadata",
            envvar="PYL_M_ORG_XMP"
        ),
        dry: bool = typer.Option(
            False,
            "--dry",
            help="Run in dry-run mode (preview only)",
            envvar="PYL_M_ORG_DRY"
        ),
        exclude: str = typer.Option(
            None,
            "--exclude", "-ex",
            help="Regex pattern to exclude files (-ex '.*\\.tmp' -ex '.*\\.temp')",
            envvar="PYL_M_ORG_EXCLUDE"
        ),
        list_accepted: bool = typer.Option(
            True,
            "--list-accepted", "-lac",
            help="List accepted file during search.",
            envvar="PYL_M_ORG_LIST_ACCEPTED"
        ),
        list_rejected: bool = typer.Option(
            True,
            "--list-rejected", "-lrej",
            help="List rejected files during search.",
            envvar="PYL_M_ORG_LIST_REJECTED"
        ),
        list_errored: bool = typer.Option(
            True,
            "--list-errored", "-lerr",
            help="List errored files during search.",
            envvar="PYL_M_ORG_LIST_ERRORED"
        ),
        list_accepted_order_index: int = typer.Option(
            0,
            "--list-accepted-order-index", "-laoi",
            help="Index of the column to sort accepted list by (0-6). Default is 0 (Index). Columns: 0=Index, 1=Filename, 2=Creation Date, 3=Exif, 4=Ext, 5=Size, 6=Sidecars.",
            min=0,
            max=6,
            envvar="PYL_M_ORG_LIST_ACCEPTED_ORDER_INDEX"
        ),
        list_rejected_order_index: int = typer.Option(
            0,
            "--list-rejected-order-index", "-lroi",
            help="Index of the column to sort rejected list by (0-6). Default is 0 (Index). Columns: 0=Index, 1=Filename, 2=Creation Date, 3=Exif, 4=Ext, 5=Size, 6=Reason.",
            min=0,
            max=6,
            envvar="PYL_M_ORG_LIST_REJECTED_ORDER_INDEX"
        ),
        list_errored_order_index: int = typer.Option(
            0,
            "--list-errored-order-index", "-leoi",
            help="Index of the column to sort errored list by (0-6). Default is 0 (Index). Columns: 0=Index, 1=Filename, 2=Creation Date, 3=Exif, 4=Ext, 5=Size, 6=Reason.",
            min=0,
            max=6,
            envvar="PYL_M_ORG_LIST_ERRORED_ORDER_INDEX"
        ),
        print_results: bool = typer.Option(
            True,
            "--print-results", "-pres",
            help="Print organization results in a table.",
            envvar="PYL_M_ORG_PRINT_RESULTS"
        ),
        list_result_order_index: int = typer.Option(
            0,
            "--list-result-order-index", "-lresoi",
            help="Index of the column to sort results list by (0-5). Default is 0 (Index). Columns: 0=Index, 1=Status, 2=Filename, 3=Extension, 4=Destination, 5=Reason.",
            min=0,
            max=5,
            envvar="PYL_M_ORG_LIST_RESULT_ORDER_INDEX"
        )
):
    """
    Organize files in the filesystem by applying metadata and filters.

    Supports Eagle metadata, XMP, and regex patterns for file exclusion.
    """

    # Basic validations
    if not path:
        typer.echo("❌ Error: path cannot be empty", err=True)
        raise typer.Exit(code=1)
    if not output:
        typer.echo("❌ Error: output cannot be empty", err=True)
        raise typer.Exit(code=1)

    # Log parameters
    typer.echo("\n" + "─" * 50)
    typer.echo(f"📁 Source: {path}")
    typer.echo(f"📁 Output: {output}")
    typer.echo(f"🔍 Dry-run: {'Yes' if dry else 'No'}")
    typer.echo(f"🦅 Eagle Catalog: {'Yes' if eaglecatalog else 'No'}")
    if eaglecatalog:
        typer.echo(f"🏷️  Eagle Tags: {', '.join(eagletag) if eagletag else 'None'}")
    typer.echo(f"📝 XMP Metadata: {'Yes' if xmp else 'No'}")
    typer.echo(f"🚫 Exclude pattern: {exclude if exclude else 'None'}")
    typer.echo(f"✅ List accepted: {'Yes' if list_accepted else 'No'}")
    typer.echo(f"❌ List rejected: {'Yes' if list_rejected else 'No'}")
    typer.echo(f"⚠️ List errored: {'Yes' if list_errored else 'No'}")
    typer.echo(f"📊 Print results: {'Yes' if print_results else 'No'}")

    column_names_search = ["Index", "Filename", "Creation Date", "Exif", "Ext", "Size", "Extra (Sidecars/Reason)"]
    column_names_res = ["Index", "Status", "Filename", "Extension", "Destination", "Reason"]
    sort_col_acc = column_names_search[list_accepted_order_index]
    sort_col_rej = column_names_search[list_rejected_order_index]
    sort_col_err = column_names_search[list_errored_order_index]
    sort_col_res = column_names_res[list_result_order_index]
    typer.echo(f"🔢 Accepted list sort: {sort_col_acc} (index {list_accepted_order_index})")
    typer.echo(f"🔢 Rejected list sort: {sort_col_rej} (index {list_rejected_order_index})")
    typer.echo(f"🔢 Errored list sort: {sort_col_err} (index {list_errored_order_index})")
    typer.echo(f"🔢 Results list sort: {sort_col_res} (index {list_result_order_index})")
    typer.echo("─" * 50 + "\n")

    # Searching file to organize
    searcher = MediaSearcher(path)
    if eaglecatalog:
        searcher.run_search_eagle(eagletag)
    else:
        searcher.run_search_system(exclude, dry)

    search_result = searcher.get_result()
    media_global = search_result.accepted

    # Logging search results
    print("\n")
    if list_accepted:
        with Console().status("[bold cyan]Generating Accepted Table...[/bold cyan]"):
            searcher.printAcceptedAsTable(list_accepted_order_index)

    print("\n")
    if list_rejected:
        with Console().status("[bold cyan]Generating Rejected Table...[/bold cyan]"):
            searcher.printRejectedAsTable(list_rejected_order_index)

    print("\n")
    if list_errored:
        with Console().status("[bold cyan]Generating Errored Table...[/bold cyan]"):
            searcher.printErroredAsTable(list_errored_order_index)
    print("\n\n")

    # Check if there are files to process
    if not media_global:
        print("No files to process. Exiting.")
        raise typer.Exit(code=0)

    # Wait for user confirmation
    input("Press Enter to continue with organization...")

    if xmp:
        searcher.generate_missing_xmps()

    # Organizing files
    options = OrganizerOptions(
        no_progress=False,
        daily=False,
        copy=True,
        no_year=False,
        delete_duplicates=False,
        dry_run=dry,
        exif=True
    )

    # Pass LizMediaSearchResult objects directly to MediaOrganizer to preserve sidecar info
    organizer_instance = MediaOrganizer(media_global, output, options)
    organizer_instance.organize()

    if print_results:
        organizer_instance.print_results_table(list_result_order_index)

    if xmp:
        searcher.cleanup_generated_xmps()


