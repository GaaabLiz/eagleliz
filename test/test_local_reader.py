import pytest
from pathlib import Path
from eagleliz.local.reader import EagleLocalReader
from conftest import TEST_CATALOG_PATH
from pylizlib.core.domain.os import FileType

def test_reader_initialization():
    reader = EagleLocalReader(TEST_CATALOG_PATH)
    assert reader.catalogue == TEST_CATALOG_PATH
    assert reader.include_deleted is False
    assert FileType.IMAGE in reader.file_types

def test_reader_scan_basic():
    if not TEST_CATALOG_PATH.exists():
        pytest.skip("TestCatalog.library not found")
        
    reader = EagleLocalReader(TEST_CATALOG_PATH)
    reader.run()
    
    assert reader.scanned_folders_count > 0
    assert len(reader.items) > 0
    # Every item should have metadata and a file path
    for item in reader.items:
        assert item.metadata is not None
        assert item.file_path.exists()
        assert item.file_path.is_file()

def test_reader_filter_tags():
    if not TEST_CATALOG_PATH.exists():
        pytest.skip("TestCatalog.library not found")
        
    # We saw "BatchURL" tag in the previous check
    reader = EagleLocalReader(TEST_CATALOG_PATH, filter_tags=["BatchURL"])
    reader.run()
    
    assert len(reader.items) > 0
    for item in reader.items:
        assert "BatchURL" in item.metadata.tags


def test_reader_include_deleted():
    if not TEST_CATALOG_PATH.exists():
        pytest.skip("TestCatalog.library not found")
        
    # Scan without deleted
    reader_no_del = EagleLocalReader(TEST_CATALOG_PATH, include_deleted=False)
    reader_no_del.run()
    
    # Scan with deleted
    reader_with_del = EagleLocalReader(TEST_CATALOG_PATH, include_deleted=True)
    reader_with_del.run()
    
    # Normally we'd expect more items with deleted, but it depends on the catalog
    assert len(reader_with_del.items) >= len(reader_no_del.items)

def test_reader_invalid_path():
    with pytest.raises(ValueError):
        reader = EagleLocalReader(Path("/non/existent/path.library"))
        reader.run()

def test_reader_include_base64():
    if not TEST_CATALOG_PATH.exists():
        pytest.skip("TestCatalog.library not found")
        
    reader = EagleLocalReader(TEST_CATALOG_PATH, include_base64=True)
    reader.run()
    
    if reader.items:
        # Check first item for base64
        item = reader.items[0]
        assert item.base64_content is not None
        assert len(item.base64_content) > 0
