import pytest
import os
import time
from pathlib import Path
from eagleliz.api.eaglelizapi import EagleAPI, EagleAPIError

# Use the catalog provided by the user in the root directory
TEST_CATALOG_PATH = Path(__file__).parent.parent / "TestCatalog.library"

@pytest.fixture(scope="session")
def api():
    """Provides a global EagleAPI client instance for all tests."""
    client = EagleAPI()
    
    # Optional: Verify Eagle is reachable before running suite
    try:
        client.get_application_info()
    except EagleAPIError as e:
        pytest.fail(f"Eagle API is unreachable. Tests require Eagle.cool to be running with TestCatalog.library. Error: {e}")
        
    return client

@pytest.fixture(scope="session")
def test_root_folder(api):
    """Creates a dedicated root folder for all tests and cleans it up after."""
    folder_name = f"Pytest_Root_{int(time.time())}"
    folder = api.create_folder(folder_name)
    yield folder
    
    # Teardown: Trash the entire test folder and its contents
    # Eagle API doesn't have an explicit 'trash folder' endpoint, but we can list items inside
    # and trash them, then maybe we leave the folder. Let's just trash all items inside it.
    items = api.get_items(limit=10000, folders=[folder.id])
    if items:
        api.move_to_trash(item_ids=[item.id for item in items])

def verify_item_in_catalog(item_id, expected_ext):
    """
    Helper to verify an item physically exists in TestCatalog.library/images/{id}.info/{id}.{ext}
    """
    if not TEST_CATALOG_PATH.exists():
        pytest.skip(f"TestCatalog.library not found at {TEST_CATALOG_PATH}. Skipping filesystem verification.")
        
    img_dir = TEST_CATALOG_PATH / "images" / f"{item_id}.info"
    assert img_dir.exists() and img_dir.is_dir(), f"Item directory not found in catalog: {img_dir}"
    
    # The actual file
    ext_lower = expected_ext.lower()
    matching_files = [f for f in img_dir.iterdir() if f.is_file() and f.suffix.lower() == f".{ext_lower}" and not f.name.endswith('_thumbnail.png')]
    assert len(matching_files) > 0, f"No file with extension {expected_ext} found in {img_dir}"
