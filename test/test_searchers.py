import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
from eagleliz.local.searcher_eagle import EagleCatalogSearcher
from eagleliz.local.searcher_os import FileSystemSearcher
from conftest import TEST_CATALOG_PATH


def test_eagle_catalog_searcher_basic():
    if not TEST_CATALOG_PATH.exists():
        pytest.skip("TestCatalog.library not found")

    searcher = EagleCatalogSearcher(str(TEST_CATALOG_PATH))
    searcher.search()

    result = searcher.get_result()
    assert len(result.accepted) > 0
    for item in result.accepted:
        assert item.media is not None
        assert item.media.eagle_metadata is not None


def test_eagle_catalog_searcher_with_tags():
    if not TEST_CATALOG_PATH.exists():
        pytest.skip("TestCatalog.library not found")

    searcher = EagleCatalogSearcher(str(TEST_CATALOG_PATH))
    # Using tag we know exists from previous inspection
    searcher.search(eagletag=["BatchURL"])

    result = searcher.get_result()
    assert len(result.accepted) > 0
    for item in result.accepted:
        assert "BatchURL" in item.media.eagle_metadata.tags


def test_filesystem_searcher_basic():
    with TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        # Create some dummy media files
        (tmp_path / "test1.jpg").write_bytes(b"jpg content")
        (tmp_path / "test2.png").write_bytes(b"png content")
        (tmp_path / "not_media.txt").write_bytes(b"not media")

        searcher = FileSystemSearcher(tmp_dir)
        result = searcher.search()

        # LizMedia usually validates by extension, so txt might be skipped
        assert len(result.accepted) == 2
        names = [item.path.name for item in result.accepted]
        assert "test1.jpg" in names
        assert "test2.png" in names


def test_filesystem_searcher_exclude():
    with TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        (tmp_path / "test1.jpg").write_bytes(b"1")
        (tmp_path / "exclude_me.jpg").write_bytes(b"2")

        searcher = FileSystemSearcher(tmp_dir)
        result = searcher.search(exclude="exclude_me")

        assert len(result.accepted) == 1
        assert len(result.rejected) == 1
        assert result.accepted[0].path.name == "test1.jpg"
        assert result.rejected[0].path.name == "exclude_me.jpg"
