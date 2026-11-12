"""FastAPI aria2 torrent file-selection interface."""

from __future__ import annotations

import logging
import re
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import aiohttp
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates

from config import ARIA2_RPC_HOST, ARIA2_RPC_PORT, ARIA2_RPC_SECRET
from web import nodes

logger = logging.getLogger("web.server")
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
MAX_DOWNLOAD_SIZE = 20 * 1024 * 1024 * 1024


class Aria2RpcError(RuntimeError):
    """Raised when aria2 returns an RPC or transport error."""


class Aria2RpcClient:
    """Minimal asynchronous JSON-RPC client for aria2."""

    def __init__(self) -> None:
        host = ARIA2_RPC_HOST.rstrip("/")
        if re.search(r":\d+$", host):
            self.url = f"{host}/jsonrpc"
        else:
            self.url = f"{host}:{ARIA2_RPC_PORT}/jsonrpc"
        self.session: aiohttp.ClientSession | None = None

    async def open(self) -> None:
        self.session = aiohttp.ClientSession()

    async def close(self) -> None:
        if self.session is not None:
            await self.session.close()
            self.session = None

    async def call(self, method: str, *arguments: Any) -> Any:
        if self.session is None:
            raise Aria2RpcError("aria2 client is not available")

        params = list(arguments)
        if ARIA2_RPC_SECRET:
            params.insert(0, f"token:{ARIA2_RPC_SECRET}")
        payload = {"jsonrpc": "2.0", "id": "subxtract-web", "method": method, "params": params}
        try:
            async with self.session.post(self.url, json=payload) as response:
                response.raise_for_status()
                body = await response.json()
        except (aiohttp.ClientError, ValueError) as exc:
            raise Aria2RpcError(f"aria2 request failed: {exc}") from exc

        if "error" in body:
            error = body["error"]
            raise Aria2RpcError(
                f"aria2 RPC error {error.get('code')}: {error.get('message')}"
            )
        return body.get("result")

    async def getFiles(self, gid: str) -> list[dict[str, Any]]:
        return await self.call("aria2.getFiles", gid)

    async def getOption(self, gid: str) -> dict[str, Any]:
        return await self.call("aria2.getOption", gid)

    async def changeOption(self, gid: str, options: dict[str, str]) -> Any:
        return await self.call("aria2.changeOption", gid, options)

    async def resume(self, gid: str) -> Any:
        return await self.call("aria2.unpause", gid)


def _validate_pin(gid: str, pin: str) -> None:
    if not gid or not pin:
        raise HTTPException(status_code=400, detail="gid and pin are required.")
    numeric = "".join(character for character in gid if character.isdigit())
    if len(numeric) < 4 or pin != numeric[:4]:
        raise HTTPException(status_code=403, detail="Invalid PIN.")


def _selected_size(data: Any) -> int:
    """Calculate the selected file size from the submitted aria2 tree."""
    if isinstance(data, list):
        return sum(_selected_size(item) for item in data)
    if not isinstance(data, dict):
        return 0
    if data.get("type") == "file" and data.get("selected") is True:
        try:
            size = int(data.get("size", 0))
        except (TypeError, ValueError) as exc:
            raise ValueError("Selected file sizes must be integers.") from exc
        if size < 0:
            raise ValueError("Selected file sizes cannot be negative.")
        return size
    if data.get("type") == "folder":
        return _selected_size(data.get("children", []))
    return 0


@asynccontextmanager
async def lifespan(app: FastAPI):
    client = Aria2RpcClient()
    await client.open()
    app.state.aria2 = client
    try:
        yield
    finally:
        await client.close()


app = FastAPI(title="Subxtract aria2 file selection", lifespan=lifespan)


@app.get("/app/files")
async def files_page(request: Request):
    return templates.TemplateResponse(request=request, name="page.html")


@app.get("/app/files/torrent")
async def get_torrent_files(
    request: Request,
    gid: str = Query(""),
    pin: str = Query(""),
    mode: str = Query("get"),
):
    del request
    if mode != "get":
        raise HTTPException(status_code=400, detail="mode must be get.")
    _validate_pin(gid, pin)
    try:
        aria2: Aria2RpcClient = app.state.aria2
        file_info = await aria2.getFiles(gid)
        options = await aria2.getOption(gid)
        root_path = str(options.get("dir", ""))
        if not root_path:
            raise Aria2RpcError("aria2 did not return a download directory")
        tree = nodes.make_tree(file_info, root_path)
        return {"files": nodes.create_list(tree), "engine": "aria2", "error": False, "message": ""}
    except (Aria2RpcError, ValueError) as exc:
        logger.exception("Could not retrieve aria2 files for gid %s", gid)
        return JSONResponse(
            status_code=502,
            content={"files": [], "engine": "aria2", "error": True, "message": str(exc)},
        )


@app.post("/app/files/torrent")
async def submit_torrent_selection(
    request: Request,
    gid: str = Query(""),
    pin: str = Query(""),
    mode: str = Query("selection"),
):
    if mode != "selection":
        raise HTTPException(status_code=400, detail="mode must be selection.")
    _validate_pin(gid, pin)
    try:
        data = await request.json()
        selected, unselected = nodes.extract_file_ids(data)
        if not selected:
            raise HTTPException(status_code=400, detail="Select at least one file.")
        if set(selected) & set(unselected):
            raise ValueError("A file cannot be both selected and unselected.")
        if _selected_size(data) > MAX_DOWNLOAD_SIZE:
            raise HTTPException(
                status_code=400,
                detail="The selected files exceed the 20 GB download limit.",
            )
        await app.state.aria2.changeOption(gid, {"select-file": ",".join(map(str, selected))})
        await app.state.aria2.resume(gid)
        return {
            "engine": "aria2",
            "error": False,
            "message": "Your selection has been submitted successfully.",
        }
    except HTTPException:
        raise
    except (Aria2RpcError, ValueError, TypeError) as exc:
        logger.exception("Could not apply aria2 selection for gid %s", gid)
        return JSONResponse(
            status_code=502,
            content={"engine": "aria2", "error": True, "message": str(exc)},
        )
