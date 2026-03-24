"""Shared building blocks for the Eagle API clients.

The official Eagle API is a local HTTP service exposed by the desktop app,
typically at ``http://localhost:41595/api``. Most endpoints return a JSON
envelope shaped like ``{"status": "success", "data": ...}``, while a few
endpoints such as ``/library/icon`` stream raw bytes instead.

This module centralises the boring-but-important pieces used by both the
synchronous and asynchronous clients: configuration, token handling, payload
cleanup, request URL construction, response validation, and conversion from raw
dictionaries into the public dataclass models defined in
``eagleliz.model.api``.
"""

from __future__ import annotations

import os
from typing import Any, Optional
from urllib.parse import parse_qs, urlencode, urlparse

from eagleliz.model.api import ApplicationInfo, EagleFolder, EagleItem, LibraryInfo


class EagleAPIError(Exception):
    """Base exception raised for Eagle API transport and response errors.

    The sync and async clients both translate network failures, HTTP status
    failures and non-success Eagle API responses into this exception so callers
    can handle all operational API failures consistently.
    """


class EagleAPIBase:
    """Common configuration and constructor helpers for Eagle API clients.

    Attributes:
        base_url: Fully qualified Eagle API base URL, including the ``/api``
            prefix used by every endpoint.
        token: Optional API token appended to requests when provided.
    """

    def __init__(self, host: str = "localhost", port: int = 41595, token: Optional[str] = None):
        """Initialize a client against a local Eagle instance.

        Args:
            host: Hostname where the Eagle desktop app exposes its local API.
            port: Listening port used by the Eagle API server. The official
                documentation uses ``41595`` by default.
            token: Optional authentication token. When present, it is injected
                into query parameters for ``GET`` requests and JSON bodies for
                ``POST`` requests.
        """
        self.base_url = f"http://{host}:{port}/api"
        self.token = token

    @classmethod
    def from_url(cls, raw_url: str):
        """Create a client instance from a complete Eagle API URL.

        The input may include the ``/api`` path and an optional ``token`` query
        parameter, for example ``http://localhost:41595/api?token=secret``.
        Only the hostname, port and token are extracted; endpoint fragments and
        additional query parameters are ignored.

        Args:
            raw_url: Full Eagle API URL.

        Returns:
            A configured client instance of the concrete subclass.
        """
        parsed = urlparse(raw_url)
        token = parse_qs(parsed.query).get("token", [None])[0]
        host = parsed.hostname or "localhost"
        port = parsed.port or 41595
        return cls(host=host, port=port, token=token)

    @classmethod
    def from_env(cls, env_var: str = "EAGLE_URL"):
        """Create a client instance from an environment variable.

        Args:
            env_var: Environment variable containing a full Eagle API URL.
                When the variable is unset or empty, a default localhost client
                is returned instead.

        Returns:
            A configured client instance of the concrete subclass.
        """
        url = os.getenv(env_var)
        if not url:
            return cls()
        return cls.from_url(url)


def compact_dict(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a shallow payload copy without ``None`` values.

    This helper intentionally preserves other falsy values such as ``0``,
    ``False``, empty strings, and empty containers because those can be valid
    Eagle API inputs.
    """
    return {key: value for key, value in payload.items() if value is not None}


def build_request_url(
    base_url: str,
    endpoint: str,
    *,
    params: Optional[dict[str, Any]] = None,
    token: Optional[str] = None,
) -> str:
    """Build a fully encoded Eagle request URL.

    Args:
        base_url: Client base URL, usually ``http://localhost:41595/api``.
        endpoint: Endpoint path beginning with ``/``.
        params: Optional query parameters for the request.
        token: Optional API token to append to the query string when no
            explicit ``token`` parameter is already present.

    Returns:
        The final request URL, including an encoded query string when needed.
    """
    query_params = compact_dict(dict(params or {}))
    if token and "token" not in query_params:
        query_params["token"] = token

    encoded_query = urlencode(query_params)
    url = f"{base_url}{endpoint}"
    if encoded_query:
        return f"{url}?{encoded_query}"
    return url


def build_json_payload(payload: Optional[dict[str, Any]], token: Optional[str] = None) -> Optional[dict[str, Any]]:
    """Build a JSON payload for ``POST`` requests.

    The input mapping is copied so the caller's dictionary is never mutated. If
    a token is supplied it is inserted only when the payload does not already
    define one.

    Args:
        payload: Request body to send as JSON.
        token: Optional API token for authenticated requests.

    Returns:
        A new dictionary ready for JSON serialization, or ``None`` when the
        caller does not need a request body.
    """
    if payload is None:
        return None

    built_payload = dict(payload)
    if token and "token" not in built_payload:
        built_payload["token"] = token
    return built_payload


def mask_token(value: str, token: Optional[str]) -> str:
    """Mask a token before logging a URL or payload fragment.

    Args:
        value: String that may contain the token in plain text.
        token: Sensitive token value to redact.

    Returns:
        The original string when no token is available, otherwise the string
        with every literal occurrence replaced by ``********``.
    """
    if token:
        return value.replace(token, "********")
    return value


def parse_api_response(result: Any, *, url: str) -> Any:
    """Validate and unwrap the standard Eagle JSON response envelope.

    According to the official documentation, most endpoints return a dictionary
    containing ``status`` and, on success, an optional ``data`` field. This
    helper enforces that contract and converts any non-success result into an
    ``EagleAPIError`` with context about the failing request.

    Args:
        result: Decoded JSON payload returned by the server.
        url: Log-safe request URL used in error messages.

    Returns:
        The value contained in ``data``. When the API returns success without a
        data field, an empty dictionary is returned for consistency.

    Raises:
        EagleAPIError: If the response is not a dictionary or the reported
            status is not ``"success"``.
    """
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
    """Build query parameters for ``/item/list``.

    The official Eagle documentation accepts ``orderBy`` values such as
    ``CREATEDATE``, ``FILESIZE``, ``NAME`` and ``RESOLUTION``. Tag and folder
    filters are transmitted as comma-separated strings.

    Args:
        limit: Maximum number of items to return. Eagle defaults to ``200``.
        offset: Number of matching items to skip before collecting results.
        order_by: Optional Eagle sort expression, including descending values
            prefixed with ``-``.
        keyword: Optional free-text filter.
        ext: Optional file extension filter, for example ``jpg`` or ``png``.
        tags: Optional list of tags. They are joined with commas.
        folders: Optional list of folder IDs. They are joined with commas.

    Returns:
        A query-parameter dictionary ready to be passed to ``build_request_url``.
    """
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
    """Normalize the library history response to a list of filesystem paths.

    The official endpoint returns an array of recently opened library paths. If
    Eagle ever responds with an unexpected type, an empty list is returned so
    callers receive a predictable container type.
    """
    if isinstance(data, list):
        return [str(item) for item in data]
    return []


def parse_folder_list(data: Any) -> list[EagleFolder]:
    """Convert a raw folder list payload into ``EagleFolder`` instances.

    Non-list payloads are normalized to an empty list instead of raising, which
    keeps list-oriented client methods easy to consume.
    """
    if not isinstance(data, list):
        return []
    return [EagleFolder.from_dict(folder_data) for folder_data in data]


def parse_item_list(data: Any) -> list[EagleItem]:
    """Convert a raw item list payload into ``EagleItem`` instances.

    Non-list payloads are normalized to an empty list instead of raising, which
    mirrors the behaviour of ``parse_folder_list`` and simplifies callers.
    """
    if not isinstance(data, list):
        return []
    return [EagleItem.from_dict(item_data) for item_data in data]


def parse_library_info(data: dict[str, Any]) -> LibraryInfo:
    """Convert raw library metadata into a ``LibraryInfo`` model."""
    return LibraryInfo.from_dict(data)

