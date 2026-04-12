from typer.testing import CliRunner
from eagleliz.cli import eagleliz_app

runner = CliRunner()


def test_cli_help():
    result = runner.invoke(eagleliz_app, ["--help"])
    assert result.exit_code == 0
    assert "Eagle.cool related utility scripts" in result.output
    # Check if subcommands are listed
    assert "organizer" in result.output
    assert "sidegen" in result.output


def test_cli_no_args():
    result = runner.invoke(eagleliz_app, [])
    # If no command is provided, Typer shows usage
    assert result.exit_code in [0, 2]
    assert "Usage:" in result.output
