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
    Represents the result of an attempt to organize a single file.
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
    Configuration options for the media organization process.
    """
    no_progress: bool = False
    daily: bool = False
    copy: bool = False
    no_year: bool = False
    delete_duplicates: bool = False
    dry_run: bool = False
    exif: bool = False
