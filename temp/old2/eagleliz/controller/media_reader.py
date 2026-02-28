import json
from pathlib import Path
from typing import Generator, Optional
import typer

from temp.old2.eagleliz.core.metadata import Metadata


class EagleMedia:
    def __init__(self, media_path: Path, metadata: Metadata):
        self.media_path = media_path
        self.metadata = metadata


class EagleMediaReader:
    def __init__(self, catalogue: Path):
        self.catalogue = catalogue

    def run(self) -> Generator[EagleMedia, None, None]:
        images_dir = self.catalogue / "images"
        
        if not images_dir.exists():
            typer.secho(f"Directory not found: {images_dir}", fg=typer.colors.RED)
            return

        for folder in images_dir.iterdir():
            if folder.is_dir():
                typer.secho(f"Processing folder: {folder}", fg=typer.colors.CYAN)
                result = self.__handle_eagle_folder(folder)
                if result:
                    yield result

    def __handle_eagle_folder(self, folder: Path) -> Optional[EagleMedia]:
        metadata_obj = None
        media_file = None

        for file_path in folder.iterdir():
            if not file_path.is_file():
                continue
                
            if "_thumbnail" in file_path.name:
                continue
                
            if file_path.name == "metadata.json":
                try:
                    with file_path.open('r', encoding='utf-8') as f:
                        data = json.load(f)
                        metadata_obj = Metadata.from_json(data)
                except Exception as e:
                    typer.secho(f"Error reading metadata from {file_path}: {e}", fg=typer.colors.RED)
            else:
                # Assuming any other file that is not a thumbnail and not metadata.json is the media file
                media_file = file_path
        
        if metadata_obj and media_file:
            return EagleMedia(media_file, metadata_obj)
        return None
