"""Dataclass and DTO models used by the Eagle.cool API clients."""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from typing import Any, Optional


def _split_known_and_extra_data(model_cls: type, data: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Split a raw API dictionary into dataclass fields and extra values."""
    known_fields = {model_field.name for model_field in fields(model_cls) if model_field.name != "_extra_data"}
    known_data = {key: value for key, value in data.items() if key in known_fields}
    extra_data = {key: value for key, value in data.items() if key not in known_fields}
    return known_data, extra_data


@dataclass
class ApplicationInfo:
    """Information returned by the Eagle application info endpoint."""

    version: str = ""
    prereleaseVersion: Optional[str] = None
    buildVersion: Optional[str] = None
    execPath: str = ""
    platform: str = ""
    _extra_data: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Optional[dict[str, Any]]) -> "ApplicationInfo":
        """Build an ``ApplicationInfo`` instance from a raw Eagle API payload."""
        known_data, extra_data = _split_known_and_extra_data(cls, data or {})
        return cls(**known_data, _extra_data=extra_data)


@dataclass
class EagleFolder:
    """Folder model returned by the Eagle folder endpoints."""

    id: str = ""
    name: str = ""
    description: Optional[str] = None
    modificationTime: Optional[int] = None
    images: Optional[list[str]] = None
    folders: Optional[list[str]] = None
    imagesMappings: Optional[dict[str, Any]] = None
    tags: Optional[list[str]] = None
    children: Optional[list[Any]] = None
    isExpand: Optional[bool] = None
    size: Optional[int] = None
    vstype: Optional[str] = None
    editable: Optional[bool] = None
    pinyin: Optional[str] = None
    styles: Optional[dict[str, Any]] = None
    _extra_data: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Optional[dict[str, Any]]) -> "EagleFolder":
        """Build an ``EagleFolder`` instance from a raw Eagle API payload."""
        known_data, extra_data = _split_known_and_extra_data(cls, data or {})
        return cls(**known_data, _extra_data=extra_data)


@dataclass
class EagleItemURLPayload:
    """DTO used by batch URL-based item creation endpoints."""

    url: str
    name: str
    website: Optional[str] = None
    tags: Optional[list[str]] = None
    annotation: Optional[str] = None
    modificationTime: Optional[int] = None
    headers: Optional[dict[str, str]] = None
    star: Optional[int] = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize the payload while omitting ``None`` values."""
        return {key: value for key, value in self.__dict__.items() if value is not None}


@dataclass
class EagleItemPathPayload:
    """DTO used by batch path-based item creation endpoints."""

    path: str
    name: str
    website: Optional[str] = None
    tags: Optional[list[str]] = None
    annotation: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize the payload while omitting ``None`` values."""
        return {key: value for key, value in self.__dict__.items() if value is not None}


@dataclass
class EagleItem:
    """Item model returned by the Eagle item endpoints."""

    id: str = ""
    name: str = ""
    ext: str = ""
    url: str = ""
    annotation: str = ""
    tags: list[str] = field(default_factory=list)
    folders: list[str] = field(default_factory=list)
    size: int = 0
    isDeleted: bool = False
    modificationTime: int = 0
    lastModified: int = 0
    noThumbnail: bool = False
    width: int = 0
    height: int = 0
    palettes: list[dict[str, Any]] = field(default_factory=list)
    star: int = 0
    _extra_data: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Optional[dict[str, Any]]) -> "EagleItem":
        """Build an ``EagleItem`` instance from a raw Eagle API payload."""
        known_data, extra_data = _split_known_and_extra_data(cls, data or {})
        known_data["tags"] = known_data.get("tags") or []
        known_data["folders"] = known_data.get("folders") or []
        known_data["palettes"] = known_data.get("palettes") or []
        return cls(**known_data, _extra_data=extra_data)


@dataclass
class LibraryInfo:
    """Library model returned by the Eagle library info endpoint."""

    folders: list[EagleFolder] = field(default_factory=list)
    smartFolders: list[dict[str, Any]] = field(default_factory=list)
    quickAccess: list[dict[str, Any]] = field(default_factory=list)
    tagsGroups: list[dict[str, Any]] = field(default_factory=list)
    modificationTime: int = 0
    applicationVersion: str = ""
    _extra_data: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Optional[dict[str, Any]]) -> "LibraryInfo":
        """Build a ``LibraryInfo`` instance from a raw Eagle API payload."""
        known_data, extra_data = _split_known_and_extra_data(cls, data or {})
        folders_data = known_data.get("folders") or []
        known_data["folders"] = [EagleFolder.from_dict(folder_data) for folder_data in folders_data]
        known_data.setdefault("smartFolders", [])
        known_data.setdefault("quickAccess", [])
        known_data.setdefault("tagsGroups", [])
        known_data.setdefault("modificationTime", 0)
        known_data.setdefault("applicationVersion", "")
        return cls(**known_data, _extra_data=extra_data)


__all__ = [
    "ApplicationInfo",
    "EagleFolder",
    "EagleItem",
    "EagleItemPathPayload",
    "EagleItemURLPayload",
    "LibraryInfo",
]

