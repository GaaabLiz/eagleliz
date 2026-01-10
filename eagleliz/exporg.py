import json
from pathlib import Path
import typer

from eagleliz.core.metadata import Metadata


class ExportOrganizedWorkflow:
    
    def __init__(self, catalogue: Path, output_path: Path, tag: str, xmp: bool):
        self.catalogue = catalogue
        self.output_path = output_path
        self.tag = tag
        self.xmp = xmp
    
    def run(self):
        images_dir = self.catalogue / "images"
        
        if not images_dir.exists():
            typer.secho(f"Directory not found: {images_dir}", fg=typer.colors.RED)
            return

        for folder in images_dir.iterdir():
            if folder.is_dir():
                typer.secho(f"Processing folder: {folder}", fg=typer.colors.CYAN)
                self.__handle_eagle_folder(folder)


    def __handle_eagle_folder(self, folder: Path):
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
            # Placeholder for further instructions
            typer.echo(f"Found media: {media_file.name}")
            self.__handle_eagle_media(media_file, metadata_obj)


    def __handle_eagle_media(self, media_file: Path, metadata_obj: Metadata):
        if self.tag not in metadata_obj.tags:
            typer.secho(f"Skipping {media_file.name}: Tag '{self.tag}' not found.", fg=typer.colors.YELLOW)
            return
        
        # Tag found, waiting for further instructions
        pass
