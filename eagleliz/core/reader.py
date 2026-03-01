"""
Core EagleLiz reader functionality.

This module provides the classes for scanning and parsing elements
within an Eagle.cool library folder.
"""
import json
import base64
from dataclasses import dataclass, field
from pathlib import Path
from typing import Generator, List, Optional, Tuple

from rich import print
from tqdm import tqdm
from pylizlib.core.domain.os import FileType
from pylizlib.core.os.file import get_file_type

from eagleliz.model.metadata import Metadata


class EagleItem:
    """
    Representation of an item loaded from the Eagle catalog's filesystem.
    
    Attributes:
        file_path (Path): Path to the actual media asset file on disk.
        metadata (Metadata): Parsed Metadata object extracted from `metadata.json`.
        base64_content (Optional[str]): Base64 encoded string of the asset, if requested.
    """
    def __init__(self, file_path: Path, metadata: Metadata, base64_content: Optional[str] = None):
        """
        Initializes an EagleItem explicitly.
        
        Args:
            file_path (Path): Fast system Path pointing to the main file.
            metadata (Metadata): Pydantic structured metadata object.
            base64_content (Optional[str]): Inline file content as base64 string.
        """
        self.file_path = file_path
        self.metadata = metadata
        self.base64_content = base64_content


class EagleCoolReader:
    """
    Reader for scanning and processing an Eagle.cool library catalog format.
    
    Attributes:
        catalogue (Path): Absolute path of the `.library` bundle directory.
        include_deleted (bool): Flag determining if items marked deleted should be included.
        file_types (List[FileType]): Allowed enum type file formats to include.
        filter_tags (Optional[List[str]]): List of tags to filter against.
        include_base64 (bool): Flag to aggressively read file bytes into base64.
        items (List[EagleItem]): Accepted list of populated, mapped Eagle items.
        error_paths (List[Tuple[Path, str]]): Paths that raised filesystem or parsing errors.
        items_skipped (List[Tuple[EagleItem, str]]): Valid items filtered down during scan.
        scanned_folders_count (int): Counter for the number of internal folder UUIDs scanned.
    """
    def __init__(self, catalogue: Path, include_deleted: bool = False, file_types: List[FileType] = None, filter_tags: Optional[List[str]] = None, include_base64: bool = False):
        """
        Initializes the library reader.
        
        Args:
            catalogue (Path): Absolute path of the `.library` bundle directory.
            include_deleted (bool): If True, retains logically deleted media items. Defaults to False.
            file_types (List[FileType]): Restricted valid media formats. Defaults to Image, Video, Audio.
            filter_tags (Optional[List[str]]): Tag arrays evaluated via OR strategy to narrow down search.
            include_base64 (bool): If True, will synchronously cache local media into a utf-8 base64 buffer.
        """
        self.catalogue = catalogue
        self.include_deleted = include_deleted
        self.file_types = file_types if file_types else [FileType.IMAGE, FileType.VIDEO, FileType.AUDIO]
        self.filter_tags = filter_tags
        self.include_base64 = include_base64
        self.items: List[EagleItem] = []
        self.error_paths: List[Tuple[Path, str]] = []
        self.items_skipped: List[Tuple[EagleItem, str]] = []
        self.scanned_folders_count: int = 0

    def run(self):
        """
        Execute the scanning phase iterating over the catalog files.
        Populates standard lists of `items`, `items_skipped`, and `error_paths`.
        
        Raises:
            ValueError: If the `images` directory is not inherently present within the .library folder.
        """
        images_dir = self.catalogue / "images"

        if not images_dir.exists():
            raise ValueError(f"Eagle catalogue 'images' directory not found: {images_dir}")

        folders = list(images_dir.iterdir())
        for folder in tqdm(folders, desc="Scanning Eagle Library folders", unit="folders"):
            if folder.is_dir():
                self.scanned_folders_count += 1
                result = self.__handle_eagle_folder(folder)
                if result:
                    self.items.append(result)

    def __handle_eagle_folder(self, folder: Path) -> Optional[EagleItem]:
        """
        Process a specific UUID folder within the catalog.
        
        Args:
            folder (Path): System path object towards the generated subfolder.
            
        Returns:
            Optional[EagleItem]: Nullable EagleItem initialized based on `metadata.json` mapping. None if failed/filtered.
        """
        metadata_obj, media_file, error_occurred = self.__scan_folder_contents(folder)

        if error_occurred:
            return None

        # Check missing components
        if not metadata_obj or not media_file:
            reason = []
            if not metadata_obj:
                reason.append("Missing metadata.json")
            if not media_file:
                reason.append("Missing media file")
            self.error_paths.append((folder, ", ".join(reason)))
            return None

        eagle_item = EagleItem(media_file, metadata_obj)

        # Check for deleted items
        if metadata_obj.isDeleted and not self.include_deleted:
            self.items_skipped.append((eagle_item, "Item is deleted"))
            return None

        # Check file type
        try:
            detected_type = get_file_type(str(media_file))
            if detected_type not in self.file_types:
                self.items_skipped.append((eagle_item, f"File type not requested: {detected_type.name}"))
                return None
        except ValueError:
            self.items_skipped.append((eagle_item, f"Unsupported file type: {media_file.suffix}"))
            return None
            
        # Check tags
        if self.filter_tags:
            if not any(tag in metadata_obj.tags for tag in self.filter_tags):
                self.items_skipped.append((eagle_item, "Tag mismatch"))
                return None

        # Read base64 content if requested
        if self.include_base64:
            try:
                with open(media_file, "rb") as f:
                    eagle_item.base64_content = base64.b64encode(f.read()).decode('utf-8')
            except Exception as e:
                print(f"[red]Error reading/encoding file {media_file}: {e}[/red]")
                # If reading fails, we might want to skip the item or just log it.
                # For now, I'll just log it and leave base64_content as None.
                pass

        # TODO: Implement stricter checking based on self.file_types (e.g. separate Audio, Video, Image)
        
        return eagle_item

    def __scan_folder_contents(self, folder: Path) -> Tuple[Optional[Metadata], Optional[Path], bool]:
        """
        Scans strictly within a subfolder to isolate exact logical media file targets.
        
        Args:
            folder (Path): The `.library/images/<UUID>` local subfolder structure.
            
        Returns:
            Tuple[Optional[Metadata], Optional[Path], bool]: 
                Index 0 points to Pydantic metadata.
                Index 1 indicates exact media filepath ignoring thumbnails.
                Index 2 is a strict error-flag asserting true if catastrophic disk failure occurs.
        """
        metadata_obj = None
        media_candidates = []

        for file_path in folder.iterdir():
            if not file_path.is_file():
                continue

            if "_thumbnail" in file_path.name:
                continue

            if file_path.name == "metadata.json":
                metadata_obj = self.__load_metadata(file_path, folder)
                if metadata_obj is None:
                    return None, None, True
            else:
                media_candidates.append(file_path)
        
        media_file = self._determine_main_file(media_candidates)
        
        return metadata_obj, media_file, False

    def _determine_main_file(self, file_candidates: List[Path]) -> Optional[Path]:
        """
        Determines the main file representation when multiple asset backups overlap in logic.
        Implements strict priority hierarchies for HEIC bounding arrays.
        
        Args:
            file_candidates (List[Path]): Remaining files matching target characteristics.
            
        Returns:
            Optional[Path]: Narrowed precise representation target layout object.
        """
        if not file_candidates:
            return None
            
        # Logic 1: Handle HEIC and DNG pairs (.heic/.dng and .heic.png/.dng.png)
        priority_extensions = ['.heic', '.dng']
        for ext in priority_extensions:
            target_files = [f for f in file_candidates if f.suffix.lower() == ext]
            for target_file in target_files:
                # Check if there is a corresponding .ext.png file
                potential_png = target_file.with_name(target_file.name + ".png")
                if potential_png in file_candidates:
                    return target_file

        # Default: Return the first candidate found
        # (This preserves existing behavior for single files or unspecified priorities)
        return file_candidates[0]

    def __load_metadata(self, file_path: Path, folder: Path) -> Optional[Metadata]:
        """
        Parses strictly typed Pydantic metadata safely.
        
        Args:
            file_path (Path): Path to the `metadata.json`.
            folder (Path): Root mapping directory for internal reference logic.
            
        Returns:
            Optional[Metadata]: Defined typing payload or None on parse exception handler.
        """
        try:
            with file_path.open('r', encoding='utf-8') as f:
                data = json.load(f)
                return Metadata.from_json(data)
        except Exception as e:
            print(f"[red]Error reading metadata from {file_path}: {e}[/red]")
            self.error_paths.append((folder, f"Error reading metadata: {e}"))
            return None
