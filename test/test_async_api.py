import asyncio
import inspect
import os
import tempfile
import uuid

from conftest import verify_item_in_catalog
from eagleliz.api.eagleapi import EagleAPI, EagleFolder as LegacyEagleFolder
from eagleliz.api.eagleapi_async import AsyncEagleAPI
from eagleliz.model.api import ApplicationInfo, EagleFolder, EagleItem, LibraryInfo


def _build_async_client(sync_client: EagleAPI) -> AsyncEagleAPI:
    raw_url = sync_client.base_url
    if sync_client.token:
        raw_url = f"{raw_url}?token={sync_client.token}"
    return AsyncEagleAPI.from_url(raw_url)


def test_models_live_in_dedicated_module_and_are_reexported():
    assert ApplicationInfo.__module__ == "eagleliz.model.api"
    assert EagleFolder.__module__ == "eagleliz.model.api"
    assert EagleItem.__module__ == "eagleliz.model.api"
    assert LibraryInfo.__module__ == "eagleliz.model.api"
    assert LegacyEagleFolder is EagleFolder


def test_async_client_exposes_sync_public_api_surface():
    sync_methods = {
        name
        for name, member in inspect.getmembers(EagleAPI)
        if callable(member) and not name.startswith("_")
    }
    async_methods = {
        name
        for name, member in inspect.getmembers(AsyncEagleAPI)
        if callable(member) and not name.startswith("_")
    }
    assert sync_methods <= async_methods


def test_async_read_endpoints(api):
    async def scenario():
        client = _build_async_client(api)

        app_info = await client.get_application_info()
        assert isinstance(app_info, ApplicationInfo)
        assert app_info.version

        library_info = await client.get_library_info()
        assert isinstance(library_info, LibraryInfo)
        assert isinstance(library_info.folders, list)

        history = await client.get_library_history()
        assert isinstance(history, list)
        assert history

        icon_bytes = await client.get_library_icon(history[0])
        assert isinstance(icon_bytes, bytes)
        assert icon_bytes

        folders = await client.list_folders()
        assert isinstance(folders, list)

    asyncio.run(scenario())


def test_async_folder_and_item_lifecycle(api):
    async def scenario():
        client = _build_async_client(api)
        folder_name = f"AsyncFolder_{uuid.uuid4().hex[:6]}"
        folder = await client.create_folder(folder_name)
        assert isinstance(folder, EagleFolder)
        assert folder.name == folder_name

        renamed = await client.rename_folder(folder.id, f"{folder_name}_renamed")
        assert renamed.id == folder.id

        updated_folder = await client.update_folder(folder.id, new_description="async test folder", new_color="blue")
        assert updated_folder.id == folder.id

        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as handle:
            handle.write(b"async-eagle-test")
            temp_path = handle.name

        item_name = f"AsyncItem_{uuid.uuid4().hex[:6]}"
        try:
            added = await client.add_item_from_path(
                path=temp_path,
                name=item_name,
                tags=["AsyncAPI"],
                annotation="Created from async test",
                folder_id=folder.id,
            )
            assert added is True

            await asyncio.sleep(1)
            items = await client.get_items(keyword=item_name, limit=1, folders=[folder.id])
            assert len(items) == 1

            item = items[0]
            verify_item_in_catalog(item.id, item.ext)

            item_info = await client.get_item_info(item.id)
            assert item_info.id == item.id

            updated_item = await client.update_item(
                item.id,
                tags=["AsyncAPI", "Updated"],
                annotation="Updated asynchronously",
                star=2,
            )
            assert updated_item.star == 2
            assert "Updated" in updated_item.tags

            assert await client.refresh_item_thumbnail(item.id) is True
            assert await client.refresh_item_palette(item.id) is True

            thumbnail_path = await client.get_item_thumbnail(item.id)
            assert isinstance(thumbnail_path, str)
            assert thumbnail_path

            assert await client.move_to_trash([item.id]) is True
            await asyncio.sleep(0.5)
            trashed_item = await client.get_item_info(item.id)
            assert trashed_item.isDeleted is True
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    asyncio.run(scenario())


