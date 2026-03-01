import pytest
import time
from eagleliz.api.eaglelizapi import EagleAPI, EagleAPIError
from conftest import verify_item_in_catalog

class TestAppAPI:
    def test_get_application_info(self, api):
        info = api.get_application_info()
        assert info.version is not None
        assert info.platform in ["darwin", "win32", "linux"]
        assert hasattr(info, "execPath")
        # buildVersion might be None in some Eagle releases, just ensure it's a known attribute
        assert hasattr(info, "buildVersion")

class TestLibraryAPI:
    def test_get_library_info(self, api):
        info = api.get_library_info()
        assert info.applicationVersion is not None
        assert isinstance(info.folders, list)
        assert isinstance(info.smartFolders, list)
        assert isinstance(info.quickAccess, list)
        assert isinstance(info.tagsGroups, list)
        assert isinstance(info.modificationTime, int)

    def test_get_library_history(self, api):
        history = api.get_library_history()
        assert isinstance(history, list)
        # Assuming TestCatalog.library is currently open, history should not be empty
        assert len(history) > 0
        assert isinstance(history[0], str)

    def test_get_library_icon(self, api):
        history = api.get_library_history()
        if not history:
            pytest.skip("No library history to extract current path from.")
            
        current_library = history[0]
        icon_bytes = api.get_library_icon(current_library)
        assert isinstance(icon_bytes, bytes)
        assert len(icon_bytes) > 0

    def test_switch_library_is_ignored(self, api):
        # We intentionally do not test switch_library per the user's instructions.
        pass
