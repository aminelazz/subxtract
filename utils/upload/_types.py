"""Types for the upload utilities."""

from typing import NamedTuple, Optional, TypedDict

class UploadProgressTypeDict(TypedDict):
    """Type definition for upload progress data structure in dictionary form."""

    file_path: str
    """The path of the file being uploaded."""
    file_name: str
    """The name of the file being uploaded."""
    uploaded_size: int
    """The current uploaded size in bytes."""
    total_size: int
    """The total size of the file being uploaded in bytes."""
    percentage: float
    """The upload percentage (0.0 to 100.0)."""
    speed: float
    """The current speed in bytes per second."""
    eta: float
    """The estimated remaining time in seconds."""
    is_complete: bool
    """Whether the upload is complete or not."""
    total_formatted: str
    """The total size formatted as a human-readable string."""
    uploaded_formatted: str
    """The uploaded size formatted as a human-readable string."""
    speed_formatted: str
    """The speed formatted as a human-readable string."""
    eta_formatted: str
    """The estimated remaining time formatted as a human-readable string."""

class UploadProgressType(NamedTuple):
    """Type definition for upload progress data structure."""

    file_path: str
    """The path of the file being uploaded."""
    file_name: str
    """The name of the file being uploaded."""
    uploaded_size: int
    """The current uploaded size in bytes."""
    total_size: int
    """The total size of the file being uploaded in bytes."""
    percentage: float
    """The upload percentage (0.0 to 100.0)."""
    speed: float
    """The current speed in bytes per second."""
    eta: float
    """The estimated remaining time in seconds."""
    is_complete: bool
    """Whether the upload is complete or not."""
    total_formatted: str
    """The total size formatted as a human-readable string."""
    uploaded_formatted: str
    """The uploaded size formatted as a human-readable string."""
    speed_formatted: str
    """The speed formatted as a human-readable string."""
    eta_formatted: str
    """The estimated remaining time formatted as a human-readable string."""
    
    @classmethod
    def from_dict(cls, data: UploadProgressTypeDict) -> "UploadProgressType":
        """Builds the structure from raw data, converting each guild dict."""
        
        return cls(
            file_path=data.get("file_path", ""),
            file_name=data.get("file_name", ""),
            uploaded_size=data.get("uploaded_size", 0),
            total_size=data.get("total_size", 0),
            percentage=data.get("percentage", 0.0),
            speed=data.get("speed", 0.0),
            eta=data.get("eta", 0.0),
            is_complete=data.get("is_complete", False),
            total_formatted=data.get("total_formatted", ""),
            uploaded_formatted=data.get("uploaded_formatted", ""),
            speed_formatted=data.get("speed_formatted", ""),
            eta_formatted=data.get("eta_formatted", "")
        )

    @classmethod
    def to_dict(cls, instance: "UploadProgressType") -> UploadProgressTypeDict:
        """Converts the UploadProgressType to a dictionary."""
        return {
            "file_path": instance.file_path,
            "file_name": instance.file_name,
            "uploaded_size": instance.uploaded_size,
            "total_size": instance.total_size,
            "percentage": instance.percentage,
            "speed": instance.speed,
            "eta": instance.eta,
            "is_complete": instance.is_complete,
            "total_formatted": instance.total_formatted,
            "uploaded_formatted": instance.uploaded_formatted,
            "speed_formatted": instance.speed_formatted,
            "eta_formatted": instance.eta_formatted
        }

class UploadResult(NamedTuple):
    """Type definition for upload result data structure."""

    success: bool
    """Whether the upload was successful or not."""
    error_message: Optional[str] = None
    """Error message if the upload failed, otherwise None."""
    file_url: Optional[str] = None
    """The URL of the uploaded file, if available."""

#region ---- Gofile Upload Types ----
class GofileUploadDataDict(TypedDict, total=False):
    """Type definition for Gofile upload data in dictionary form."""

    code: str
    """The Gofile file/content code."""
    createTime: int
    """Timestamp when the file was created."""
    downloadPage: str
    """The page URL where the file can be downloaded."""
    guestToken: str
    """Guest token for managing the file."""
    id: str
    """Unique identifier of the uploaded file."""
    md5: str
    """MD5 checksum of the uploaded file."""
    mimetype: str
    """MIME type of the uploaded file."""
    modTime: int
    """Timestamp when the file was last modified."""
    name: str
    """Name of the uploaded file."""
    parentFolder: str
    """Identifier of the parent folder."""
    parentFolderCode: str
    """Code of the parent folder."""
    servers: list[str]
    """List of servers storing the file."""
    size: int
    """Size of the file in bytes."""
    type: str
    """Type of the uploaded content (e.g., 'file')."""

class GofileUploadResultDict(TypedDict, total=False):
    """Type definition for Gofile upload result in dictionary form."""

    status: str
    """Status returned by the API (e.g. 'ok')."""
    data: Optional[GofileUploadDataDict]
    """Data object containing upload details."""

class GofileUploadData(NamedTuple):
    """Type definition for Gofile upload file metadata."""

    code: str = ""
    """The Gofile file/content code."""
    create_time: int = 0
    """Timestamp when the file was created."""
    download_page: str = ""
    """The page URL where the file can be downloaded."""
    guest_token: str = ""
    """Guest token for managing the file."""
    id: str = ""
    """Unique identifier of the uploaded file."""
    md5: str = ""
    """MD5 checksum of the uploaded file."""
    mimetype: str = ""
    """MIME type of the uploaded file."""
    mod_time: int = 0
    """Timestamp when the file was last modified."""
    name: str = ""
    """Name of the uploaded file."""
    parent_folder: str = ""
    """Identifier of the parent folder."""
    parent_folder_code: str = ""
    """Code of the parent folder."""
    servers: list[str] = []
    """List of servers storing the file."""
    size: int = 0
    """Size of the file in bytes."""
    type: str = "file"
    """Type of the uploaded content (e.g., 'file')."""

    @classmethod
    def from_dict(cls, data: Optional["GofileUploadDataDict"]) -> "GofileUploadData":
        """Builds GofileUploadData from dictionary (handles both camelCase and snake_case)."""
        if not data:
            return cls()
        return cls(
            code=data.get("code", ""),
            create_time=data.get("createTime", data.get("create_time", 0)),
            download_page=data.get("downloadPage", data.get("download_page", "")),
            guest_token=data.get("guestToken", data.get("guest_token", "")),
            id=data.get("id", ""),
            md5=data.get("md5", ""),
            mimetype=data.get("mimetype", ""),
            mod_time=data.get("modTime", data.get("mod_time", 0)),
            name=data.get("name", ""),
            parent_folder=data.get("parentFolder", data.get("parent_folder", "")),
            parent_folder_code=data.get("parentFolderCode", data.get("parent_folder_code", "")),
            servers=list(data.get("servers", [])),
            size=data.get("size", 0),
            type=data.get("type", "file"),
        )

    def to_dict(self) -> GofileUploadDataDict:
        """Converts GofileUploadData to a dictionary."""
        return {
            "code": self.code,
            "createTime": self.create_time,
            "downloadPage": self.download_page,
            "guestToken": self.guest_token,
            "id": self.id,
            "md5": self.md5,
            "mimetype": self.mimetype,
            "modTime": self.mod_time,
            "name": self.name,
            "parentFolder": self.parent_folder,
            "parentFolderCode": self.parent_folder_code,
            "servers": self.servers,
            "size": self.size,
            "type": self.type,
        }

class GofileUploadResult(NamedTuple):
    """Type definition for Gofile upload result data structure."""

    status: str = ""
    """Status returned by the Gofile API (e.g., 'ok')."""
    data: Optional[GofileUploadData] = None
    """File metadata returned upon successful upload."""

    @property
    def success(self) -> bool:
        """Whether the upload was successful."""
        return self.status == "ok"

    @property
    def download_page(self) -> str:
        """Convenience property for the download page URL."""
        return self.data.download_page if self.data else ""

    @classmethod
    def from_dict(cls, data: GofileUploadResultDict) -> "GofileUploadResult":
        """Builds GofileUploadResult from raw API response dictionary."""
        status = data.get("status", "")
        raw_data = data.get("data")
        data_obj = GofileUploadData.from_dict(raw_data) if isinstance(raw_data, dict) else None
        return cls(status=status, data=data_obj)

    def to_dict(self) -> GofileUploadResultDict:
        """Converts GofileUploadResult to a dictionary."""
        return {
            "status": self.status,
            "data": self.data.to_dict() if self.data else None,
        }
#endregion ---- Gofile Upload Types ----

#region ---- Buzzheavier Upload Types ----
class BuzzheavierUploadDataDict(TypedDict, total=False):
    """Type definition for Buzzheavier upload data in dictionary form."""

    id: str
    """Unique identifier for the file on Buzzheavier."""
    name: str
    """Name of the uploaded file."""
    isDirectory: bool
    """Whether the item is a directory."""
    locationId: str
    """Location identifier for the file."""
    size: int
    """Size of the file in bytes."""
    expiry: str
    """ISO 8601 timestamp string indicating file expiration time."""
    views: int
    """Number of times the file has been viewed."""
    downloads: int
    """Number of times the file has been downloaded."""
    sha256: str
    """SHA-256 hash of the uploaded file."""
    md5: str
    """MD5 checksum of the uploaded file."""
    note: str
    """Optional note attached to the file."""
    createdAt: str
    """ISO 8601 timestamp string indicating creation time."""

class BuzzheavierUploadResultDict(TypedDict, total=False):
    """Type definition for Buzzheavier upload result in dictionary form."""

    code: int
    """HTTP status code returned by the API (e.g., 201)."""
    error: Optional[str]
    """Error message returned by the API, if any."""
    data: Optional[BuzzheavierUploadDataDict]
    """Data object containing upload details."""

class BuzzheavierUploadData(NamedTuple):
    """Type definition for Buzzheavier upload file metadata."""

    id: str = ""
    """Unique identifier for the file on Buzzheavier."""
    name: str = ""
    """Name of the uploaded file."""
    is_directory: bool = False
    """Whether the item is a directory."""
    location_id: str = ""
    """Location identifier for the file."""
    size: int = 0
    """Size of the file in bytes."""
    expiry: str = ""
    """ISO 8601 timestamp string indicating file expiration time."""
    views: int = 0
    """Number of times the file has been viewed."""
    downloads: int = 0
    """Number of times the file has been downloaded."""
    sha256: str = ""
    """SHA-256 hash of the uploaded file."""
    md5: str = ""
    """MD5 checksum of the uploaded file."""
    note: str = ""
    """Optional note attached to the file."""
    created_at: str = ""
    """ISO 8601 timestamp string indicating creation time."""

    @property
    def download_url(self) -> str:
        """The public download URL for the file."""
        return f"https://buzzheavier.com/{self.id}" if self.id else ""

    @classmethod
    def from_dict(cls, data: Optional[BuzzheavierUploadDataDict]) -> "BuzzheavierUploadData":
        """Builds BuzzheavierUploadData from dictionary (supports camelCase and snake_case)."""
        if not data:
            return cls()
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            is_directory=data.get("isDirectory", data.get("is_directory", False)),
            location_id=data.get("locationId", data.get("location_id", "")),
            size=data.get("size", 0),
            expiry=data.get("expiry", ""),
            views=data.get("views", 0),
            downloads=data.get("downloads", 0),
            sha256=data.get("sha256", ""),
            md5=data.get("md5", ""),
            note=data.get("note", ""),
            created_at=data.get("createdAt", data.get("created_at", "")),
        )

    def to_dict(self) -> BuzzheavierUploadDataDict:
        """Converts BuzzheavierUploadData to a dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "isDirectory": self.is_directory,
            "locationId": self.location_id,
            "size": self.size,
            "expiry": self.expiry,
            "views": self.views,
            "downloads": self.downloads,
            "sha256": self.sha256,
            "md5": self.md5,
            "note": self.note,
            "createdAt": self.created_at,
        }

class BuzzheavierUploadResult(NamedTuple):
    """Type definition for Buzzheavier upload result data structure."""

    code: int = 0
    """HTTP status code returned by the API (e.g., 201)."""
    error: Optional[str] = None
    """Error message returned by the API, if any."""
    data: Optional[BuzzheavierUploadData] = None
    """Data object containing upload details."""

    @property
    def success(self) -> bool:
        """Whether the upload was successful (HTTP 2xx code)."""
        return 200 <= self.code < 300

    @property
    def download_url(self) -> str:
        """Convenience property for the download URL."""
        return self.data.download_url if self.data else ""

    @property
    def file_id(self) -> str:
        """Convenience property for the file ID."""
        return self.data.id if self.data else ""

    @classmethod
    def from_dict(cls, data: BuzzheavierUploadResultDict) -> "BuzzheavierUploadResult":
        """Builds BuzzheavierUploadResult from raw API response dictionary."""
        code = data.get("code", 0)
        error = data.get("error")
        raw_data = data.get("data")
        data_obj = BuzzheavierUploadData.from_dict(raw_data) if isinstance(raw_data, dict) else None
        return cls(code=code, error=error, data=data_obj)

    def to_dict(self) -> BuzzheavierUploadResultDict:
        """Converts BuzzheavierUploadResult to a dictionary."""
        return {
            "code": self.code,
            "error": self.error,
            "data": self.data.to_dict() if self.data else None,
        }
#endregion ---- Buzzheavier Upload Types ----
