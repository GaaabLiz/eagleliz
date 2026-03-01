import os
import requests
from typing import Optional, Dict, Any
from datetime import datetime, timezone

class ImmichAPIError(Exception):
    pass

class ImmichAPI:
    """Python bindings for the Immich API."""
    
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        # Fallback to environment variables if not provided
        self.base_url = base_url or os.environ.get("IMMICH_URL")
        self.api_key = api_key or os.environ.get("IMMICH_API_KEY")
        
        if not self.base_url or not self.api_key:
            raise ValueError("Immich base_url and api_key must be configured via params or environment variables.")
        
        # Ensure base URL does not have trailing slash and appends /api
        self.base_url = self.base_url.rstrip("/")
        if not self.base_url.endswith("/api"):
            self.base_url += "/api"

        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "x-api-key": self.api_key
        })

    def _get_iso_timestamp(self, timestamp: float) -> str:
        """Converts a Unix timestamp to ISO 8601 format required by Immich."""
        dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        return dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

    def upload_asset(self, file_path: str, device_asset_id: Optional[str] = None, device_id: str = "eagleliz-python") -> Dict[str, Any]:
        """
        Uploads a new media asset to Immich.
        
        Args:
            file_path: The local path to the media file.
            device_asset_id: A unique identifier for the asset on the device. Defaults to the filename.
            device_id: The identifier for the device making the upload.
            
        Returns:
            Dictionary containing the Immich API response.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
            
        filename = os.path.basename(file_path)
        if not device_asset_id:
            device_asset_id = filename
            
        url = f"{self.base_url}/assets"
        
        stat = os.stat(file_path)
        
        data = {
            "deviceAssetId": device_asset_id,
            "deviceId": device_id,
            "fileCreatedAt": self._get_iso_timestamp(stat.st_mtime),
            "fileModifiedAt": self._get_iso_timestamp(stat.st_mtime),
            "isFavorite": "false",
        }
        
        with open(file_path, "rb") as f:
            files = {
                "assetData": (filename, f, "application/octet-stream")
            }
            response = self.session.post(url, data=data, files=files)
            
        if not response.ok:
            raise ImmichAPIError(f"Failed to upload asset: {response.status_code} {response.text}")
            
        return response.json()

    def update_asset(self, asset_id: str, is_favorite: Optional[bool] = None, is_archived: Optional[bool] = None, description: Optional[str] = None) -> Dict[str, Any]:
        """
        Modifies the metadata of an existing Immich asset.
        
        Args:
            asset_id: The unique Immich ID of the asset.
            is_favorite: Boolean to favorite/unfavorite the asset.
            is_archived: Boolean to archive/unarchive the asset.
            description: String description for the asset.
            
        Returns:
            Dictionary containing the Immich API response.
        """
        url = f"{self.base_url}/assets/{asset_id}"
        
        payload = {}
        if is_favorite is not None:
            payload["isFavorite"] = is_favorite
        if is_archived is not None:
            payload["isArchived"] = is_archived
        if description is not None:
            payload["description"] = description
            
        response = self.session.put(url, json=payload)
        
        if not response.ok:
            raise ImmichAPIError(f"Failed to update asset {asset_id}: {response.status_code} {response.text}")
            
        return response.json()
