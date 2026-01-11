from pathlib import Path
import typer

from eagleliz.controller.media_reader import EagleMediaReader, EagleMedia
from eagleliz.core.metadata import Metadata


class ExportOrganizedWorkflow:
    
    def __init__(self, catalogue: Path, output_path: Path, tag: str, xmp: bool):
        self.catalogue = catalogue
        self.output_path = output_path
        self.tag = tag
        self.xmp = xmp
    
    def run(self):
        reader = EagleMediaReader(self.catalogue)
        for eagle_media in reader.run():
            self.__handle_eagle_media(eagle_media)

    def __handle_eagle_media(self, eagle_media: EagleMedia):
        media_file = eagle_media.media_path
        metadata_obj = eagle_media.metadata

        if self.tag not in metadata_obj.tags:
            typer.secho(f"Skipping {media_file.name}: Tag '{self.tag}' not found.", fg=typer.colors.YELLOW)
            return
        
        typer.echo(f"Found media: {media_file.name}")
        # Tag found, waiting for further instructions
        pass
