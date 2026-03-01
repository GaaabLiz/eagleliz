import json
import urllib.request
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
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

@dataclass
class EagleItem:
    """
    Represents an Item returned by the Eagle App API.
    Handles known properties explicitly while gracefully keeping extra fields mapped in future API versions.
    """
    id: str
    name: str
    ext: str
    url: str
    annotation: str
    tags: List[str]
    folders: List[str]
    size: int
    isDeleted: bool
    modificationTime: int
    lastModified: int
    noThumbnail: bool
    width: int
    height: int
    palettes: List[Dict[str, Any]]
    star: int
    _extra_data: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EagleItem":
        """
        Create an EagleItem object from a dictionary, capturing any unknown fields safely in _extra_data.
        """
        known_fields = {
            "id", "name", "ext", "url", "annotation", "tags", "folders", 
            "size", "isDeleted", "modificationTime", "lastModified", "noThumbnail", 
            "width", "height", "palettes", "star"
        }
        
        kwargs = {}
        extra_data = {}
        
        for key, value in data.items():
            if key in known_fields:
                kwargs[key] = value
            else:
                extra_data[key] = value
                
        # Ensure lists are cleanly parsed even if they arrive as None
        kwargs["tags"] = kwargs.get("tags") or []
        kwargs["folders"] = kwargs.get("folders") or []
        kwargs["palettes"] = kwargs.get("palettes") or []
        
        # Populate defaults for missing required primitive keys gracefully
        kwargs.setdefault("id", "")
        kwargs.setdefault("name", "")
        kwargs.setdefault("ext", "")
        kwargs.setdefault("url", "")
        kwargs.setdefault("annotation", "")
        kwargs.setdefault("size", 0)
        kwargs.setdefault("isDeleted", False)
        kwargs.setdefault("modificationTime", 0)
        kwargs.setdefault("lastModified", 0)
        kwargs.setdefault("noThumbnail", False)
        kwargs.setdefault("width", 0)
        kwargs.setdefault("height", 0)
        kwargs.setdefault("star", 0)

        kwargs["_extra_data"] = extra_data
        
        return cls(**kwargs)

@dataclass
class LibraryInfo:
    """Dataclass representing the current library information."""
    folders: List[EagleFolder]
    smartFolders: List[Dict[str, Any]]
    quickAccess: List[Dict[str, Any]]
    tagsGroups: List[Dict[str, Any]]
    modificationTime: int
    applicationVersion: str
    _extra_data: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict) -> 'LibraryInfo':
        """Constructs a LibraryInfo from a raw dictionary."""
        folders_data = data.get('folders', [])
        folders = [EagleFolder.from_dict(f) for f in folders_data]
        
        known_fields = {'folders', 'smartFolders', 'quickAccess', 'tagsGroups', 'modificationTime', 'applicationVersion'}
        kwargs = {k: v for k, v in data.items() if k in known_fields and k != 'folders'}
        kwargs['folders'] = folders
        kwargs.setdefault('smartFolders', [])
        kwargs.setdefault('quickAccess', [])
        kwargs.setdefault('tagsGroups', [])
        kwargs.setdefault('modificationTime', 0)
        kwargs.setdefault('applicationVersion', '')
        
        extra_data = {k: v for k, v in data.items() if k not in known_fields}
        return cls(**kwargs, _extra_data=extra_data)

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

    # -------------------------------------------------------------------------
    # LIBRARY ENDPOINTS
    # -------------------------------------------------------------------------

    def get_library_info(self) -> LibraryInfo:
        """
        Get detailed information of the library currently running.
        
        Returns:
            LibraryInfo: An object containing folders, smart folders, quick access, etc.
        """
        data = self._make_request("/library/info")
        return LibraryInfo.from_dict(data)

    def get_library_history(self) -> List[str]:
        """
        Get the list of libraries recently opened by the Application.
        
        Returns:
            List[str]: A list containing paths to recently opened libraries.
        """
        data = self._make_request("/library/history")
        # Ensure it returns a list of strings
        if isinstance(data, list):
            return data
        return []

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

    def add_bookmark(
        self,
        url: str,
        name: str,
        base64: Optional[str] = None,
        tags: Optional[List[str]] = None,
        modificationTime: Optional[int] = None,
        folder_id: Optional[str] = None
    ) -> bool:
        """
        Save a link in URL form to the Eagle App as a bookmark.

        Args:
            url (str): Required. The link of the page to be saved.
            name (str): Required. The name of the bookmark.
            base64 (Optional[str]): The thumbnail of the bookmark. Must be a base64 encoded image string.
            tags (Optional[List[str]]): Tags for the bookmark.
            modificationTime (Optional[int]): The creation date of the bookmark.
            folder_id (Optional[str]): ID of the folder to add the bookmark to.

        Returns:
            bool: True if the operation was successful.
        """
        payload = {"url": url, "name": name}
        
        if base64 is not None:
            payload["base64"] = base64
        if tags is not None:
            payload["tags"] = tags
        if modificationTime is not None:
            payload["modificationTime"] = modificationTime
        if folder_id is not None:
            payload["folderId"] = folder_id

        self._make_request("/item/addBookmark", method="POST", data=payload)
        return True

    def move_to_trash(self, item_ids: List[str]) -> bool:
        """
        Move items to the trash.

        Args:
            item_ids (List[str]): Required. A list of item IDs to be moved to the trash.

        Returns:
            bool: True if the moving was successful.
        """
        payload = {"itemIds": item_ids}
        self._make_request("/item/moveToTrash", method="POST", data=payload)
        return True

    def update_item(
        self,
        item_id: str,
        tags: Optional[List[str]] = None,
        annotation: Optional[str] = None,
        url: Optional[str] = None,
        star: Optional[int] = None
    ) -> EagleItem:
        """
        Modify specific metadata fields of an item.

        Args:
            item_id (str): Required. ID of the item to be modified.
            tags (Optional[List[str]]): An array of strings representing tags to assign.
            annotation (Optional[str]): A string representing the annotation/note for the item.
            url (Optional[str]): The source url of the item.
            star (Optional[int]): The rating between 1 and 5.

        Returns:
            EagleItem: An object reflecting the updated state of the item.
        """
        payload: Dict[str, Any] = {"id": item_id}
        
        if tags is not None:
            payload["tags"] = tags
        if annotation is not None:
            payload["annotation"] = annotation
        if url is not None:
            payload["url"] = url
        if star is not None:
            payload["star"] = star
            
        data = self._make_request("/item/update", method="POST", data=payload)
        return EagleItem.from_dict(data)

    def refresh_item_palette(self, item_id: str) -> bool:
        """
        Re-analyze the colors of a file updating its palette.

        Args:
            item_id (str): Required. ID of the file.

        Returns:
            bool: True if the refresh request succeeded.
        """
        payload = {"id": item_id}
        self._make_request("/item/refreshPalette", method="POST", data=payload)
        return True

    def refresh_item_thumbnail(self, item_id: str) -> bool:
        """
        Re-generate the thumbnail of a file used in the list view.
        (Color analysis will also be implicitly refreshed).

        Args:
            item_id (str): Required. ID of the file.

        Returns:
            bool: True if the refresh request succeeded.
        """
        payload = {"id": item_id}
        self._make_request("/item/refreshThumbnail", method="POST", data=payload)
        return True

    # -------------------------------------------------------------------------
    # ITEM READ ENDPOINTS
    # -------------------------------------------------------------------------

    def get_item_info(self, item_id: str) -> EagleItem:
        """
        Get properties of the specified file, including the file name, tags, categorizations, folders, dimensions, etc.

        Args:
            item_id (str): Required. ID of the file.

        Returns:
            EagleItem: An object containing all the metadata of the file.
        """
        data = self._make_request(f"/item/info?id={item_id}")
        return EagleItem.from_dict(data)

    def get_item_thumbnail(self, item_id: str) -> str:
        """
        Get the absolute file system path of the thumbnail for the specified file.

        Args:
            item_id (str): Required. ID of the file.

        Returns:
            str: The absolute path pointing to the thumbnail image on disk.
        """
        data = self._make_request(f"/item/thumbnail?id={item_id}")
        return str(data)

    def get_items(
        self,
        limit: int = 200,
        offset: int = 0,
        order_by: Optional[str] = None,
        keyword: Optional[str] = None,
        ext: Optional[str] = None,
        tags: Optional[List[str]] = None,
        folders: Optional[List[str]] = None
    ) -> List[EagleItem]:
        """
        Get a list of items that match the specified filter conditions.

        Args:
            limit (int): The number of items to be displayed. Defaults to 200.
            offset (int): Offset a collection of results from the api. Defaults to 0.
            order_by (Optional[str]): The sorting order. Options include 'CREATEDATE', 'FILESIZE', 'NAME', 'RESOLUTION'. Prefix with '-' for descending, e.g., '-FILESIZE'.
            keyword (Optional[str]): Filter by keyword.
            ext (Optional[str]): Filter by the extension type, e.g., 'jpg', 'png'.
            tags (Optional[List[str]]): Filter by tags.
            folders (Optional[List[str]]): Filter by Folders by passing their IDs.

        Returns:
            List[EagleItem]: A list of objects matching the filter.
        """
        query_parts = []
        query_parts.append(f"limit={limit}")
        query_parts.append(f"offset={offset}")
        
        if order_by:
            query_parts.append(f"orderBy={order_by}")
        if keyword:
            # properly urlencode the keyword
            encoded_keyword = urllib.parse.quote(keyword)
            query_parts.append(f"keyword={encoded_keyword}")
        if ext:
            query_parts.append(f"ext={ext}")
        if tags:
            # Eagle expects comma-separated values for tags
            query_parts.append(f"tags={','.join(tags)}")
        if folders:
            # Eagle expects comma-separated values for folder IDs
            query_parts.append(f"folders={','.join(folders)}")

        query_string = "&".join(query_parts)
        data = self._make_request(f"/item/list?{query_string}")
        return [EagleItem.from_dict(item) for item in data]
