import pytest
import uuid
import tempfile
import os
import time
from pathlib import Path
from eagleliz.api.eaglelizapi import EagleItemURLPayload, EagleItemPathPayload, EagleAPIError
from conftest import verify_item_in_catalog

class TestItemAPI:

    @pytest.fixture(autouse=True)
    def setup_sandbox(self, api):
        # Creates a dedicated folder for all items in a test module
        folder_name = f"Pytest_ItemSandbox_{int(time.time())}"
        self.sandbox = api.create_folder(folder_name)
        yield
        
        # We try to trash all items in sandbox by grabbing list and passing to trash
        try:
            items = api.get_items(limit=1000, folders=[self.sandbox.id])
            if items:
                api.move_to_trash([item.id for item in items])
        except Exception as e:
            print(f"Warning: Teardown trash failed: {e}")

    # ==========================
    # URL Additions
    # ==========================
    def test_add_item_from_url_minimal(self, api):
        # Let's use a very reliable small URL
        url = "https://raw.githubusercontent.com/pytest-dev/pytest/main/doc/en/img/pytest_logo_curves.svg"
        name = f"Minimal_SVG_{uuid.uuid4().hex[:4]}"
        
        success = api.add_item_from_url(url=url, name=name, folderId=self.sandbox.id)
        assert success is True
        
        # Verify it exists by fetching it right away
        time.sleep(1) # Give Eagle a sec to digest
        items = api.get_items(keyword=name, limit=1)
        assert len(items) == 1
        assert items[0].name == name
        verify_item_in_catalog(items[0].id, items[0].ext)

    def test_add_item_from_url_comprehensive(self, api):
        url = "https://picsum.photos/id/237/200/300"
        name = f"Comprehensive_URL_{uuid.uuid4().hex[:4]}"
        success = api.add_item_from_url(
            url=url,
            name=name,
            website="https://picsum.photos",
            tags=["TestDog", "Comprehensive"],
            star=4,
            annotation="A good dog.",
            modificationTime=int(time.time() * 1000),
            folderId=self.sandbox.id,
            headers={"User-Agent": "Pytest/1.0"}
        )
        assert success is True
        time.sleep(1)
        items = api.get_items(keyword=name, limit=1)
        assert len(items) == 1
        item = items[0]
        assert "TestDog" in item.tags
        assert item.star == 4
        assert item.annotation == "A good dog."
        assert item.url == "https://picsum.photos"
        verify_item_in_catalog(item.id, item.ext)

    def test_add_items_from_urls_batch(self, api):
        item1 = EagleItemURLPayload(
            url="https://picsum.photos/id/1/100",
            name="Batch_1",
            tags=["BatchURL"]
        )
        item2 = EagleItemURLPayload(
            url="https://picsum.photos/id/2/100",
            name="Batch_2",
            tags=["BatchURL"]
        )
        success = api.add_items_from_urls([item1, item2], folder_id=self.sandbox.id)
        assert success is True
        time.sleep(1.5)
        
        items = api.get_items(tags=["BatchURL"], limit=10, folders=[self.sandbox.id])
        assert len(items) == 2
        for i in items:
            verify_item_in_catalog(i.id, i.ext)

    # ==========================
    # Path Additions
    # ==========================
    @pytest.mark.parametrize("ext,content", [
        (".txt", b"Hello Eagle"),
        (".md", b"# Markdown Test"),
    ])
    def test_add_item_from_path(self, api, ext, content):
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name
            
        name = f"PathItem_{ext.strip('.')}"
        try:
            success = api.add_item_from_path(
                path=tmp_path,
                name=name,
                tags=["LocalPath"],
                annotation=f"Imported from {tmp_path}",
                folder_id=self.sandbox.id
            )
            assert success is True
            time.sleep(0.5)
            items = api.get_items(keyword=name, limit=1, folders=[self.sandbox.id])
            assert len(items) == 1
            verify_item_in_catalog(items[0].id, items[0].ext)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_add_items_from_paths_batch(self, api):
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as t1, \
             tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as t2:
            t1.write(b"1")
            t2.write(b"2")
            p1 = t1.name
            p2 = t2.name
            
        try:
            pl1 = EagleItemPathPayload(path=p1, name="BatchPath1", tags=["BPath"])
            pl2 = EagleItemPathPayload(path=p2, name="BatchPath2", tags=["BPath"])
            success = api.add_items_from_paths([pl1, pl2], folder_id=self.sandbox.id)
            assert success is True
            time.sleep(1)
            items = api.get_items(tags=["BPath"], limit=10, folders=[self.sandbox.id])
            assert len(items) == 2
        finally:
            if os.path.exists(p1): os.remove(p1)
            if os.path.exists(p2): os.remove(p2)

    # ==========================
    # Bookmark Addition
    # ==========================
    def test_add_bookmark(self, api):
        name = f"Bookmark_{uuid.uuid4().hex[:4]}"
        dummy_base64_png = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
        bm_tag = f"BM_{uuid.uuid4().hex[:4]}"
    
        success = api.add_bookmark(
            url="https://pytest.org",
            name=name,
            base64=dummy_base64_png,
            tags=[bm_tag]
        )
        assert success is True
        time.sleep(2) # Give OS a moment to sync file
        
        # Verify directly from OS since Eagle API indexing for bookmarks is asynchronous
        from conftest import TEST_CATALOG_PATH
        if not TEST_CATALOG_PATH.exists():
            pytest.skip("No TestCatalog.library to verify bookmark against.")
            
        # Search for Name within the images directory
        images_dir = TEST_CATALOG_PATH / "images"
        found = False
        for info_dir in images_dir.iterdir():
            if info_dir.is_dir() and info_dir.name.endswith(".info"):
                url_file = info_dir / f"{name}.url"
                if url_file.exists():
                    found = True
                    break
                    
        assert found is True, f"Bookmark file {name}.url not found in local catalog filesystem"

    # ==========================
    # Get/Update/Refresh
    # ==========================
    def test_get_update_refresh_cycle(self, api):
        # 1. Add item
        url = "https://picsum.photos/id/55/100"
        name = f"CycleItem"
        api.add_item_from_url(url=url, name=name, folderId=self.sandbox.id)
        time.sleep(1.5)
        items = api.get_items(keyword=name, limit=1, folders=[self.sandbox.id])
        assert len(items) == 1
        item_id = items[0].id
        
        # 2. Get Info
        info = api.get_item_info(item_id)
        assert info.id == item_id
        assert info.name == name
        
        # 3. Update Item properties
        updated = api.update_item(
            item_id=item_id,
            tags=["UpdatedCycle"],
            annotation="Updated Note",
            star=3
        )
        assert updated.star == 3
        assert "UpdatedCycle" in updated.tags
        assert updated.annotation == "Updated Note"
        
        # 4. Refresh Thumbnail & Palette
        assert api.refresh_item_thumbnail(item_id) is True
        assert api.refresh_item_palette(item_id) is True
        
        # 5. Get Thumbnail Path
        thumb_path = api.get_item_thumbnail(item_id)
        assert isinstance(thumb_path, str)
        assert thumb_path.endswith(".jpg") or thumb_path.endswith(".png")

    # ==========================
    # Extraparameterized Get Items
    # ==========================
    @pytest.mark.parametrize("order_by", ["NAME", "-NAME", "FILESIZE", "-FILESIZE", "CREATEDATE", "-CREATEDATE"])
    def test_get_items_ordering(self, api, order_by):
        # Create a few items so we can sort them, wait, we don't need to create them, they'll pull from entire catalog.
        # But we limit to 5 to make it fast
        items = api.get_items(limit=3, order_by=order_by)
        assert isinstance(items, list)
        
    @pytest.mark.parametrize("limit,offset", [(1, 0), (2, 1), (5, 5)])
    def test_get_items_pagination(self, api, limit, offset):
        items = api.get_items(limit=limit, offset=offset)
        assert len(items) <= limit

    def test_get_items_invalid_keyword(self, api):
        items = api.get_items(keyword="IMPOSSIBLE_KEYWORD_THAT_DOES_NOT_EXIST_XYZ123")
        assert len(items) == 0

    # ==========================
    # Trash
    # ==========================
    def test_move_to_trash(self, api):
        api.add_item_from_url("https://picsum.photos/id/66/10", name="TrashMe", folderId=self.sandbox.id)
        time.sleep(1)
        items = api.get_items(keyword="TrashMe", limit=1, folders=[self.sandbox.id])
        assert len(items) == 1
        item_id = items[0].id
        
        success = api.move_to_trash([item_id])
        assert success is True
        
        # Verify it's in trash (isDeleted = True)
        info = api.get_item_info(item_id)
        assert info.isDeleted is True

    # ==========================
    # Negative Scenarios
    # ==========================
    def test_get_item_invalid_id(self, api):
        with pytest.raises(EagleAPIError):
            api.get_item_info("INVALID_ID")
            
    def test_update_item_invalid_id(self, api):
        with pytest.raises(EagleAPIError):
            api.update_item("INVALID_ID", star=5)
