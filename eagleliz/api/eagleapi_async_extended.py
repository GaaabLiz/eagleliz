"""Extended asynchronous Eagle API client.

This module adds higher-level helpers on top of ``AsyncEagleAPI`` for
workflows where local files must be uploaded through ``/api/item/addFromURL``
using a base64 data URI.
"""

from __future__ import annotations

import base64
import os
from typing import Optional

from eagleliz.api._shared import EagleAPIError
from eagleliz.api.eagleapi_async import AsyncEagleAPI

_IMAGE_MIME_TYPES: dict[str, str] = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".gif": "image/gif",
}


class AsynchEagleApiExtended(AsyncEagleAPI):
    """Extended async client with local-file upload convenience helpers."""

    async def add_item_from_file(
        self,
        path: str,
        name: str,
        tags: Optional[list[str]] = None,
    ) -> str:
        """Upload a local image file through ``POST /api/item/addFromURL``.

        The file is converted to a base64 data URI so Eagle can receive its
        bytes over HTTP even when Eagle cannot access the file path directly.

        Args:
            path: Local absolute or relative file path.
            name: Display name for the new Eagle item.
            tags: Optional list of tags.

        Returns:
            The created Eagle item ID.

        Raises:
            RuntimeError: On file read errors, API failures, or missing ID in
                Eagle response payload.
        """
        data_uri = self._build_data_uri(path)
        return await self._post_to_eagle(data_uri, name, tags or [])

    def _build_data_uri(self, path: str) -> str:
        """Return a base64 data URI for a local image file.

        Args:
            path: Local file path.

        Returns:
            A string like ``data:image/png;base64,<...>``.

        Raises:
            RuntimeError: If the file cannot be read.
        """
        ext = os.path.splitext(path)[1].lower()
        mime = _IMAGE_MIME_TYPES.get(ext, "image/png")

        try:
            with open(path, "rb") as handle:
                raw = handle.read()
        except OSError as exc:
            raise RuntimeError(
                f"Impossibile leggere il file immagine '{path}': {exc}"
            ) from exc

        b64 = base64.b64encode(raw).decode("ascii")
        return f"data:{mime};base64,{b64}"

    async def _post_to_eagle(
        self, url_or_data_uri: str, name: str, tags: list[str]
    ) -> str:
        """Call ``POST /api/item/addFromURL`` and return the new item ID.

        Args:
            url_or_data_uri: Remote URL or data URI payload.
            name: Display name for the item.
            tags: Tags to attach.

        Returns:
            Eagle item ID.

        Raises:
            RuntimeError: On API errors or if Eagle does not return an ID.
        """
        try:
            data = await self._add_item_from_url_request(
                url=url_or_data_uri, name=name, tags=tags
            )
        except EagleAPIError as exc:
            raise RuntimeError(f"Eagle API request failed: {exc}") from exc

        if isinstance(data, str) and data:
            return data

        if isinstance(data, dict):
            for key in ("id", "itemId", "itemID"):
                value = data.get(key)
                if isinstance(value, str) and value:
                    return value

        raise RuntimeError(f"Eagle ha risposto senza item ID valido: {data}")


__all__ = ["AsynchEagleApiExtended"]
