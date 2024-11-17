from typing import Any
from dataclasses import dataclass
import json


@dataclass
class Data:
    version: str
    prereleaseVersion: str
    buildVersion: str
    execPath: str
    platform: str

    @staticmethod
    def from_dict(obj: Any) -> 'Data':
        _version = str(obj.get("version", None))
        _prereleaseVersion = str(obj.get("prereleaseVersion", None))
        _buildVersion = str(obj.get("buildVersion", None))
        _execPath = str(obj.get("execPath", None))
        _platform = str(obj.get("platform", None))
        return Data(_version, _prereleaseVersion, _buildVersion, _execPath, _platform)


@dataclass
class EagleDto:
    status: str
    data: Data | None
    data2: str | None

    @staticmethod
    def from_dict(obj: Any) -> 'EagleDto':
        _status = str(obj.get("status"))
        _data = Data.from_dict(obj.get("data") if "data" in obj else None)
        return EagleDto(_status, _data, None)

    @staticmethod
    def from_dict2(obj: Any) -> 'EagleDto':
        _status = str(obj.get("status"))
        _data2 = obj.get("data") if "data" in obj else None
        return EagleDto(_status, None, _data2)
