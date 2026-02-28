import json
from pathlib import Path
from typing import List, Optional
from xml.sax.saxutils import escape

from pydantic import BaseModel


def get_tags_from_metadata(metadata: Path) -> list[str]:
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
    color: List[int]
    ratio: float


class Metadata(BaseModel):
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
        return cls(**dict)

    def to_xmp(self) -> str:
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