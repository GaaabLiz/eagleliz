import json
import urllib.request
import urllib.error
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class ApplicationInfo:
    """Dataclass representing the Eagle application information."""
    version: str
    prereleaseVersion: Optional[str]
    buildVersion: str
    execPath: str
    platform: str

@dataclass
class EagleFolder:
    """Dataclass representing an Eagle Folder."""
    id: str
    name: str
    modificationTime: Optional[int] = None
    images: Optional[List[str]] = None
    folders: Optional[List[str]] = None
    imagesMappings: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    children: Optional[List[Any]] = None
    isExpand: Optional[bool] = None
    size: Optional[int] = None
    vstype: Optional[str] = None
    editable: Optional[bool] = None
    pinyin: Optional[str] = None
    styles: Optional[Dict[str, Any]] = None
    # We add a generic catch-all dict to avoid unpacking errors on future schema changes
    _extra_data: Dict[str, Any] = None 

    @classmethod
    def from_dict(cls, data: dict) -> 'EagleFolder':
        """Constructs an EagleFolder from a raw dictionary, securely ignoring unspecified kwargs."""
        field_names = {f for f in cls.__dataclass_fields__ if f != '_extra_data'}
        kwargs = {k: v for k, v in data.items() if k in field_names}
        extra_data = {k: v for k, v in data.items() if k not in field_names}
        
        return cls(**kwargs, _extra_data=extra_data)

@dataclass
class EagleItemURLPayload:
    """Dataclass representing a single item payload for /item/addFromURLs"""
    url: str
    name: str
    website: Optional[str] = None
    tags: Optional[List[str]] = None
    annotation: Optional[str] = None
    modificationTime: Optional[int] = None
    headers: Optional[Dict[str, str]] = None
    
    def to_dict(self) -> dict:
        """Serializes payload dropping None values."""
        return {k: v for k, v in self.__dict__.items() if v is not None}

@dataclass
class EagleItemPathPayload:
    """Dataclass representing a single local item payload for /item/addFromPaths"""
    path: str
    name: str
    website: Optional[str] = None
    tags: Optional[List[str]] = None
    annotation: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Serializes payload dropping None values."""
        return {k: v for k, v in self.__dict__.items() if v is not None}

class EagleAPIError(Exception):
    """Base exception for Eagle API errors."""
    pass

class EagleAPI:
    """Client for interacting with the local Eagle.cool API."""
    
    def __init__(self, host: str = "localhost", port: int = 41595):
        self.base_url = f"http://{host}:{port}/api"
        
    def _make_request(self, endpoint: str, method: str = "GET", data: Optional[dict] = None) -> dict:
        url = f"{self.base_url}{endpoint}"
        
        req_kwargs = {'method': method}
        if data is not None:
            json_data = json.dumps(data).encode('utf-8')
            req_kwargs['data'] = json_data
            req_kwargs['headers'] = {'Content-Type': 'application/json'}
            
        req = urllib.request.Request(url, **req_kwargs)
        
        try:
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode())
                if result.get("status") != "success":
                   raise EagleAPIError(f"API returned status: {result.get('status')}")
                return result.get("data", {})
        except urllib.error.HTTPError as e:
            error_body = e.read().decode()
            logger.error(f"HTTP Error {e.code} for Eagle API at {url}. Body: {error_body}")
            raise EagleAPIError(f"HTTP {e.code} error: {error_body}") from e
        except urllib.error.URLError as e:
            logger.error(f"Failed to connect to Eagle API at {url}. Is Eagle running? Error: {e}")
            raise EagleAPIError(f"Connection error: {e}") from e
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse response from Eagle API at {url}. Error: {e}")
            raise EagleAPIError(f"JSON Parse error: {e}") from e

    def get_application_info(self) -> ApplicationInfo:
        """
        Get detailed information on the Eagle App currently running.
        
        Returns:
            ApplicationInfo: An object containing version, platform, and executable path.
        """
        data = self._make_request("/application/info")
        return ApplicationInfo(
            version=data.get("version"),
            prereleaseVersion=data.get("prereleaseVersion"),
            buildVersion=data.get("buildVersion"),
            execPath=data.get("execPath"),
            platform=data.get("platform")
        )

    def create_folder(self, folder_name: str, parent_id: Optional[str] = None) -> EagleFolder:
        """
        Create a new folder in the current Eagle library.

        Args:
            folder_name (str): The name of the new folder.
            parent_id (Optional[str]): The ID of the parent folder. Defaults to None (root).

        Returns:
            EagleFolder: An object representing the newly created folder.
        """
        payload = {"folderName": folder_name}
        if parent_id:
            payload["parent"] = parent_id
            
        data = self._make_request("/folder/create", method="POST", data=payload)
        return EagleFolder.from_dict(data)

    def rename_folder(self, folder_id: str, new_name: str) -> EagleFolder:
        """
        Rename an existing folder in the current Eagle library.

        Args:
            folder_id (str): The ID of the folder to rename.
            new_name (str): The new name for the folder.

        Returns:
            EagleFolder: An object representing the renamed folder.
        """
        payload = {
            "folderId": folder_id,
            "newName": new_name
        }
        
        data = self._make_request("/folder/rename", method="POST", data=payload)
        return EagleFolder.from_dict(data)

    def update_folder(self, folder_id: str, new_name: Optional[str] = None, new_description: Optional[str] = None, new_color: Optional[str] = None) -> EagleFolder:
        """
        Update the specified folder with new properties.

        Args:
            folder_id (str): The ID of the folder to update.
            new_name (Optional[str]): The new name of the folder.
            new_description (Optional[str]): The new description of the folder.
            new_color (Optional[str]): The new color. Valid options: "red", "orange", "green", "yellow", "aqua", "blue", "purple", "pink".

        Returns:
            EagleFolder: An object representing the updated folder.
        """
        payload = {"folderId": folder_id}
        if new_name is not None:
            payload["newName"] = new_name
        if new_description is not None:
            payload["newDescription"] = new_description
        if new_color is not None:
            payload["newColor"] = new_color
            
        data = self._make_request("/folder/update", method="POST", data=payload)
        return EagleFolder.from_dict(data)

    def list_folders(self) -> List[EagleFolder]:
        """
        Get the list of folders of the current library.
        
        Returns:
            List[EagleFolder]: A list containing the root folders of the library.
        """
        data = self._make_request("/folder/list")
        return [EagleFolder.from_dict(folder_data) for folder_data in data]

    def list_recent_folders(self) -> List[EagleFolder]:
        """
        Get the list of folders recently used by the user.
        
        Returns:
            List[EagleFolder]: A list containing the recently used folders.
        """
        data = self._make_request("/folder/listRecent")
        return [EagleFolder.from_dict(folder_data) for folder_data in data]

    def add_item_from_url(
        self,
        url: str,
        name: str,
        website: Optional[str] = None,
        tags: Optional[List[str]] = None,
        star: Optional[int] = None,
        annotation: Optional[str] = None,
        modificationTime: Optional[int] = None,
        folderId: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Add an image from a URL or base64 data to the Eagle App.

        Args:
            url (str): Required. The URL of the image to be added. Supports http, https, base64.
            name (str): Required. The name of the image.
            website (Optional[str]): The source address of the image.
            tags (Optional[List[str]]): Tags for the image.
            star (Optional[int]): The rating for the image (1-5).
            annotation (Optional[str]): The annotation/notes for the image.
            modificationTime (Optional[int]): The creation date of the image. Modifies sorting in Eagle.
            folderId (Optional[str]): ID of the folder to add the image to.
            headers (Optional[Dict[str, str]]): HTTP headers, e.g., to circumvent security like referer checks.

        Returns:
            bool: True if the operation was successful.
        """
        payload = {"url": url, "name": name}
        if website is not None:
            payload["website"] = website
        if tags is not None:
            payload["tags"] = tags
        if star is not None:
            payload["star"] = star
        if annotation is not None:
            payload["annotation"] = annotation
        if modificationTime is not None:
            payload["modificationTime"] = modificationTime
        if folderId is not None:
            payload["folderId"] = folderId
        if headers is not None:
            payload["headers"] = headers

        # Since a successful addFromURL just returns { "status": "success" }
        # the make_request function already validates this and returns the inner 'data' dict (which is empty here)
        # We can just return True upon no errors.
        self._make_request("/item/addFromURL", method="POST", data=payload)
        return True

    def add_items_from_urls(self, items: List[EagleItemURLPayload], folder_id: Optional[str] = None) -> bool:
        """
        Add multiple images from URLs to the Eagle App sequentially.

        Args:
            items (List[EagleItemURLPayload]): An array composed of strongly typed EagleItemURLPayload objects.
            folder_id (Optional[str]): If provided, all images will be added to this specific folder ID.

        Returns:
            bool: True if the operation was successful.
        """
        payload_items = [item.to_dict() for item in items]
        payload = {"items": payload_items}
        
        if folder_id is not None:
            payload["folderId"] = folder_id
            
        self._make_request("/item/addFromURLs", method="POST", data=payload)
        return True

    def add_item_from_path(
        self,
        path: str,
        name: str,
        website: Optional[str] = None,
        tags: Optional[List[str]] = None,
        annotation: Optional[str] = None,
        folder_id: Optional[str] = None
    ) -> bool:
        """
        Add a local file to the Eagle App.

        Args:
            path (str): Required. The absolute path of the local file.
            name (str): Required. The name of the image/file in Eagle.
            website (Optional[str]): The source address/website of the image.
            tags (Optional[List[str]]): Tags for the image.
            annotation (Optional[str]): The annotation/notes for the image.
            folder_id (Optional[str]): ID of the folder to add the image to.

        Returns:
            bool: True if the operation was successful.
        """
        payload = {"path": path, "name": name}
        
        if website is not None:
            payload["website"] = website
        if tags is not None:
            payload["tags"] = tags
        if annotation is not None:
            payload["annotation"] = annotation
        if folder_id is not None:
            payload["folderId"] = folder_id

        self._make_request("/item/addFromPath", method="POST", data=payload)
        return True

    def add_items_from_paths(
        self,
        items: List[EagleItemPathPayload],
        folder_id: Optional[str] = None
    ) -> bool:
        """
        Add multiple local files to the Eagle App sequentially.

        Args:
            items (List[EagleItemPathPayload]): An array composed of strongly typed EagleItemPathPayload objects.
            folder_id (Optional[str]): If provided, all files will be added to this specific folder ID.

        Returns:
            bool: True if the operation was successful.
        """
        payload_items = [item.to_dict() for item in items]
        payload = {"items": payload_items}
        
        if folder_id is not None:
            payload["folderId"] = folder_id
            
        self._make_request("/item/addFromPaths", method="POST", data=payload)
        return True
