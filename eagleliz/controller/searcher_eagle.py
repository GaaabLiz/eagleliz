"""
Search strategy for Eagle library catalogs.

Integrates with the EagleCool reader to extract media items and metadata
from an Eagle library folder.
"""
import time
from pathlib import Path
from typing import List, Optional

from rich import print
from tqdm import tqdm

from pylizlib.core.domain.os import FileType
from pylizlib.core.os.file import is_media_file, is_media_sidecar_file
from pylizlib.eaglecool.reader import EagleCoolReader
from pylizlib.media.lizmedia import LizMedia, MediaListResult, LizMediaSearchResult, MediaStatus


class EagleCatalogSearcher:
    """
    Strategy class to search for media files using the Eagle library.
    """
    def __init__(self, path: str):
        """
        Initialize with the path to the Eagle library.
        
        :param path: Base path of the Eagle library.
        """
        self.path = path
        self._result = MediaListResult()

    def get_result(self) -> MediaListResult:
        """Returns the search result object."""
        return self._result

    def search(self, eagletag: Optional[List[str]] = None):
        """
        Performs the search in the Eagle catalog.
        
        :param eagletag: Optional list of tags to filter by.
        """
        self._result = MediaListResult() # Reset result on new search
        reader = EagleCoolReader(
            Path(self.path), 
            file_types=[FileType.IMAGE, FileType.VIDEO, FileType.AUDIO, FileType.MEDIA_SIDECAR],
            filter_tags=eagletag
        )
        
        # Run the reader to populate findings (blocking operation with its own progress bar)
        reader.run() 
        
        self._process_accepted_items(reader)
        self._process_skipped_items(reader)
        self._process_errors(reader)
        self._print_summary(reader)

    def _process_accepted_items(self, reader: EagleCoolReader):
        """Process items accepted by the Eagle reader, handling media and sidecars."""
        media_items = []
        sidecar_items = []

        # Split items into media and sidecars
        for item in reader.items:
            path_str = str(item.file_path)
            if is_media_file(path_str):
                media_items.append(item)
            elif is_media_sidecar_file(path_str):
                sidecar_items.append(item)
            else:
                # Should not happen given Reader filters, but fallback
                self._result.rejected.append(LizMediaSearchResult(
                    status=MediaStatus.REJECTED,
                    path=item.file_path,
                    reason="Unknown file type in accepted list"
                ))

        # Process Media Items
        with tqdm(media_items, desc="Processing Eagle Media", unit="items") as pbar:
            for eagle in pbar:
                pbar.set_description(f"Processing {eagle.file_path.name}")
                
                lizmedia = LizMedia(eagle.file_path)
                lizmedia.attach_eagle_metadata(eagle.metadata)
                
                self._result.accepted.append(LizMediaSearchResult(
                    status=MediaStatus.ACCEPTED,
                    path=eagle.file_path,
                    media=lizmedia
                ))
                pbar.update(1)
            pbar.set_description("Media processing complete")

        # Map for sidecar linking
        accepted_map_by_stem = {item.path.stem: item for item in self._result.accepted}
        accepted_map_by_name = {item.path.name: item for item in self._result.accepted}

        # Process Sidecar Items
        with tqdm(sidecar_items, desc="Linking Sidecars", unit="items") as pbar:
            for sidecar in pbar:
                stem = sidecar.file_path.stem
                
                # Check match by name (e.g. image.png.xmp -> matches image.png)
                if stem in accepted_map_by_name:
                    accepted_map_by_name[stem].media.attach_sidecar_file(sidecar.file_path)
                    pbar.update(1)
                    continue
                
                # Check match by stem (e.g. image.xmp -> matches image.png)
                if stem in accepted_map_by_stem:
                    accepted_map_by_stem[stem].media.attach_sidecar_file(sidecar.file_path)
                    pbar.update(1)
                    continue
                
                # Orphan sidecar
                self._result.rejected.append(LizMediaSearchResult(
                    status=MediaStatus.REJECTED,
                    path=sidecar.file_path,
                    reason="Orphan sidecar file (no matching media)"
                ))
                pbar.update(1)

    def _process_skipped_items(self, reader: EagleCoolReader):
        """Process items skipped by the Eagle reader (e.g. deleted, wrong tag)."""
        for eagle_item, reason in tqdm(reader.items_skipped, desc="Processing Skipped Items", unit="items"):
            media_obj = None
            try:
                # Attempt to create LizMedia only if it's a media file, otherwise None
                if is_media_file(str(eagle_item.file_path)):
                    media_obj = LizMedia(eagle_item.file_path)
            except ValueError:
                pass

            self._result.rejected.append(LizMediaSearchResult(
                status=MediaStatus.REJECTED,
                path=eagle_item.file_path,
                media=media_obj,
                reason=reason
            ))

    def _process_errors(self, reader: EagleCoolReader):
        """Process errors encountered by the Eagle reader."""
        for error_path, reason in tqdm(reader.error_paths, desc="Processing Reader Errors", unit="errors"):
            self._result.errored.append(LizMediaSearchResult(
                status=MediaStatus.REJECTED,
                path=error_path,
                media=None,
                reason=reason
            ))

    def _print_summary(self, reader: EagleCoolReader):
        """Print a summary of the search results."""
        print("\n[bold cyan]Eagle Search Summary:[/bold cyan]")
        print(f"  Scanned folders: {reader.scanned_folders_count}")
        print(f"  File types: {', '.join([ft.name for ft in reader.file_types])}")
        print(f"  Eagle Items created: {len(reader.items) + len(reader.items_skipped)}")
        print(f"  Accepted items: {len(self._result.accepted)}")
        print(f"  Rejected items: {len(self._result.rejected)}")
        print(f"  Errored items: {len(self._result.errored)}")
        
        total_sidecars = sum(len(item.media.attached_sidecar_files) for item in self._result.accepted if item.media)
        print(f"  Sidecar files linked: {total_sidecars}")
