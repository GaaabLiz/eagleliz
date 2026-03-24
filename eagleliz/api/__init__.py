"""
Eagle API Bindings Module.

This package contains the core Python bindings for interacting with the 
local Eagle App REST API, including dataclasses for serialization and 
the main `EagleAPI` client class.
"""

from eagleliz.api._shared import EagleAPIError
from eagleliz.api.eagleapi import EagleAPI
from eagleliz.api.eagleapi_async import AsyncEagleAPI
from eagleliz.model.api import (
	ApplicationInfo,
	EagleFolder,
	EagleItem,
	EagleItemPathPayload,
	EagleItemURLPayload,
	LibraryInfo,
)

__all__ = [
	"ApplicationInfo",
	"AsyncEagleAPI",
	"EagleAPI",
	"EagleAPIError",
	"EagleFolder",
	"EagleItem",
	"EagleItemPathPayload",
	"EagleItemURLPayload",
	"LibraryInfo",
]
