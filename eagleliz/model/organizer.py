"""
Domain models for the media organizer.

Contains dataclasses and structures representing organization results and configuration options.
"""
from dataclasses import dataclass, field
from itertools import count
from pathlib import Path
from typing import Optional

from pylizlib.media.lizmedia import LizMedia

# Global counter for OrganizerResult index
_result_counter = count(1)

@dataclass
class OrganizerResult:
    """
    Represents the result of an single file organization workflow step.
    
    Attributes:
        success (bool): Whether the file was properly copied, moved or parsed.
        source_file (Path): Reference to the original file to act upon computationally.
        media (Optional[LizMedia]): Analyzed media node. Left unbound on failure.
        reason (str): Empty baseline string denoting operational rejection or success flags.
        destination_path (Optional[str]): Pathing destination targeting after organization.
        index (int): Auto-generating counter identifying the exact index of this sequence block.
    """
    success: bool
    source_file: Path
    media: Optional[LizMedia] = None
    reason: str = ""
    destination_path: Optional[str] = None
    index: int = field(default_factory=lambda: next(_result_counter), init=False)

    @property
    def source_path(self) -> str:
        """Returns the source file path as a string."""
        return str(self.source_file)


@dataclass
class OrganizerOptions:
    """
    Configuration options for the media organization process defining boolean flags.
    
    Attributes:
        no_progress (bool): If True, hides CLI rich progress bar wrappers implicitly.
        daily (bool): Flag defining daily categorization structuring mapping format structures.
        copy (bool): Retains the original filesystem source without moving/destroying it natively.
        no_year (bool): Strips generic root-relative Year sorting folder nesting out.
        delete_duplicates (bool): Enforces strict checksum deletion dropping duplicates natively.
        dry_run (bool): Evaluates workflow pipelines cleanly without executing destructive filesystem saves.
        exif (bool): Leverages EXIF internal media file tags as source of truth for generation metadata creation bounds.
    """
    no_progress: bool = False
    daily: bool = False
    copy: bool = False
    no_year: bool = False
    delete_duplicates: bool = False
    dry_run: bool = False
    exif: bool = False
