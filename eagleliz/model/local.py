from pathlib import Path
from typing import Optional

from eagleliz.model.metadata import Metadata


class EagleLocalItem:
    """
    Representation of an item loaded from the Eagle catalog's filesystem.

    Attributes:
        file_path (Path): Path to the actual media asset file on disk.
        metadata (Metadata): Parsed Metadata object extracted from `metadata.json`.
        base64_content (Optional[str]): Base64 encoded string of the asset, if requested.
    """

    def __init__(self, file_path: Path, metadata: Metadata, base64_content: Optional[str] = None):
        """
        Initializes an EagleLocalItem explicitly.

        Args:
            file_path (Path): Fast system Path pointing to the main file.
            metadata (Metadata): Pydantic structured metadata object.
            base64_content (Optional[str]): Inline file content as base64 string.
        """
        self.file_path = file_path
        self.metadata = metadata
        self.base64_content = base64_content

