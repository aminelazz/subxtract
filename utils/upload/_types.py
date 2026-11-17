"""Types for the upload utilities."""

from typing import NamedTuple, TypedDict

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