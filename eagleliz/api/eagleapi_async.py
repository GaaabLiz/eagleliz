"""Asynchronous Python client for the local Eagle.cool API.

This module provides an ``httpx``-based async wrapper over the official Eagle
desktop API documented at ``https://api.eagle.cool``. It mirrors the public
surface of ``eagleliz.api.eagleapi.EagleAPI`` so the same endpoint coverage is
available in synchronous and asynchronous codebases.
"""

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
    """Asynchronous client for interacting with the local Eagle.cool HTTP API.

    Like the synchronous client, this wrapper builds Eagle endpoint URLs,
    injects an optional token, validates Eagle's ``status/data`` envelope and
    maps successful responses to typed dataclass models. Every public method is
    an awaitable counterpart of the sync API surface.

    Operational failures are raised as ``EagleAPIError``.
    """

    async def _make_request(
        self,
        endpoint: str,
        *,
        method: str = "GET",
        data: Optional[dict[str, Any]] = None,
        params: Optional[dict[str, Any]] = None,
    ) -> Any:
        """Execute a JSON request and unwrap Eagle's ``data`` payload.

        Args:
            endpoint: Eagle endpoint path beginning with ``/``.
            method: HTTP method. The current client uses ``GET`` and ``POST``.
            data: Optional JSON body for ``POST`` endpoints.
            params: Optional query parameters for ``GET`` endpoints.

        Returns:
            The value contained in Eagle's top-level ``data`` field. Endpoints
            that only return ``{"status": "success"}`` are normalized to an
            empty dictionary by the shared response parser.

        Raises:
            EagleAPIError: If the request fails at the transport, HTTP or JSON
                parsing layer, or if Eagle responds with a non-success status.
        """
        url = build_request_url(
            self.base_url,
            endpoint,
            params=params,
            token=self.token if method == "GET" else None,
        )
        payload = build_json_payload(
            data, token=self.token if method == "POST" else None
        )

        async with httpx.AsyncClient() as client:
            try:
                response = await client.request(method, url, json=payload)
                response.raise_for_status()
                result = response.json()
                return parse_api_response(
                    result, url=mask_token(str(response.url), self.token)
                )
            except httpx.HTTPStatusError as exc:
                log_url = mask_token(str(exc.request.url), self.token)
                logger.error(
                    "HTTP error %s for Eagle API at %s. Body: %s",
                    exc.response.status_code,
                    log_url,
                    exc.response.text,
                )
                raise EagleAPIError(
                    f"HTTP {exc.response.status_code} error: {exc.response.text}"
                ) from exc
            except httpx.HTTPError as exc:
                logger.error(
                    "Request transport failed for Eagle API endpoint %s: %s",
                    endpoint,
                    exc,
                )
                raise EagleAPIError(f"Connection error: {exc}") from exc
            except json.JSONDecodeError as exc:
                log_url = mask_token(url, self.token)
                logger.error(
                    "Failed to parse JSON response from Eagle API at %s. Error: %s",
                    log_url,
                    exc,
                )
                raise EagleAPIError(f"JSON parse error: {exc}") from exc

    async def _read_bytes(
        self, endpoint: str, *, params: Optional[dict[str, Any]] = None
    ) -> bytes:
        """Execute an endpoint that streams raw bytes instead of JSON.

        This is currently used for ``GET /api/library/icon``, which returns the
        icon image content directly rather than Eagle's standard JSON envelope.
        """
        url = build_request_url(
            self.base_url, endpoint, params=params, token=self.token
        )

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url)
                response.raise_for_status()
                return response.content
            except httpx.HTTPStatusError as exc:
                log_url = mask_token(str(exc.request.url), self.token)
                logger.error(
                    "HTTP error %s fetching Eagle binary response at %s. Body: %s",
                    exc.response.status_code,
                    log_url,
                    exc.response.text,
                )
                raise EagleAPIError(
                    f"HTTP {exc.response.status_code} error: {exc.response.text}"
                ) from exc
            except httpx.HTTPError as exc:
                logger.error(
                    "Request transport failed for Eagle API binary endpoint %s: %s",
                    endpoint,
                    exc,
                )
                raise EagleAPIError(f"Connection error: {exc}") from exc

    async def get_application_info(self) -> ApplicationInfo:
        """Return metadata about the currently running Eagle application.

        Wraps ``GET /api/application/info`` and returns fields such as Eagle's
        version, build number, executable path and platform.
        """
        data = await self._make_request("/application/info")
        return parse_application_info(data)

    async def get_library_info(self) -> LibraryInfo:
        """Return metadata for the currently opened Eagle library.

        Wraps ``GET /api/library/info`` and includes folder trees, smart
        folders, quick-access sections, tag groups and library modification
        metadata.
        """
        data = await self._make_request("/library/info")
        return parse_library_info(data)

    async def get_library_history(self) -> list[str]:
        """Return filesystem paths of recently opened Eagle libraries.

        Wraps ``GET /api/library/history``.
        """
        data = await self._make_request("/library/history")
        return parse_library_history(data)

    async def switch_library(self, library_path: str) -> bool:
        """Switch Eagle to another library.

        Args:
            library_path: Absolute path of the ``.library`` bundle to open.

        Returns:
            ``True`` when Eagle acknowledges the request successfully.
        """
        await self._make_request(
            "/library/switch", method="POST", data={"libraryPath": library_path}
        )
        return True

    async def get_library_icon(self, library_path: str) -> bytes:
        """Return the raw icon bytes for the given library path.

        The official ``GET /api/library/icon`` endpoint takes a ``libraryPath``
        query parameter and streams image bytes directly.
        """
        return await self._read_bytes(
            "/library/icon", params={"libraryPath": library_path}
        )

    async def create_folder(
        self, folder_name: str, parent_id: Optional[str] = None
    ) -> EagleFolder:
        """Create a folder in the current library.

        Args:
            folder_name: Name of the folder to create.
            parent_id: Optional parent folder ID for nested creation. The
                underlying Eagle parameter name is ``parent``.

        Returns:
            The created folder as returned by ``POST /api/folder/create``.
        """
        payload = compact_dict({"folderName": folder_name, "parent": parent_id})
        data = await self._make_request("/folder/create", method="POST", data=payload)
        return EagleFolder.from_dict(data)

    async def rename_folder(self, folder_id: str, new_name: str) -> EagleFolder:
        """Rename an existing folder.

        Wraps ``POST /api/folder/rename``.
        """
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
        """Update mutable folder metadata.

        According to the official documentation, ``new_color`` accepts the
        values ``red``, ``orange``, ``yellow``, ``green``, ``aqua``, ``blue``,
        ``purple`` and ``pink``.
        """
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
        """Return the folders from the current library.

        Wraps ``GET /api/folder/list``. Eagle may include nested children in
        the returned folder payloads.
        """
        data = await self._make_request("/folder/list")
        return parse_folder_list(data)

    async def list_recent_folders(self) -> list[EagleFolder]:
        """Return folders recently used in Eagle.

        Wraps ``GET /api/folder/listRecent``.
        """
        data = await self._make_request("/folder/listRecent")
        return parse_folder_list(data)

    async def _add_item_from_url_request(
        self,
        *,
        url: str,
        name: str,
        website: Optional[str] = None,
        tags: Optional[list[str]] = None,
        star: Optional[int] = None,
        annotation: Optional[str] = None,
        modificationTime: Optional[int] = None,
        folderId: Optional[str] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> Any:
        """Internal helper for ``POST /api/item/addFromURL``.

        Returns the raw ``data`` payload from Eagle so higher-level callers can
        decide whether to only acknowledge success or extract returned IDs.
        """
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
        return await self._make_request("/item/addFromURL", method="POST", data=payload)

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
        """Import a remote asset into Eagle from a URL or base64 source.

        This method mirrors ``POST /api/item/addFromURL`` from the official
        API. The parameter names ``modificationTime`` and ``folderId`` keep the
        same casing used by Eagle's request schema for easier cross-reference
        with the upstream documentation.
        """
        await self._add_item_from_url_request(
            url=url,
            name=name,
            website=website,
            tags=tags,
            star=star,
            annotation=annotation,
            modificationTime=modificationTime,
            folderId=folderId,
            headers=headers,
        )
        return True

    async def add_items_from_urls(
        self, items: list[EagleItemURLPayload], folder_id: Optional[str] = None
    ) -> bool:
        """Import multiple remote assets in one request.

        Wraps ``POST /api/item/addFromURLs``. Using the batch endpoint is the
        preferred approach when adding many remote items, as also recommended by
        the official documentation.
        """
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
        """Import a local file into the current library.

        Wraps ``POST /api/item/addFromPath``.
        """
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

    async def add_items_from_paths(
        self, items: list[EagleItemPathPayload], folder_id: Optional[str] = None
    ) -> bool:
        """Import multiple local files in one request.

        Wraps ``POST /api/item/addFromPaths``.
        """
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
        """Save a bookmark entry into Eagle.

        Wraps ``POST /api/item/addBookmark``. The optional ``base64`` argument
        is the bookmark thumbnail preview described by the official Eagle
        documentation.
        """
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
        """Move one or more items to Eagle's trash.

        Args:
            item_ids: List of Eagle item IDs to trash.

        Returns:
            ``True`` when Eagle reports success.
        """
        await self._make_request(
            "/item/moveToTrash", method="POST", data={"itemIds": item_ids}
        )
        return True

    async def update_item(
        self,
        item_id: str,
        tags: Optional[list[str]] = None,
        annotation: Optional[str] = None,
        url: Optional[str] = None,
        star: Optional[int] = None,
    ) -> EagleItem:
        """Update mutable metadata fields on an existing Eagle item.

        Wraps ``POST /api/item/update``. The official documentation currently
        lists ``tags``, ``annotation``, ``url`` and ``star`` as supported
        mutable fields.
        """
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
        """Ask Eagle to recompute an item's color analysis.

        Wraps ``POST /api/item/refreshPalette``.
        """
        await self._make_request(
            "/item/refreshPalette", method="POST", data={"id": item_id}
        )
        return True

    async def refresh_item_thumbnail(self, item_id: str) -> bool:
        """Ask Eagle to regenerate an item's thumbnail.

        Per the official documentation, Eagle also refreshes color analysis as
        part of ``POST /api/item/refreshThumbnail``.
        """
        await self._make_request(
            "/item/refreshThumbnail", method="POST", data={"id": item_id}
        )
        return True

    async def get_item_info(self, item_id: str) -> EagleItem:
        """Return full metadata for a single item.

        Wraps ``GET /api/item/info`` and returns the item's core properties,
        folder membership, tags, dimensions and palette information.
        """
        data = await self._make_request("/item/info", params={"id": item_id})
        return EagleItem.from_dict(data)

    async def get_item_thumbnail(self, item_id: str) -> str:
        """Return the absolute thumbnail path recorded by Eagle.

        Wraps ``GET /api/item/thumbnail``.
        """
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
        """Return items matching the provided filter parameters.

        Args:
            limit: Maximum number of items to return. Eagle defaults to ``200``.
            offset: Number of matching items to skip.
            order_by: Optional sort expression such as ``NAME``, ``FILESIZE``,
                ``CREATEDATE`` or ``RESOLUTION``. Prefix with ``-`` for
                descending order, for example ``-FILESIZE``.
            keyword: Optional free-text keyword filter.
            ext: Optional extension filter, such as ``jpg`` or ``png``.
            tags: Optional list of tags. Eagle expects them as a comma-separated
                query parameter and this method performs that conversion.
            folders: Optional list of folder IDs, also sent as a comma-separated
                query parameter.

        Returns:
            A list of ``EagleItem`` models from ``GET /api/item/list``.
        """
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
