import pytest
from typer.testing import CliRunner
from eagleliz.cli import eagleliz_app
from conftest import TEST_CATALOG_PATH

runner = CliRunner()


def test_sidegen_dry_run():
    if not TEST_CATALOG_PATH.exists():
        pytest.skip("TestCatalog.library not found")

    result = runner.invoke(eagleliz_app, ["sidegen", str(TEST_CATALOG_PATH), "--dry"])
    assert result.exit_code == 0
    assert "Dry-run complete" in result.output
    assert "Found" in result.output


def test_sidegen_missing_path():
    result = runner.invoke(eagleliz_app, ["sidegen"])
    # result.exit_code 2 is for missing arguments in Typer
    assert result.exit_code != 0


def test_sidegen_invalid_path():
    result = runner.invoke(eagleliz_app, ["sidegen", "/non/existent/path"])
    assert result.exit_code == 1
    assert "Error: path '/non/existent/path' does not exist" in result.output


@pytest.mark.parametrize("tags", [["BatchURL"], ["NonExistentTag"]])
def test_sidegen_with_tags_dry(tags):
    if not TEST_CATALOG_PATH.exists():
        pytest.skip("TestCatalog.library not found")

    args = ["sidegen", str(TEST_CATALOG_PATH), "--dry"]
    for tag in tags:
        args.extend(["--eagletag", tag])

    result = runner.invoke(eagleliz_app, args)
    assert result.exit_code == 0
    if tags == ["NonExistentTag"]:
        assert "No media files found" in result.output
    else:
        assert "Found" in result.output
