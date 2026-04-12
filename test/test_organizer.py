import pytest
from typer.testing import CliRunner
from pathlib import Path
from tempfile import TemporaryDirectory
from eagleliz.cli import eagleliz_app
from conftest import TEST_CATALOG_PATH

runner = CliRunner()


def test_organizer_dry_run_system():
    with TemporaryDirectory() as src_dir, TemporaryDirectory() as dst_dir:
        src_path = Path(src_dir)
        (src_path / "test.jpg").write_bytes(b"1")

        # We need to simulate the "Enter" press
        result = runner.invoke(
            eagleliz_app, ["organizer", src_dir, dst_dir, "--dry"], input="\n"
        )

        assert result.exit_code == 0
        assert "Source:" in result.output
        assert "Dry-run: Yes" in result.output
        assert "Organization Results" in result.output


def test_organizer_eagle_catalog_dry():
    if not TEST_CATALOG_PATH.exists():
        pytest.skip("TestCatalog.library not found")

    with TemporaryDirectory() as dst_dir:
        result = runner.invoke(
            eagleliz_app,
            ["organizer", str(TEST_CATALOG_PATH), dst_dir, "--eaglecatalog", "--dry"],
            input="\n",
        )

        assert result.exit_code == 0
        assert "Eagle Catalog: Yes" in result.output
        assert "Filename" in result.output


def test_organizer_missing_args():
    result = runner.invoke(eagleliz_app, ["organizer"])
    assert result.exit_code != 0


def test_organizer_exclude_dry():
    with TemporaryDirectory() as src_dir, TemporaryDirectory() as dst_dir:
        src_path = Path(src_dir)
        (src_path / "keep.jpg").write_bytes(b"1")
        (src_path / "exclude_me.jpg").write_bytes(b"2")

        result = runner.invoke(
            eagleliz_app,
            ["organizer", src_dir, dst_dir, "--dry", "--exclude", "exclude_me"],
            input="\n",
        )

        assert result.exit_code == 0
        # Check that only 1 file is accepted (it prints a table, so we check for the filename)
        assert "keep.jpg" in result.output
        # exclude_me.jpg should be in the rejected table
        assert "exclude_me.jpg" in result.output


def test_organizer_with_tags_dry():
    if not TEST_CATALOG_PATH.exists():
        pytest.skip("TestCatalog.library not found")

    with TemporaryDirectory() as dst_dir:
        result = runner.invoke(
            eagleliz_app,
            [
                "organizer",
                str(TEST_CATALOG_PATH),
                dst_dir,
                "--eaglecatalog",
                "--dry",
                "--eagletag",
                "BatchURL",
            ],
            input="\n",
        )

        assert result.exit_code == 0
        assert "Eagle Tags: BatchURL" in result.output
