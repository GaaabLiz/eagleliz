import pytest
import time
from pathlib import Path
from eagleliz.api.eagleapi import EagleAPI, EagleAPIError
from eagleliz.model.api import EagleItemURLPayload

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
        pytest.fail(
            f"Eagle API is unreachable. Tests require Eagle.cool to be running with TestCatalog.library. Error: {e}"
        )

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


@pytest.fixture(scope="session")
def dynamic_test_items(api, test_root_folder):
    """
    Downloads random images from picsum.photos and adds them to Eagle.
    Cleans them up after tests.
    """
    num_items = 5
    items_to_add = []
    for i in range(num_items):
        items_to_add.append(
            EagleItemURLPayload(
                url=f"https://picsum.photos/seed/{int(time.time()) + i}/800/600.jpg",
                name=f"Dynamic_Test_Image_{i}",
                tags=["DynamicTest"],
            )
        )

    # Upload to Eagle
    api.add_items_from_urls(items_to_add, folder_id=test_root_folder.id)

    # Wait for items to appear in Eagle (metadata sync)
    if not wait_for_items(
        api, folders=[test_root_folder.id], expected_count=num_items, timeout=30
    ):
        pytest.fail("Timeout waiting for dynamic test items to appear in Eagle.")

    # Get the actual items with their IDs
    created_items = api.get_items(folders=[test_root_folder.id], limit=num_items)

    # Now we need to wait for the files to actually exist on disk in the library
    # because the Searcher/Reader read directly from the filesystem.
    for item in created_items:

        def check_file():
            img_dir = TEST_CATALOG_PATH / "images" / f"{item.id}.info"
            if not img_dir.exists():
                return False
            # Check if any non-json/non-ext file exists (the actual image)
            return any(
                f.suffix.lower() in [".jpg", ".png", ".jpeg"]
                for f in img_dir.iterdir()
                if not f.name.endswith(".json")
            )

        if not wait_for_condition(check_file, timeout=20):
            pytest.fail(f"Timeout waiting for item {item.id} to appear on disk.")

    yield created_items

    # Cleanup is handled by test_root_folder (it moves everything to trash)


def verify_item_in_catalog(item_id, expected_ext):
    """
    Helper to verify an item physically exists in TestCatalog.library/images/{id}.info/{id}.{ext}
    """
    if not TEST_CATALOG_PATH.exists():
        pytest.skip(
            f"TestCatalog.library not found at {TEST_CATALOG_PATH}. Skipping filesystem verification."
        )

    img_dir = TEST_CATALOG_PATH / "images" / f"{item_id}.info"
    assert img_dir.exists() and img_dir.is_dir(), (
        f"Item directory not found in catalog: {img_dir}"
    )

    # The actual file
    ext_lower = expected_ext.lower()
    matching_files = [
        f
        for f in img_dir.iterdir()
        if f.is_file()
        and f.suffix.lower() == f".{ext_lower}"
        and not f.name.endswith("_thumbnail.png")
    ]
    assert len(matching_files) > 0, (
        f"No file with extension {expected_ext} found in {img_dir}"
    )


def wait_for_condition(condition_func, timeout=15, interval=0.5):
    """
    Polls a condition function until it returns True or timeout is reached.
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        if condition_func():
            return True
        time.sleep(interval)
    return False


def wait_for_items(
    api, keyword=None, tags=None, folders=None, expected_count=1, timeout=15
):
    """
    Waits for a specific number of items to appear in Eagle.
    """

    def check():
        items = api.get_items(
            keyword=keyword, tags=tags, folders=folders, limit=max(expected_count, 10)
        )
        return len(items) >= expected_count

    return wait_for_condition(check, timeout=timeout)
