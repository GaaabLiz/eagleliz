"""
Python bindings for interacting with the Immich API.

This module provides the `ImmichAPI` class which encapsulates the REST API 
calls to an Immich server, allowing for operations such as uploading 
assets and updating their metadata.
"""
import os
import requests
from typing import Optional, Dict, Any
from datetime import datetime, timezone

class ImmichAPIError(Exception):
    """Exception raised for errors encountered when interacting with the Immich API."""
    pass

class ImmichAPI:
    """Python bindings for the Immich API."""
    
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        """
        Initializes the Immich API client.
        
        Args:
            base_url (Optional[str]): The base URL of the Immich server (e.g., 'http://192.168.0.201:30047').
                If not provided, falls back to the IMMICH_URL environment variable.
            api_key (Optional[str]): The API key for authenticating with the Immich server.
                If not provided, falls back to the IMMICH_API_KEY environment variable.
                
        Raises:
            ValueError: If the base URL or API key is not provided and cannot be found in environment variables.
        """
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
        """
        Converts a Unix timestamp to the ISO 8601 string format required by Immich.
        
        Args:
            timestamp (float): The Unix timestamp in seconds to convert.
            
        Returns:
            str: The formatted ISO 8601 timestamp string ending with 'Z'.
        """
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
