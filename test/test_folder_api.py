import pytest
import uuid
import time
from eagleliz.api.eaglelizapi import EagleFolder, EagleAPIError

class TestFolderAPI:
    @pytest.fixture
    def root_folder(self, api):
        folder_name = f"RootFolder_{uuid.uuid4().hex[:6]}"
        f = api.create_folder(folder_name)
        time.sleep(0.5) # Allow Eagle backend to safely commit the OS file write
        yield f
        # Cleanup
        try:
            api.update_folder(f.id, new_name=f"{f.name}_trash")
        except:
            pass

    def test_create_folder_root(self, api):
        name = f"Root_{uuid.uuid4().hex[:6]}"
        f = api.create_folder(name)
        assert isinstance(f, EagleFolder)
        assert f.id is not None
        assert f.name == name

    def test_create_folder_nested(self, api, root_folder):
        child_name = f"Child_{uuid.uuid4().hex[:6]}"
        child = api.create_folder(child_name, parent_id=root_folder.id)
        assert child.name == child_name
        # The returned child might not guarantee parent lookup, but we check name and ID
        assert child.id is not None

    def test_rename_folder(self, api, root_folder):
        new_name = f"Renamed_{uuid.uuid4().hex[:6]}"
        renamed = api.rename_folder(root_folder.id, new_name)
        time.sleep(0.5)
        assert renamed.name == new_name
        assert renamed.id == root_folder.id

    @pytest.mark.parametrize("color", ["red", "orange", "yellow", "green", "aqua", "blue", "purple", "pink"])
    def test_update_folder_colors(self, api, root_folder, color):
        updated = api.update_folder(root_folder.id, new_color=color)
        assert updated.id == root_folder.id

    def test_update_folder_description(self, api, root_folder):
        desc = "This is a Pytest automated description."
        updated = api.update_folder(root_folder.id, new_description=desc)
        # Verify it landed either in defined props or extra_data
        actual_desc = getattr(updated, "description", None) or updated._extra_data.get("description", "")
        assert actual_desc == desc

    def test_update_folder_combined(self, api, root_folder):
        name = "CombinedUpdate"
        desc = "CombinedDesc"
        color = "aqua"
        updated = api.update_folder(root_folder.id, new_name=name, new_description=desc, new_color=color)
        time.sleep(0.5)
        assert updated.name == name
        actual_desc = getattr(updated, "description", None) or updated._extra_data.get("description", "")
        assert actual_desc == desc

    def test_rename_nonexistent_folder_fails(self, api):
        with pytest.raises(EagleAPIError) as exc_info:
            api.rename_folder("fake_folder_id_12345", "ShouldFail")
        assert "error" in str(exc_info.value).lower()

    def test_list_folders(self, api, root_folder):
        folders = api.list_folders()
        assert isinstance(folders, list)
        assert len(folders) > 0
        assert any(f.id == root_folder.id for f in folders)

    def test_list_recent_folders(self, api, root_folder):
        # Trigger recent usage by updating it
        api.update_folder(root_folder.id, new_color="pink")
        recents = api.list_recent_folders()
        assert isinstance(recents, list)
        assert len(recents) > 0
        assert any(f.id == root_folder.id for f in recents)
