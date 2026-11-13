"""Type definitions for file utility data structures."""

from typing import NamedTuple, Self

class AllowedChannelsType(NamedTuple):
    """Type definition for allowed channels data structure."""

    allowed_channels: list["GuildObject"] = []
    """All allowed channels, grouped by guild."""

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        """Builds the structure from raw data, converting each guild dict."""
        return cls(
            allowed_channels=list(
                GuildObject(**guild) for guild in data.get("allowed_channels", [])
            )
        )

    def to_dict(self) -> dict:
        """Converts the AllowedChannelsType to a dictionary."""
        return {
            "allowed_channels": [guild.to_dict() for guild in self.allowed_channels]
        }

class GuildObject(NamedTuple):
    """Type definition for guild object in allowed channels."""

    guild: str = ""
    """The guild ID."""
    channels: list[str] = []
    """The list of allowed channels."""

    def to_dict(self) -> dict:
        """Converts the GuildObject to a dictionary."""
        return {
            "guild": self.guild,
            "channels": self.channels
        }

class CurrentDLObject(NamedTuple):
    """Type definition for current download object."""

    gid: str = ""
    """The GID of the download."""
    user_id: str = ""
    """The user ID associated with the download."""
    guild_id: str = ""
    """The guild ID associated with the download."""

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        """Builds the structure from raw data, converting each guild dict."""
        return cls(
            gid=data.get("gid", ""),
            user_id=data.get("user_id", ""),
            guild_id=data.get("guild_id", "")
        )

    def to_dict(self) -> dict[str, str]:
        """Converts the CurrentDLObject to a dictionary."""
        return {
            "gid": self.gid,
            "user_id": self.user_id,
            "guild_id": self.guild_id
        }

class QueueItem(NamedTuple):
    """Type definition for a single queue item with link and extraction type."""

    link: str = ""
    """The link associated with the queue item."""
    type: str = "all_without_audio"
    """The extraction type associated with the queue item."""

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        """Builds the structure from raw data, converting each guild dict."""
        return cls(
            link=data.get("link", ""),
            type=data.get("type", "all_without_audio")
        )

    def to_dict(self) -> dict[str, str]:
        """Converts the QueueItem to a dictionary."""
        return {
            "link": self.link,
            "type": self.type
        }

class QueueObject(NamedTuple):
    """Type definition for queue object."""

    user_id: str = ""
    """The user ID associated with the queue."""
    links: list[str] | list[QueueItem] = []
    """A list of links associated with the queue, can be in old or new format."""
    links_dict: list[QueueItem] = []
    """A list of QueueItem objects associated with the queue, always in new format."""

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        """Builds the structure from raw data, converting each guild dict."""
        return cls(
            user_id=data.get("user_id", ""),
            links=data.get("links", []),
            links_dict=cls._normalize_links(data.get("links", [])),
        )

    @staticmethod
    def _normalize_links(links: list[str] | list[QueueItem]) -> list[QueueItem]:
        """Converts links to new format {link, type} if needed."""
        normalized: list[QueueItem] = []
        for item in links:
            if isinstance(item, str):
                # Old format: just a link string
                normalized.append(QueueItem(link=item, type="all_without_audio"))
            elif isinstance(item, QueueItem):
                # New format: already a QueueItem
                normalized.append(QueueItem(link=item.link, type=item.type))
        return normalized

    def to_dict(self) -> dict[str, str | list]:
        """Converts the QueueObject to a dictionary."""
        return {
            "user_id": self.user_id,
            "links": [item.to_dict() for item in self.links_dict]
        }
