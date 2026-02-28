"""
Facade for media file search strategies.

Coordinates searching through the filesystem or Eagle catalogs, manages
temporary XMP generation, and provides reporting utilities.
"""
import os
import shutil
import tempfile
from pathlib import Path
from typing import List, Optional

from pylizlib.media.lizmedia import MediaListResult
from pylizlib.media.util.metadata import MetadataHandler
from pylizlib.media.view.table import MediaListResultPrinter
from rich import print
from rich.console import Console
from rich.table import Table
from tqdm import tqdm

from eagleliz.controller.searcher_eagle import EagleCatalogSearcher
from eagleliz.controller.searcher_os import FileSystemSearcher


class MediaSearcher:
    """
    Utility class to search for media files in a directory, optionally integrating with Eagle library
    or filtering by regex. Acts as a facade for specific search strategies.
    """

    def __init__(self, path: str):
        """
        Initialize the searcher with a root path.
        
        :param path: The directory path to search in.
        """
        self.path = path
        self._result = MediaListResult()
        self._console = Console()
        self.generated_xmps_list: List[tuple[str, str]] = []
        self._temp_xmp_dir: Optional[str] = None

    def get_result(self) -> MediaListResult:
        """Returns the collected search results."""
        return self._result

    def run_search_system(self, exclude: str = None, dry: bool = False):
        """
        Runs a standard filesystem search.
        
        :param exclude: Optional regex pattern for excluding files.
        :param dry: If True, only simulate the search.
        """
        searcher = FileSystemSearcher(self.path)
        self._result = searcher.search(exclude, dry)

    def run_search_eagle(self, eagletag: Optional[List[str]] = None):
        """
        Runs a search using the Eagle catalog metadata.
        
        :param eagletag: Optional list of Eagle tags to filter by.
        """
        searcher = EagleCatalogSearcher(self.path)
        searcher.search(eagletag)
        self._result = searcher.get_result()

    def printAcceptedAsTable(self, sort_index: int = 0):
        """Prints the accepted files as a formatted table."""
        printer = MediaListResultPrinter(self._result)
        printer.print_accepted(sort_index)

    def printRejectedAsTable(self, sort_index: int = 0):
        """Prints the rejected files as a formatted table."""
        printer = MediaListResultPrinter(self._result)
        printer.print_rejected(sort_index)

    def printErroredAsTable(self, sort_index: int = 0):
        """Prints the files that encountered errors as a formatted table."""
        printer = MediaListResultPrinter(self._result)
        printer.print_errored(sort_index)

    def generate_missing_xmps(self):
        """
        Generates missing XMP sidecar files for accepted media.
        """
        self.generated_xmps_list = []
        self._temp_xmp_dir = tempfile.mkdtemp(prefix="pyliz_xmp_")
        
        # Use tqdm for progress if there are items
        accepted_items = [i for i in self._result.accepted if i.media and not i.media.has_xmp_sidecar()]
        
        if not accepted_items:
             self._console.print("[green]No missing XMP files needed generation.[/green]\n")
             return

        pbar = tqdm(accepted_items, desc="Generating missing XMPs", unit="files")
        for idx, item in enumerate(pbar):
            try:
                pbar.set_description(f"Generating XMP for {item.media.file_name}")
                
                # Create a unique subdirectory for this specific media file's XMP to avoid filename collisions
                item_temp_dir = os.path.join(self._temp_xmp_dir, str(idx))
                os.makedirs(item_temp_dir, exist_ok=True)
                
                # Construct correct filename in temp dir
                media_path = Path(item.path)
                xmp_name = f"{media_path.stem}.xmp"
                temp_path = os.path.join(item_temp_dir, xmp_name)
                
                handler = MetadataHandler(item.path)
                if handler.generate_xmp(temp_path):
                    # Set the creation date in the XMP file
                    creation_date = item.media.creation_date_from_exif_or_file_or_sidecar
                    handler.set_creation_date(creation_date, temp_path)
                    
                    # If Eagle metadata is available, append it to the generated XMP
                    if item.media.eagle_metadata:
                        handler.append_eagle_to_xmp(item.media.eagle_metadata, temp_path)
                        
                    # Attach to LizMedia
                    item.media.attach_sidecar_file(Path(temp_path))
                    self.generated_xmps_list.append((item.media.file_name, temp_path))
                else:
                    self._console.print(f"[red]Failed to generate XMP for {item.media.file_name} (check logs/exiftool)[/red]")
                
            except Exception as e:
                self._console.print(f"[red]Error processing XMP for {item.media.file_name}: {e}[/red]")

        if self.generated_xmps_list:
            print("\n")
            table = Table(title=f"Generated Missing XMP Files ({len(self.generated_xmps_list)})")
            table.add_column("Media Filename", style="cyan")
            table.add_column("Generated XMP Path", style="magenta")
            
            for media_name, xmp_path in self.generated_xmps_list:
                table.add_row(media_name, xmp_path)
            
            self._console.print(table)
            print("\n")

    def cleanup_generated_xmps(self):
        """
        Deletes the temporary XMP files and the directory created.
        """
        if not self.generated_xmps_list:
            if self._temp_xmp_dir and os.path.exists(self._temp_xmp_dir):
                try:
                    shutil.rmtree(self._temp_xmp_dir)
                except OSError as e:
                    print(f"[red]Error removing temp dir {self._temp_xmp_dir}: {e}[/red]")
            return

        print("\n")
        with tqdm(self.generated_xmps_list, desc="Cleaning up temp XMP files", unit="files") as pbar:
            for _, xmp_path in pbar:
                pbar.set_description(f"Cleaning up {Path(xmp_path).name}")
                try:
                    if os.path.exists(xmp_path):
                        os.remove(xmp_path)
                except OSError as e:
                    print(f"[red]Error deleting {xmp_path}: {e}[/red]")

        # Remove the temporary directory
        if self._temp_xmp_dir and os.path.exists(self._temp_xmp_dir):
            try:
                shutil.rmtree(self._temp_xmp_dir)
                # print(f"[dim]Removed temporary directory: {self._temp_xmp_dir}[/dim]")
            except OSError as e:
                print(f"[red]Error removing temp dir {self._temp_xmp_dir}: {e}[/red]")
