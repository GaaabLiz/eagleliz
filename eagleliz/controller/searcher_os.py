"""
Standard filesystem search strategy.

Scans the filesystem recursively for media files, applying regex exclusions
and validating files as LizMedia items.
"""
import os
import re
from pathlib import Path

import typer
from tqdm import tqdm

from pylizlib.media.lizmedia import LizMedia, MediaListResult, LizMediaSearchResult, MediaStatus


class FileSystemSearcher:
    """
    Strategy class to search for media files in the file system.
    """
    def __init__(self, path: str):
        """
        Initialize with the root path to scan.
        
        :param path: Directory path to start the recursive scan.
        """
        self.path = path

    def search(self, exclude: str = None, dry: bool = False) -> MediaListResult:
        """
        Performs a recursive scan of the filesystem.
        
        :param exclude: Optional regex pattern to exclude certain files or directories.
        :param dry: If True, simulate the scan and log exclusions.
        :return: A MediaListResult containing accepted and rejected items.
        """
        result = MediaListResult()
        exclude_regex = None

        if exclude:
            try:
                exclude_regex = re.compile(exclude)
            except re.error as e:
                print(f"Error compiling regex '{exclude}': {e}")
                raise typer.Exit(code=1)

        # Use a single tqdm bar for the entire scanning process
        with tqdm(desc="Initializing scan...", unit="files") as pbar:
            for root, _, files in os.walk(self.path):
                for file in files:
                    file_path = Path(root) / file
                    pbar.set_description(f"Scanning {file}")
                    
                    # Check exclude pattern
                    if exclude_regex and exclude_regex.search(file):
                        if dry:
                            tqdm.write(f"  Skipping (regex match): {file}")
                        result.rejected.append(LizMediaSearchResult(
                            status=MediaStatus.REJECTED,
                            path=file_path,
                            media=None,
                            reason="Rejected by regex pattern"
                        ))
                        pbar.update(1)
                        continue

                    try:
                        liz_media = LizMedia(file_path)
                        result.accepted.append(LizMediaSearchResult(
                            status=MediaStatus.ACCEPTED,
                            path=file_path,
                            media=liz_media
                        ))
                    except ValueError:
                        # Not a media file, skip silently
                        pass
                    
                    pbar.update(1)
            
            pbar.set_description("Scanning complete")
        
        return result
