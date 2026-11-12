"""Tree helpers for aria2 torrent file selection."""

from __future__ import annotations

import os
from pathlib import PurePath
from typing import Any


class TorNode:
    """A folder or file from an aria2 download."""

    def __init__(
        self,
        name: str,
        *,
        is_folder: bool,
        parent: TorNode | None = None,
        size: int = 0,
        priority: str = "",
        file_id: int | None = None,
        progress: float = 0,
        selected: bool = False,
    ) -> None:
        self.name = name
        self.is_folder = is_folder
        self.is_file = not is_folder
        self.parent = parent
        self.size = size
        self.priority = priority
        self.file_id = file_id
        self.progress = progress
        self.selected = selected
        self.children: list[TorNode] = []


def get_folders(path: str, root_path: str) -> list[str]:
    """Return path components below the aria2 download directory."""
    normalized_path = os.path.normpath(path)
    normalized_root = os.path.normpath(root_path)

    try:
        relative = os.path.relpath(normalized_path, normalized_root)
    except ValueError:
        relative = normalized_path

    if relative == os.curdir or relative == os.pardir or relative.startswith(
        os.pardir + os.sep
    ):
        relative = normalized_path.lstrip("/\\")

    return [part for part in PurePath(relative.replace("\\", "/")).parts if part not in (".", "")]


def _number(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def make_tree(res: list[dict[str, Any]], root_path: str) -> TorNode:
    """Build a nested node tree from the result of aria2.getFiles."""
    root = TorNode("", is_folder=True)

    for file_info in res:
        path = str(file_info.get("path", ""))
        parts = get_folders(path, root_path)
        if not parts:
            continue

        parent = root
        for folder_name in parts[:-1]:
            child = next(
                (node for node in parent.children if node.is_folder and node.name == folder_name),
                None,
            )
            if child is None:
                child = TorNode(folder_name, is_folder=True, parent=parent)
                parent.children.append(child)
            parent = child

        length = _number(file_info.get("length"))
        completed = _number(file_info.get("completedLength"))
        progress = (completed / length * 100) if length else 0
        file_node = TorNode(
            parts[-1],
            is_folder=False,
            parent=parent,
            size=length,
            priority=str(file_info.get("priority", "")),
            file_id=_number(file_info.get("index"), -1),
            progress=min(100, max(0, progress)),
            selected=str(file_info.get("selected", "")).lower() == "true",
        )
        parent.children.append(file_node)

    return root


def create_list(parent: TorNode) -> list[dict[str, Any]]:
    """Convert a node's children to JSON-compatible dictionaries."""
    result: list[dict[str, Any]] = []
    for node in parent.children:
        if node.is_folder:
            result.append(
                {
                    "id": f"folderNode_{id(node)}",
                    "name": node.name,
                    "type": "folder",
                    "children": create_list(node),
                }
            )
        else:
            result.append(
                {
                    "id": node.file_id,
                    "name": node.name,
                    "size": node.size,
                    "type": "file",
                    "selected": node.selected,
                    "progress": round(node.progress, 2),
                }
            )
    return result


def extract_file_ids(data: Any) -> tuple[list[int], list[int]]:
    """Return selected and unselected aria2 file indexes from a submitted tree."""
    selected: list[int] = []
    unselected: list[int] = []

    def visit(node: Any) -> None:
        if isinstance(node, list):
            for child in node:
                visit(child)
            return
        if not isinstance(node, dict):
            return

        if node.get("type") == "file":
            file_id = node.get("id")
            if isinstance(file_id, bool) or not isinstance(file_id, int) or file_id < 0:
                raise ValueError("File nodes must contain a non-negative integer id.")
            (selected if node.get("selected") is True else unselected).append(file_id)
            return

        if node.get("type") == "folder":
            children = node.get("children")
            if not isinstance(children, list):
                raise ValueError("Folder nodes must contain a children list.")
            for child in children:
                visit(child)

    visit(data)
    return selected, unselected
