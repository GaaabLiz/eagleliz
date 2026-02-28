"""
Core organization logic for media files.

Handles the movement, copying, and conflict resolution of media files based on
metadata-derived dates and user options.
"""
import hashlib
import logging
import os
import re
import shutil
from pathlib import Path
from typing import List, Optional, Tuple

from rich import print
from rich.console import Console
from rich.table import Table
from tqdm import tqdm

from pylizlib.media.lizmedia import LizMedia, LizMediaSearchResult

from eagleliz.domain import OrganizerOptions, OrganizerResult

logger = logging.getLogger(__name__)


class MediaOrganizer:
    """
    Class responsible for organizing media files into a target directory structure
    based on their creation date (from EXIF or filesystem).
    """

    def __init__(self, search_results: list[LizMediaSearchResult], target: str, options: OrganizerOptions):
        self.search_results = search_results
        self.target = target
        self.options = options
        self._console = Console()
        self.results: List[OrganizerResult] = []

    def organize(self) -> None:
        """
        Organize files from *source* into *target* according to the provided options.
        Results are stored in self.results.
        """
        logger.info(f"Starting organization. Candidates: {len(self.search_results)}, Target: {self.target}, Options: {self.options}")
        self.results = [] # Reset results

        # Prepare iteration
        file_iter = self.search_results if self.options.no_progress else tqdm(self.search_results, unit="files", desc="Organizing")

        for item in file_iter:
            if not item.has_lizmedia():
                continue
            
            if not self.options.no_progress:
                file_iter.set_description(f"Organizing {item.media.file_name}")
            
            item_results = self._process_single_item(item)
            self.results.extend(item_results)

        # Cleanup progress bar
        if not self.options.no_progress and hasattr(file_iter, "close"):
            file_iter.close()

        logger.info(f"Organization complete. Processed {len(self.results)} items.")

    def get_results(self) -> List[OrganizerResult]:
        """Returns the list of organization results."""
        return self.results

    def print_results_table(self, sort_index: int = 0):
        """
        Prints a table of the organization results.
        
        :param sort_index: Index of the column to sort by.
                           0=Index, 1=Status, 2=Filename, 3=Extension, 4=Destination, 5=Reason
        """
        if not self.results:
            print("[yellow]No results to display.[/yellow]")
            return

        with Console().status("[bold cyan]Generating Results Table...[/bold cyan]"):
            print("\n")
            
            # Sorting logic for results
            sorted_results = list(self.results) # Create a copy to avoid modifying original order if needed elsewhere
            if sort_index == 0: # Index
                sorted_results.sort(key=lambda x: x.index)
            elif sort_index == 1: # Status
                sorted_results.sort(key=lambda x: x.success, reverse=True) # Success first
            elif sort_index == 2: # Filename
                sorted_results.sort(key=lambda x: x.source_file.name.lower())
            elif sort_index == 3: # Extension
                sorted_results.sort(key=lambda x: x.source_file.suffix.lower())
            elif sort_index == 4: # Destination
                sorted_results.sort(key=lambda x: (x.destination_path or "").lower())
            elif sort_index == 5: # Reason
                sorted_results.sort(key=lambda x: x.reason.lower())

            table = Table(title=f"Organization Results ({len(sorted_results)})")
            table.add_column(f"Index{' *' if sort_index == 0 else ''}", justify="right")
            table.add_column(f"Status{' *' if sort_index == 1 else ''}", justify="center")
            table.add_column(f"Filename{' *' if sort_index == 2 else ''}", style="cyan")
            table.add_column(f"Extension{' *' if sort_index == 3 else ''}", justify="center", style="yellow")
            table.add_column(f"Destination{' *' if sort_index == 4 else ''}", style="magenta", overflow="fold")
            table.add_column(f"Reason{' *' if sort_index == 5 else ''}", style="white", overflow="fold")

            for res in sorted_results:
                status = "[green]Success[/green]" if res.success else "[red]Failed[/red]"
                
                # Show path relative to the parent of the output directory for better readability
                if res.destination_path:
                    try:
                        dest = os.path.relpath(res.destination_path, Path(self.target).parent)
                    except ValueError:
                        # Fallback if paths are on different drives or relativity fails
                        dest = res.destination_path
                else:
                    dest = "N/A"
                
                ext = res.source_file.suffix.lower()
                display_ext = ext
                if ext in ['.xmp', '.aae']:
                    display_ext = f"[bold magenta]{ext}[/bold magenta]"
                    
                table.add_row(str(res.index), status, res.source_file.name, display_ext, dest, res.reason)
            
            Console().print(table)
            print("\n")

    def _process_single_item(self, item: LizMediaSearchResult) -> List[OrganizerResult]:
        """
        Process a single media item search result, including its sidecars.
        Returns a list of results (main item + sidecars).
        """
        results: List[OrganizerResult] = []
        media_item = item.media
        file_path = str(media_item.path)
        logger.debug(f"Processing media item: {media_item.path}")

        # 1. Sanitize Path
        try:
            sanitized_path = self._sanitize_path(file_path)
        except ValueError as e:
            logger.error(f"Rejected invalid path: {file_path}. Reason: {e}")
            return [OrganizerResult(success=False, source_file=media_item.path, media=media_item, reason=str(e))]

        # 2. Determine Dates and Paths
        year, month, day, original_timestamp = self._get_creation_details(media_item)
        target_folder = self._build_target_folder_path(self.target, year, month, day)
        target_path = os.path.join(target_folder, os.path.basename(sanitized_path))

        # 3. Ensure Directory Exists (Effect)
        if not self.options.dry_run:
            self._ensure_directory_exists(target_folder)

        # 4. Handle Main File Transfer
        main_result = None
        
        # Check for existing file (Duplicate/Conflict Logic)
        if os.path.exists(target_path):
            logger.info(f"File exists at target: {target_path}. Checking for duplicates/conflicts.")
            main_result = self._handle_existing_file(file_path, target_path, media_item)

        # If not handled as existing/duplicate, perform transfer
        if not main_result:
            main_result = self._execute_transfer(file_path, target_path, target_folder, original_timestamp, media_item)

        results.append(main_result)

        # 5. Handle Sidecars
        sidecar_results = self._process_sidecars(item, target_folder, main_result)
        results.extend(sidecar_results)

        return results

    def _get_creation_details(self, media_item: LizMedia) -> Tuple[int, int, int, float]:
        """
        Extracts creation date details from EXIF or filesystem.
        Returns: (year, month, day, timestamp)
        """
        if self.options.exif:
            creation_date = media_item.creation_date_from_exif_or_file_or_sidecar
            return creation_date.year, creation_date.month, creation_date.day, creation_date.timestamp()
        else:
            return media_item.year, media_item.month, media_item.day, media_item.creation_time.timestamp()

    def _process_sidecars(self, item: LizMediaSearchResult, target_folder: str, main_result: OrganizerResult) -> List[OrganizerResult]:
        """
        Process sidecar files associated with the main media item.
        Sidecars are processed if the main file was successful OR skipped as a duplicate.
        """
        results = []
        should_process_sidecars = False
        
        if main_result.success:
            should_process_sidecars = True
        elif main_result.reason == "Duplicate skipped":
            should_process_sidecars = True

        if should_process_sidecars and item.has_sidecars():
            # item.has_sidecars() ensures item.media is not None
            logger.debug(f"Processing {len(item.media.attached_sidecar_files)} sidecar files for: {item.media.path}. Main result: {main_result.reason}")
            
            for sidecar_path in item.media.attached_sidecar_files:
                sidecar_target = os.path.join(target_folder, sidecar_path.name)
                
                # Check if sidecar exists at target
                if os.path.exists(sidecar_target):
                    logger.debug(f"Sidecar already exists at target: {sidecar_target}. Skipping.")
                    results.append(OrganizerResult(
                        success=False, 
                        source_file=sidecar_path, 
                        reason="Sidecar exists/Duplicate skipped", 
                        destination_path=sidecar_target
                    ))
                    continue

                logger.debug(f"Transferring sidecar: {sidecar_path} -> {sidecar_target}")
                sidecar_result = self._execute_sidecar_transfer(sidecar_path, sidecar_target, target_folder)
                results.append(sidecar_result)
                
                if sidecar_result.success:
                    logger.debug(f"Sidecar transfer successful: {sidecar_path}")
                else:
                    logger.error(f"Sidecar transfer failed: {sidecar_path}. Reason: {sidecar_result.reason}")

        elif not should_process_sidecars and item.has_sidecars():
            logger.warning(f"Skipping sidecars for {item.media.path}. Main file result: success={main_result.success}, reason={main_result.reason}")
            
        return results

    def _build_target_folder_path(self, base_target: str, year: int, month: int, day: int) -> str:
        """Constructs the target folder path based on date options."""
        folder_parts = [base_target]
        if self.options.no_year:
            folder_parts.append(f"{str(year)}-{month:02d}")
        else:
            folder_parts.append(str(year))
            folder_parts.append(f"{month:02d}")
        if self.options.daily:
            folder_parts.append(f"{day:02d}")
        return os.path.join(*folder_parts)

    def _handle_existing_file(self, source_path: str, target_path: str, media: LizMedia) -> OrganizerResult | None:
        """
        Checks if file exists and handles duplicates.
        Returns OrganizerResult if handled (skipped/deleted/error), None if conflict.
        """
        source_hash = self._get_file_hash(source_path)
        target_hash = self._get_file_hash(target_path)

        if source_hash == target_hash:
            # Exact match - handle as duplicate
            logger.info(f"Duplicate content detected: {source_path} == {target_path}")
            if self.options.delete_duplicates:
                try:
                    if not self.options.dry_run:
                        os.remove(source_path)
                    logger.info(f"Duplicate deleted: {source_path}")
                    return OrganizerResult(success=False, source_file=media.path, media=media, reason="Duplicate deleted", destination_path=target_path)
                except Exception as e:
                    logger.error(f"Error deleting duplicate {source_path}: {e}")
                    return OrganizerResult(success=False, source_file=media.path, media=media, reason=f"Error deleting duplicate: {e}", destination_path=target_path)
            else:
                logger.info(f"Duplicate skipped: {source_path}")
                return OrganizerResult(success=False, source_file=media.path, media=media, reason="Duplicate skipped", destination_path=target_path)
        else:
            # Different content but same path - error
            self._console.print(f"[yellow]File conflict detected (same name, different content). Source: {source_path}, Target: {target_path}[/yellow]")
            return OrganizerResult(success=False, source_file=media.path, media=media, reason="File conflict: target exists but content differs", destination_path=target_path)

    def _execute_transfer(self, source_path: str, target_path: str, target_folder: str, original_timestamp: float, media: LizMedia) -> OrganizerResult:
        """
        Moves or copies the file and restores timestamps.
        Returns OrganizerResult.
        """
        logger.debug(f"Transferring file. Source: {source_path}, Target: {target_path}, Copy: {self.options.copy}")
        try:
            if not self.options.dry_run:
                if not os.access(target_folder, os.W_OK):
                    raise PermissionError(f"Write permission denied for {target_folder}")

                if self.options.copy:
                    shutil.copy2(source_path, target_path)
                else:
                    shutil.move(source_path, target_path)

                # Explicitly set the modification time to the original creation time
                # os.utime(target_path, (original_timestamp, original_timestamp))
            logger.info(f"Transfer successful: {source_path} -> {target_path}")
            return OrganizerResult(success=True, source_file=media.path, media=media, destination_path=target_path)
        except Exception as e:
            logger.error(f"Transfer error for {source_path}: {e}")
            return OrganizerResult(success=False, source_file=media.path, media=media, reason=f"Transfer error: {e}", destination_path=target_path)

    def _execute_sidecar_transfer(self, source_path: Path, target_path: str, target_folder: str) -> OrganizerResult:
        """
        Moves or copies a sidecar file. Returns OrganizerResult.
        """
        try:
            if not self.options.dry_run:
                if self.options.copy:
                    shutil.copy2(source_path, target_path)
                else:
                    shutil.move(source_path, target_path)
            return OrganizerResult(success=True, source_file=source_path, destination_path=target_path)
        except Exception as e:
            logger.error(f"Sidecar transfer error for {source_path}: {e}")
            return OrganizerResult(success=False, source_file=source_path, reason=f"Sidecar transfer error: {e}", destination_path=target_path)

    def _sanitize_path(self, path: str) -> str:
        """Sanitize path to prevent path traversal attacks."""
        if re.search(r'(\.\.[/\\]|^\.\.[/\\]|^\.\.)', path):
            raise ValueError("Path contains invalid traversal components")
        sanitized = os.path.normpath(path)
        return sanitized

    def _ensure_directory_exists(self, folder_path: str):
        """Ensure the given folder path exists."""
        os.makedirs(folder_path, exist_ok=True)

    def _get_file_hash(self, file_path: str, max_size: int = 100 * 1024 * 1024) -> str | None:
        """Get MD5 hash of file (for quick duplicate checks)."""
        try:
            if os.path.getsize(file_path) > max_size:
                return "LARGE_FILE"
            with open(file_path, 'rb') as f:
                chunk = f.read(4096)
                if not chunk:
                    return None
                hash_obj = hashlib.md5()
                while chunk:
                    hash_obj.update(chunk)
                    chunk = f.read(4096)
            return hash_obj.hexdigest()
        except Exception:
            return None
