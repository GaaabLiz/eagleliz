"""
EagleLiz: Eagle.cool related utility scripts and API bindings.

This module initializes the main Typer application for the EagleLiz 
CLI and provides the root command callback.
"""
import typer

eagleliz_app = typer.Typer(help="Eagle.cool related utility scripts.")


@eagleliz_app.callback()
def callback():
    """
    Main entry point for Eagle.cool related utility scripts.
    
    This callback serves as the root command for the CLI. It provides 
    the top-level help text and acts as a grouping for all subcommands.
    """
    pass
