"""Asynchronous Python client for the local Eagle.cool API."""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

import httpx

from eagleliz.api._shared import (
    EagleAPIBase,
    EagleAPIError,
    build_get_items_params,
    build_json_payload,
    build_request_url,
    compact_dict,
    mask_token,
    parse_api_response,
    parse_application_info,
    parse_folder_list,
    parse_item_list,
    parse_library_history,
    parse_library_info,
)
from eagleliz.model.api import (
    ApplicationInfo,
    EagleFolder,
    EagleItem,
    EagleItemPathPayload,
    EagleItemURLPayload,
    LibraryInfo,
)

logger = logging.getLogger(__name__)


class AsyncEagleAPI(EagleAPIBase):
    """Asynchronous client for interacting with the local Eagle.cool HTTP API."""

    async def _make_request(
        self,
        endpoint: str,
        *,
        method: str = "GET",
        data: Optional[dict[str, Any]] = None,
        params: Optional[dict[str, Any]] = None,
    ) -> Any:
        """Execute a JSON request against the Eagle API and return the response ``data`` payload."""
        url = build_request_url(self.base_url, endpoint, params=params, token=self.token if method == "GET" else None)
        payload = build_json_payload(data, token=self.token if method == "POST" else None)

        async with httpx.AsyncClient() as client:
            try:
                response = await client.request(method, url, json=payload)
                response.raise_for_status()
                result = response.json()
                return parse_api_response(result, url=mask_token(str(response.url), self.token))
            except httpx.HTTPStatusError as exc:
                log_url = mask_token(str(exc.request.url), self.token)
                logger.error("HTTP error %s for Eagle API at %s. Body: %s", exc.response.status_code, log_url, exc.response.text)
                raise EagleAPIError(f"HTTP {exc.response.status_code} error: {exc.response.text}") from exc
            except httpx.HTTPError as exc:
                logger.error("Request transport failed for Eagle API endpoint %s: %s", endpoint, exc)
                raise EagleAPIError(f"Connection error: {exc}") from exc
            except json.JSONDecodeError as exc:
                log_url = mask_token(url, self.token)
                logger.error("Failed to parse JSON response from Eagle API at %s. Error: %s", log_url, exc)
                raise EagleAPIError(f"JSON parse error: {exc}") from exc

    async def _read_bytes(self, endpoint: str, *, params: Optional[dict[str, Any]] = None) -> bytes:
        """Execute a request that returns raw bytes instead of the JSON envelope."""
        url = build_request_url(self.base_url, endpoint, params=params, token=self.token)

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url)
                response.raise_for_status()
                return response.content
            except httpx.HTTPStatusError as exc:
                log_url = mask_token(str(exc.request.url), self.token)
                logger.error("HTTP error %s fetching Eagle binary response at %s. Body: %s", exc.response.status_code, log_url, exc.response.text)
                raise EagleAPIError(f"HTTP {exc.response.status_code} error: {exc.response.text}") from exc
            except httpx.HTTPError as exc:
                logger.error("Request transport failed for Eagle API binary endpoint %s: %s", endpoint, exc)
                raise EagleAPIError(f"Connection error: {exc}") from exc

    async def get_application_info(self) -> ApplicationInfo:
        """Return information about the running Eagle application instance."""
        data = await self._make_request("/application/info")
        return parse_application_info(data)

    async def get_library_info(self) -> LibraryInfo:
        """Return metadata for the currently opened Eagle library."""
        data = await self._make_request("/library/info")
        return parse_library_info(data)

    async def get_library_history(self) -> list[str]:
        """Return the list of recently opened Eagle library paths."""
        data = await self._make_request("/library/history")
        return parse_library_history(data)

    async def switch_library(self, library_path: str) -> bool:
        """Switch Eagle to another library path."""
        await self._make_request("/library/switch", method="POST", data={"libraryPath": library_path})
        return True

    async def get_library_icon(self, library_path: str) -> bytes:
        """Return the binary icon content for a library path."""
        return await self._read_bytes("/library/icon", params={"libraryPath": library_path})

    async def create_folder(self, folder_name: str, parent_id: Optional[str] = None) -> EagleFolder:
        """Create a folder in the currently opened Eagle library."""
        payload = compact_dict({"folderName": folder_name, "parent": parent_id})
        data = await self._make_request("/folder/create", method="POST", data=payload)
        return EagleFolder.from_dict(data)

    async def rename_folder(self, folder_id: str, new_name: str) -> EagleFolder:
        """Rename an existing Eagle folder."""
        data = await self._make_request(
            "/folder/rename",
            method="POST",
            data={"folderId": folder_id, "newName": new_name},
        )
        return EagleFolder.from_dict(data)

    async def update_folder(
        self,
        folder_id: str,
        new_name: Optional[str] = None,
        new_description: Optional[str] = None,
        new_color: Optional[str] = None,
    ) -> EagleFolder:
        """Update the name, description, or color of an Eagle folder."""
        payload = compact_dict(
            {
                "folderId": folder_id,
                "newName": new_name,
                "newDescription": new_description,
                "newColor": new_color,
            }
        )
        data = await self._make_request("/folder/update", method="POST", data=payload)
        return EagleFolder.from_dict(data)

    async def list_folders(self) -> list[EagleFolder]:
        """Return the root folders of the current Eagle library."""
        data = await self._make_request("/folder/list")
        return parse_folder_list(data)

    async def list_recent_folders(self) -> list[EagleFolder]:
        """Return folders recently used by the user in Eagle."""
        data = await self._make_request("/folder/listRecent")
        return parse_folder_list(data)

    async def add_item_from_url(
        self,
        url: str,
        name: str,
        website: Optional[str] = None,
        tags: Optional[list[str]] = None,
        star: Optional[int] = None,
        annotation: Optional[str] = None,
        modificationTime: Optional[int] = None,
        folderId: Optional[str] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> bool:
        """Import a remote asset into Eagle from a URL or base64 source."""
        payload = compact_dict(
            {
                "url": url,
                "name": name,
                "website": website,
                "tags": tags,
                "star": star,
                "annotation": annotation,
                "modificationTime": modificationTime,
                "folderId": folderId,
                "headers": headers,
            }
        )
        await self._make_request("/item/addFromURL", method="POST", data=payload)
        return True

    async def add_items_from_urls(self, items: list[EagleItemURLPayload], folder_id: Optional[str] = None) -> bool:
        """Import multiple remote assets into Eagle in a single request."""
        payload: dict[str, Any] = {"items": [item.to_dict() for item in items]}
        if folder_id is not None:
            payload["folderId"] = folder_id
        await self._make_request("/item/addFromURLs", method="POST", data=payload)
        return True

    async def add_item_from_path(
        self,
        path: str,
        name: str,
        website: Optional[str] = None,
        tags: Optional[list[str]] = None,
        annotation: Optional[str] = None,
        folder_id: Optional[str] = None,
    ) -> bool:
        """Import a local file into the current Eagle library."""
        payload = compact_dict(
            {
                "path": path,
                "name": name,
                "website": website,
                "tags": tags,
                "annotation": annotation,
                "folderId": folder_id,
            }
        )
        await self._make_request("/item/addFromPath", method="POST", data=payload)
        return True

    async def add_items_from_paths(self, items: list[EagleItemPathPayload], folder_id: Optional[str] = None) -> bool:
        """Import multiple local files into Eagle in a single request."""
        payload: dict[str, Any] = {"items": [item.to_dict() for item in items]}
        if folder_id is not None:
            payload["folderId"] = folder_id
        await self._make_request("/item/addFromPaths", method="POST", data=payload)
        return True

    async def add_bookmark(
        self,
        url: str,
        name: str,
        base64: Optional[str] = None,
        tags: Optional[list[str]] = None,
        modificationTime: Optional[int] = None,
        folder_id: Optional[str] = None,
    ) -> bool:
        """Save a bookmark entry into Eagle."""
        payload = compact_dict(
            {
                "url": url,
                "name": name,
                "base64": base64,
                "tags": tags,
                "modificationTime": modificationTime,
                "folderId": folder_id,
            }
        )
        await self._make_request("/item/addBookmark", method="POST", data=payload)
        return True

    async def move_to_trash(self, item_ids: list[str]) -> bool:
        """Move one or more Eagle items to the trash."""
        await self._make_request("/item/moveToTrash", method="POST", data={"itemIds": item_ids})
        return True

    async def update_item(
        self,
        item_id: str,
        tags: Optional[list[str]] = None,
        annotation: Optional[str] = None,
        url: Optional[str] = None,
        star: Optional[int] = None,
    ) -> EagleItem:
        """Update mutable metadata fields on an existing Eagle item."""
        payload = compact_dict(
            {
                "id": item_id,
                "tags": tags,
                "annotation": annotation,
                "url": url,
                "star": star,
            }
        )
        data = await self._make_request("/item/update", method="POST", data=payload)
        return EagleItem.from_dict(data)

    async def refresh_item_palette(self, item_id: str) -> bool:
        """Ask Eagle to recalculate an item's color palette."""
        await self._make_request("/item/refreshPalette", method="POST", data={"id": item_id})
        return True

    async def refresh_item_thumbnail(self, item_id: str) -> bool:
        """Ask Eagle to regenerate an item's thumbnail."""
        await self._make_request("/item/refreshThumbnail", method="POST", data={"id": item_id})
        return True

    async def get_item_info(self, item_id: str) -> EagleItem:
        """Return full metadata for a single Eagle item."""
        data = await self._make_request("/item/info", params={"id": item_id})
        return EagleItem.from_dict(data)

    async def get_item_thumbnail(self, item_id: str) -> str:
        """Return the absolute thumbnail path stored by Eagle for a single item."""
        data = await self._make_request("/item/thumbnail", params={"id": item_id})
        return str(data)

    async def get_items(
        self,
        limit: int = 200,
        offset: int = 0,
        order_by: Optional[str] = None,
        keyword: Optional[str] = None,
        ext: Optional[str] = None,
        tags: Optional[list[str]] = None,
        folders: Optional[list[str]] = None,
    ) -> list[EagleItem]:
        """Return items matching the provided filter parameters."""
        params = build_get_items_params(
            limit=limit,
            offset=offset,
            order_by=order_by,
            keyword=keyword,
            ext=ext,
            tags=tags,
            folders=folders,
        )
        data = await self._make_request("/item/list", params=params)
        return parse_item_list(data)


__all__ = ["AsyncEagleAPI"]


