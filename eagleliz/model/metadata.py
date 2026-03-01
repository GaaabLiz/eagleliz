"""
Eagle model metadata handling definitions.

This module provides the Pydantic models for parsing and generating
Eagle-compatible metadata from `metadata.json` properties.
"""
import json
from pathlib import Path
from typing import List, Optional
from xml.sax.saxutils import escape

from pydantic import BaseModel


def get_tags_from_metadata(metadata: Path) -> list[str]:
    """
    Extract a list of raw string tags from an Eagle metadata JSON file.
    
    Args:
        metadata (Path): System Path to the `.json` file.
        
    Returns:
        list[str]: Array of extracted string tags. Empty list if none or invalid type.
    """
    # Apri e leggi il contenuto del file JSON
    with metadata.open('r', encoding='utf-8') as file:
        data = json.load(file)
    # Estrai la lista di tags
    tags_list = data.get('tags', [])
    # Controlla che sia una lista e ritorna la lista di stringhe
    if not isinstance(tags_list, list):
        print("Warning: 'tags' is not a list in metadata.")
        return []
    return [str(tag) for tag in tags_list]



class Palette(BaseModel):
    """
    Pydantic schema representing a primary visual color embedded in Eagle.
    
    Attributes:
        color (List[int]): An RGB integer array formatting the color.
        ratio (float): Mathematical ratio weight of the color within the image.
    """
    color: List[int]
    ratio: float


class Metadata(BaseModel):
    """
    Pydantic schema matching the complete structure of Eagle's `metadata.json`.
    
    Attributes:
        id (Optional[str]): Unique string UUID.
        name (Optional[str]): String display name.
        size (Optional[int]): File payload size in bytes.
        btime (Optional[int]): Creation POSIX timestamp via filesystem.
        mtime (Optional[int]): Modification POSIX timestamp via filesystem.
        ext (Optional[str]): Source file extension natively.
        tags (List[str]): Assorted array of explicit strings tags.
        folders (List[str]): Ordered folder mapping arrays.
        isDeleted (bool): Trash flag indicator.
        url (Optional[str]): Captured source application origin address.
        annotation (Optional[str]): Extra metadata descriptive string payload.
        modificationTime (Optional[int]): Mod mapping for Eagle internal sort arrays.
        height (Optional[int]): Vertical layout pixel dimension.
        width (Optional[int]): Horizontal layout pixel dimension.
        noThumbnail (Optional[bool]): Native thumbnail rendering presence block flag.
        lastModified (Optional[int]): Fallback tracker timestamp modification.
        palettes (List[Palette]): Embedded Palette array elements representing colors.
        deletedTime (Optional[int]): Deleted timeline log tracking UUID identifier.
    """
    id: Optional[str] = None
    name: Optional[str] = None
    size: Optional[int] = None
    btime: Optional[int] = None
    mtime: Optional[int] = None
    ext: Optional[str] = None
    tags: List[str] = []
    folders: List[str] = []
    isDeleted: bool = False
    url: Optional[str] = None
    annotation: Optional[str] = None
    modificationTime: Optional[int] = None
    height: Optional[int] = None
    width: Optional[int] = None
    noThumbnail: Optional[bool] = False
    lastModified: Optional[int] = None
    palettes: List[Palette] = []
    deletedTime: Optional[int] = None

    @classmethod
    def from_json(cls,  dict) -> "Metadata":
        """
        Instantiate the root Metadata object strictly utilizing a parsed valid Dictionary mapping.
        
        Args:
            dict (dict): Formatted JSON content dynamically passed as Python native structures.
            
        Returns:
            Metadata: Full Pydantic representation with proper default fallback bindings initialized.
        """
        return cls(**dict)

    def to_xmp(self) -> str:
        """
        Dynamically serialize internal properties out into strictly formatted XMP XML payloads.
        Transforms implicit metadata annotations and tags into embedded Lightroom/digiKam syntax structures natively.
        
        Returns:
            str: Native formatted XMP valid metadata blob.
        """
        lines = [
            "<?xpacket begin='﻿' id='W5M0MpCehiHzreSzNTczkc9d'?>",
            '<x:xmpmeta xmlns:x="adobe:ns:meta/" x:xmptk="EagleLiz">',
            ' <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">',
            '  <rdf:Description rdf:about=""',
            '    xmlns:dc="http://purl.org/dc/elements/1.1/"',
            '    xmlns:digiKam="http://www.digikam.org/ns/1.0/">'
        ]

        if self.annotation:
            safe_desc = escape(self.annotation)
            lines.append('   <dc:description>')
            lines.append('    <rdf:Alt>')
            lines.append(f'     <rdf:li xml:lang="x-default">{safe_desc}</rdf:li>')
            lines.append('    </rdf:Alt>')
            lines.append('   </dc:description>')

        if self.tags:
            # Standard DC Subject
            lines.append('   <dc:subject>')
            lines.append('    <rdf:Bag>')
            for tag in self.tags:
                safe_tag = escape(tag)
                lines.append(f'     <rdf:li>{safe_tag}</rdf:li>')
            lines.append('    </rdf:Bag>')
            lines.append('   </dc:subject>')
            
            # DigiKam TagsList
            lines.append('   <digiKam:TagsList>')
            lines.append('    <rdf:Seq>')
            for tag in self.tags:
                safe_tag = escape(tag)
                lines.append(f'     <rdf:li>{safe_tag}</rdf:li>')
            lines.append('    </rdf:Seq>')
            lines.append('   </digiKam:TagsList>')

        lines.append('  </rdf:Description>')
        lines.append(' </rdf:RDF>')
        lines.append('</x:xmpmeta>')
        lines.append("<?xpacket end='w'?>")

        return "\n".join(lines)