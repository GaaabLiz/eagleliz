"""
Eagle model dataclasses definitions.

This module houses all the internal representation logic structures for
parsing API payloads into defined types, handling XMP mappings, and organizing states.
"""

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
    "EagleFolder",
    "EagleItem",
    "EagleItemPathPayload",
    "EagleItemURLPayload",
    "LibraryInfo",
]
