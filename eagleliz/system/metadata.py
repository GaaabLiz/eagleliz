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
    id: str
    name: str
    size: int
    btime: int
    mtime: int
    ext: str
    tags: List[str]
    folders: List[str]
    isDeleted: bool
    url: str
    annotation: str
    modificationTime: int
    height: int
    width: int
    noThumbnail: Optional[bool] = False
    lastModified: int
    palettes: List[Palette]
    deletedTime: int

    @classmethod
    def from_json(cls,  dict) -> "Metadata":
        return cls(**dict)

    def to_xmp(self) -> str:
        lines = [
            '<x:xmpmeta xmlns:x="adobe:ns:meta/" x:xmptk="XMP Core 5.6.0">',
            ' <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">',
            '  <rdf:Description rdf:about=""',
            '    xmlns:dc="http://purl.org/dc/elements/1.1/">'
        ]

        if self.annotation:
            safe_desc = escape(self.annotation)
            lines.append('   <dc:description>')
            lines.append('    <rdf:Alt>')
            lines.append(f'     <rdf:li xml:lang="x-default">{safe_desc}</rdf:li>')
            lines.append('    </rdf:Alt>')
            lines.append('   </dc:description>')

        if self.tags:
            lines.append('   <dc:subject>')
            lines.append('    <rdf:Bag>')
            for tag in self.tags:
                safe_tag = escape(tag)
                lines.append(f'     <rdf:li>{safe_tag}</rdf:li>')
            lines.append('    </rdf:Bag>')
            lines.append('   </dc:subject>')

        lines.append('  </rdf:Description>')
        lines.append(' </rdf:RDF>')
        lines.append('</x:xmpmeta>')

        return "\n".join(lines)