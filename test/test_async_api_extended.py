import asyncio
import base64
import os
import tempfile

import pytest

from eagleliz.api._shared import EagleAPIError
from eagleliz.api.eagleapi_async_extended import AsynchEagleApiExtended


def test_build_data_uri_builds_png_prefix_and_base64_payload():
    raw = b"fake-image-bytes"
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as handle:
        handle.write(raw)
        temp_path = handle.name

    try:
        client = AsynchEagleApiExtended()
        data_uri = client._build_data_uri(temp_path)
        assert data_uri.startswith("data:image/png;base64,")
        encoded = data_uri.split(",", 1)[1]
        assert base64.b64decode(encoded) == raw
    finally:
        os.remove(temp_path)


def test_build_data_uri_raises_runtime_error_on_missing_file():
    client = AsynchEagleApiExtended()

    with pytest.raises(RuntimeError, match="Impossibile leggere il file immagine"):
        client._build_data_uri("/tmp/definitely-not-present-eagleliz.png")


def test_add_item_from_file_uses_helpers(monkeypatch):
    client = AsynchEagleApiExtended()
    captured: dict[str, object] = {}

    def fake_build_data_uri(path: str) -> str:
        captured["path"] = path
        return "data:image/png;base64,ZmFrZQ=="

    async def fake_post(data_uri: str, name: str, tags: list[str]) -> str:
        captured["data_uri"] = data_uri
        captured["name"] = name
        captured["tags"] = tags
        return "item-123"

    monkeypatch.setattr(client, "_build_data_uri", fake_build_data_uri)
    monkeypatch.setattr(client, "_post_to_eagle", fake_post)

    result = asyncio.run(
        client.add_item_from_file("/tmp/photo.png", "photo", ["tag-a", "tag-b"])
    )

    assert result == "item-123"
    assert captured == {
        "path": "/tmp/photo.png",
        "data_uri": "data:image/png;base64,ZmFrZQ==",
        "name": "photo",
        "tags": ["tag-a", "tag-b"],
    }


def test_post_to_eagle_calls_expected_endpoint_and_returns_string_id(monkeypatch):
    client = AsynchEagleApiExtended()
    captured: dict[str, object] = {}

    async def fake_make_request(
        endpoint: str, *, method: str = "GET", data=None, params=None
    ):
        captured["endpoint"] = endpoint
        captured["method"] = method
        captured["data"] = data
        captured["params"] = params
        return "new-item-id"

    monkeypatch.setattr(client, "_make_request", fake_make_request)

    result = asyncio.run(
        client._post_to_eagle("data:image/png;base64,abc", "Image", ["a"])
    )

    assert result == "new-item-id"
    assert captured["endpoint"] == "/item/addFromURL"
    assert captured["method"] == "POST"
    assert captured["data"] == {
        "url": "data:image/png;base64,abc",
        "name": "Image",
        "tags": ["a"],
    }


def test_post_to_eagle_wraps_eagle_api_errors(monkeypatch):
    client = AsynchEagleApiExtended()

    async def fake_make_request(
        endpoint: str, *, method: str = "GET", data=None, params=None
    ):
        raise EagleAPIError("boom")

    monkeypatch.setattr(client, "_make_request", fake_make_request)

    with pytest.raises(RuntimeError, match="Eagle API request failed: boom"):
        asyncio.run(client._post_to_eagle("data:image/png;base64,abc", "Image", []))
