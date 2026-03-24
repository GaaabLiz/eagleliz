"""Utility helpers shared by the Eagle sync and async API clients."""

from __future__ import annotations

import os
from typing import Any, Optional
from urllib.parse import parse_qs, urlencode, urlparse

from eagleliz.model.api import ApplicationInfo, EagleFolder, EagleItem, LibraryInfo


class EagleAPIError(Exception):
    """Base exception raised for Eagle API transport and response errors."""


class EagleAPIBase:
    """Common configuration and constructor helpers for Eagle API clients."""

    def __init__(self, host: str = "localhost", port: int = 41595, token: Optional[str] = None):
        self.base_url = f"http://{host}:{port}/api"
        self.token = token

    @classmethod
    def from_url(cls, raw_url: str):
        """Create a client instance from an Eagle API URL, with optional token."""
        parsed = urlparse(raw_url)
        token = parse_qs(parsed.query).get("token", [None])[0]
        host = parsed.hostname or "localhost"
        port = parsed.port or 41595
        return cls(host=host, port=port, token=token)

    @classmethod
    def from_env(cls, env_var: str = "EAGLE_URL"):
        """Create a client instance from the URL stored in an environment variable."""
        url = os.getenv(env_var)
        if not url:
            return cls()
        return cls.from_url(url)


def compact_dict(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a shallow payload copy without keys whose value is ``None``."""
    return {key: value for key, value in payload.items() if value is not None}


def build_request_url(
    base_url: str,
    endpoint: str,
    *,
    params: Optional[dict[str, Any]] = None,
    token: Optional[str] = None,
) -> str:
    """Build a fully encoded request URL including query string and optional token."""
    query_params = compact_dict(dict(params or {}))
    if token and "token" not in query_params:
        query_params["token"] = token

    encoded_query = urlencode(query_params)
    url = f"{base_url}{endpoint}"
    if encoded_query:
        return f"{url}?{encoded_query}"
    return url


def build_json_payload(payload: Optional[dict[str, Any]], token: Optional[str] = None) -> Optional[dict[str, Any]]:
    """Build a JSON payload for POST requests and inject the token when needed."""
    if payload is None:
        return None

    built_payload = dict(payload)
    if token and "token" not in built_payload:
        built_payload["token"] = token
    return built_payload


def mask_token(value: str, token: Optional[str]) -> str:
    """Mask the token in a loggable string representation."""
    if token:
        return value.replace(token, "********")
    return value


def parse_api_response(result: Any, *, url: str) -> Any:
    """Validate the JSON response envelope returned by the Eagle API."""
    if not isinstance(result, dict):
        raise EagleAPIError(f"Unexpected response type from Eagle API at {url}: {type(result).__name__}")

    status = result.get("status")
    if status != "success":
        message = result.get("message") or result.get("error") or "Unknown Eagle API error"
        raise EagleAPIError(f"API returned status {status!r}: {message}")

    return result.get("data", {})


def build_get_items_params(
    *,
    limit: int = 200,
    offset: int = 0,
    order_by: Optional[str] = None,
    keyword: Optional[str] = None,
    ext: Optional[str] = None,
    tags: Optional[list[str]] = None,
    folders: Optional[list[str]] = None,
) -> dict[str, Any]:
    """Build the filter parameters accepted by ``/item/list``."""
    params: dict[str, Any] = {"limit": limit, "offset": offset}
    if order_by:
        params["orderBy"] = order_by
    if keyword:
        params["keyword"] = keyword
    if ext:
        params["ext"] = ext
    if tags:
        params["tags"] = ",".join(tags)
    if folders:
        params["folders"] = ",".join(folders)
    return params


def parse_application_info(data: dict[str, Any]) -> ApplicationInfo:
    """Convert raw application metadata into an ``ApplicationInfo`` model."""
    return ApplicationInfo.from_dict(data)


def parse_library_history(data: Any) -> list[str]:
    """Normalize the library history endpoint response to a list of paths."""
    if isinstance(data, list):
        return [str(item) for item in data]
    return []


def parse_folder_list(data: Any) -> list[EagleFolder]:
    """Convert a raw folder list payload into ``EagleFolder`` instances."""
    if not isinstance(data, list):
        return []
    return [EagleFolder.from_dict(folder_data) for folder_data in data]


def parse_item_list(data: Any) -> list[EagleItem]:
    """Convert a raw item list payload into ``EagleItem`` instances."""
    if not isinstance(data, list):
        return []
    return [EagleItem.from_dict(item_data) for item_data in data]


def parse_library_info(data: dict[str, Any]) -> LibraryInfo:
    """Convert raw library metadata into a ``LibraryInfo`` model."""
    return LibraryInfo.from_dict(data)

