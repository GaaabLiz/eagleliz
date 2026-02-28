import typer

eagleliz_app = typer.Typer(help="Eagle.cool related utility scripts.")


@eagleliz_app.callback()
def callback():
    """
    Eagle.cool related utility scripts.
    """
    pass
