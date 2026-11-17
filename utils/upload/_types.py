"""Types for the upload utilities."""

from typing import Any, Dict, NamedTuple, Optional, TypedDict

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
    file_url: Optional[str]
    """The URL of the uploaded file, if available."""

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
