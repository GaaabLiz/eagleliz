import json
from pathlib import Path
from typing import List

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
    noThumbnail: bool
    lastModified: int
    palettes: List[Palette]
    deletedTime: int

    @classmethod
    def from_json(cls,  dict) -> "Metadata":
        return cls(**dict)