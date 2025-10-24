"""Utils functions for the bot."""

import asyncio
import os
import logging
from pathlib import Path
from typing import Literal

from interactions import File
from interactions import Message, SlashContext

from utils import aria2_service, file_utils, mkv_service
from utils.controller import extraction_cancel_event
from utils.logger import get_logger

def get_download_status_message(status: dict, gid: str) -> str:
    """Generates a status message for a download."""
    return (
        f"┏**{status['name']}**\n"
        f"┠**Progress:** {status['progress']}\n"
        f"┠**GID:** `{gid}`\n"
        f"┠**Processed:** {status.get('downloaded_size', '0B')} of {status.get('full_size', '0B')}\n"
        f"┠**Status:** {status['status']}\n"
        f"┠**Speed:** {status.get('speed', 'N/A')}\n"
        f"┠**Seeders:** {status.get('seeders', 'N/A')}\n"
        f"┠**Total Files:** {status.get('num_files', 'N/A')}\n"
        f"┖**ETA:** {status.get('eta', 'N/A')}"
    )

def remove_duplicates_preserve_order(links: list[str]) -> list[str]:
    """Removes duplicate links while preserving the original order."""
    unique_links = []
    for link in links:
        if link.strip() not in unique_links:
            unique_links.append(link.strip())
    return unique_links

def get_merge_commands(files: list[Path], type: Literal["subs", "attachments"]) -> str:
    """Generates mkvmerge commands for merging subtitles and attachments."""
    separated_by_plus_sign = " + ".join([f'"{os.path.basename(file)}"' for file in files])
    separated_by_space = " ".join([f'"{os.path.basename(file)}"' for file in files])

    windows_command = f'copy /b {separated_by_plus_sign} {type}.zip'
    unix_command = f'cat {separated_by_space} > {type}.zip'

    return (
        f"To merge the {type} into a single zip file, use the following commands:\n\n"
        f"```Windows:\n{windows_command}\n\n"
        f"```Unix:\n{unix_command}```"
    )

# Check if the command has been run in the allowed channel
async def is_allowed_channel(ctx: SlashContext) -> bool:
    """Checks if the command is run in an allowed channel."""
    guild_id = str(ctx.guild_id)
    channel_id = str(ctx.channel_id)
    allowed_channels_data = file_utils.load_allowed_channels()
    if allowed_channels_data is None:
        return False  # If no allowed channels file, disallow by default

    guild_obj = next(
        (g for g in allowed_channels_data.allowed_channels if g.guild == guild_id),
        None
    )
    if guild_obj is not None:
        return channel_id in guild_obj.channels
    return False

async def download_file(gid: str, ctx: SlashContext, message: Message) -> bool | None:
    """Downloads a file and tracks its progress."""
    # Configure logging
    logger = get_logger("downloader")

    file_utils.save_current_dl(gid=gid, user_id=str(ctx.author.id), guild_id=str(ctx.guild_id))
    try:
        progress = aria2_service.track_progress(gid)
        try:
            status = next(progress)
        except StopIteration:
            return True
        # Check for errors in status
        if status["status"] == "error":
            await message.edit(
                content=f"Download error: {status.get('error', 'Unknown error')}"
            )
            logger.error("Download error: %s", status.get('error', 'Unknown error'))
            aria2_service.remove_all_downloads(force=True)
            file_utils.clear_current_dl()
            file_utils.clear_temp()
            return False
        await message.edit(
            content=get_download_status_message(status, gid)
        )
        if status["status"] == "complete":
            logger.info("Download completed successfully.")
            return True
        await asyncio.sleep(2)
    except Exception as e:
        await ctx.send(f"An error occurred while tracking progress: {e}")
        logger.error("An error occurred while tracking progress: %s", e)
        aria2_service.remove_all_downloads(force=True)
        file_utils.clear_current_dl()
        file_utils.clear_temp()
        return False

async def extract_from_download(gid: str, ctx: SlashContext, message: Message, dir_path: Path, event = extraction_cancel_event) -> str | None:
    """Extracts files from the downloaded archive."""
    # Configure logging
    logger = get_logger("extractor")

    logger.info("Starting extraction of Matroska files from download with GID: %s", gid)
    all_files_dict = file_utils.get_temp_files(dir_path)
    files = all_files_dict["filenames"] if all_files_dict else []
    full_paths = all_files_dict["full_paths"] if all_files_dict else []
    # Check if there are any matroska files to extract
    if not files:
        await ctx.send("No Matroska files (.mkv, .mk3d, .mka) found for extraction.")
        logger.warning("No Matroska files found for extraction, Extraction aborted.")
        aria2_service.remove_all_downloads(force=True)
        file_utils.clear_current_dl()
        file_utils.clear_temp()
        return
    # Send list of files to be processed
    all_files_str = "\n- ".join(files)
    await ctx.send(
        f"Files List:\n"
        f"```- {all_files_str}```"
    )

    # Perform extraction
    for i, file in enumerate(full_paths, start=1):
        # Check for cancellation
        if event.is_set():
            aria2_service.remove_all_downloads(force=True)
            file_utils.clear_current_dl()
            file_utils.clear_temp()
            await ctx.send("Extraction has been cancelled.")
            logger.info("Extraction for download with GID: %s has been cancelled.", gid)
            return
        logger.info("Processing (%d/%d)", i, len(full_paths))
        message = await ctx.send(f"Processing file ({i}/{len(full_paths)})...")
        try:
            mkv_service_class = mkv_service.MKVService()
            mkv_info = mkv_service_class.get_mkv_info(file)
            mkv_info_path = file_utils.save_file_to_extract_dir(mkv_info.encode("utf-8"), "mkv_info.txt")
            zipped_subs = mkv_service_class.extract_subtitles(file)
            zipped_attachments = mkv_service_class.extract_attachments(file)
            chapters = mkv_service_class.extract_chapters(file)

            # Files' paths to send
            files=[
                mkv_info_path,
                chapters.get("path") if chapters else None
            ]
            files.extend(zipped_subs.paths if zipped_subs else [])
            files.extend(zipped_attachments.paths if zipped_attachments else [])
            logger.info("Finished processing MKV file, Uploading results...")
            await message.edit(content="Uploading results...")
            await message.edit(
                content=
                    f"`{os.path.basename(file)}`\n"
                    f"```Subtitles: {zipped_subs.count if zipped_subs else 0}\n"
                    f"Attachments: {zipped_attachments.count if zipped_attachments else 0}\n"
                    f"Chapters: {chapters.get('count') if chapters else 0}```\n"
                    f"{get_merge_commands(zipped_subs.paths, 'subs') if zipped_subs and len(zipped_subs.paths) > 1 else ''}\n"
                    f"{get_merge_commands(zipped_attachments.paths, 'attachments') if zipped_attachments and len(zipped_attachments.paths) > 1 else ''}",
                files=[File(file=f, file_name=os.path.basename(f)) for f in files if f is not None]
            )
            logger.info("Finished upload results for: %s", os.path.basename(file))
        except Exception as e:
            await ctx.send(f"An error occurred while extracting MKV info from `{os.path.basename(file)}`: {e}")
            logger.error("An error occurred while extracting MKV info from %s: %s", os.path.basename(file), e)
            continue
        file_utils.clear_extract_dir()

async def download_and_extract(ctx: SlashContext, url: str) -> bool:
    """Combined download and extraction process."""
    # Reset cancellation event
    extraction_cancel_event.clear()

    # Configure logging
    logger = get_logger("download_and_extractor")

    try:
        #region Initial checks
        connection_established = aria2_service.check_connection()
        if not connection_established:
            await ctx.send("Error: Unable to connect to Aria2 RPC server.")
            return False

        if file_utils.load_current_dl():
            await ctx.send("A download is already in progress. Please wait for it to finish or cancel it before starting a new one.")
            logger.warning("Download attempt rejected while another download is in progress.")
            return False
        #endregion

        #region ---- Stage 1: Download ----
        message = await ctx.send("Starting download...")
        gid = aria2_service.add_torrent(url)
        await message.edit(content=f"Added download with GID: `{gid}`")
        logger.info("Started download with GID: %s", gid)

        #region Track METADATA/DDL links progress
        status = aria2_service.get_status(gid)
        while True:
            # Check for cancellation
            if extraction_cancel_event.is_set():
                aria2_service.remove_all_downloads(force=True)
                file_utils.clear_current_dl()
                file_utils.clear_temp()
                await message.edit(content="Download has been cancelled.")
                logger.info("Download with GID: %s has been cancelled.", gid)
                return False
            # Check if complete
            completed = await download_file(gid, ctx, message)
            if completed is True:
                break
            if completed is False:
                return False
        #endregion

        #region Verify completion
        try:
            status = aria2_service.get_status(gid)
            if status["status"] != "complete":
                await ctx.send(f"Download failed or incomplete. Current status: {status['status']}")
                logger.error("Download failed or incomplete. Current status: %s", status['status'])
                aria2_service.remove_all_downloads(force=True)
                file_utils.clear_current_dl()
                file_utils.clear_temp()
                return False
        except Exception as e:
            await ctx.send(f"An error occurred while verifying download: {e}")
            logger.error("An error occurred while verifying download: %s", e)
            aria2_service.remove_all_downloads(force=True)
            file_utils.clear_current_dl()
            file_utils.clear_temp()
            return False
        #endregion

        #region Torrent download
        if status["followed_by_ids"]:
            try:
                # Check for cancellation
                if extraction_cancel_event.is_set():
                    aria2_service.remove_all_downloads(force=True)
                    file_utils.clear_current_dl()
                    file_utils.clear_temp()
                    await message.edit(content="Torrent download has been cancelled.")
                    logger.info("Torrent download with GID: %s has been cancelled.", gid)
                    return False
                gid = status["followed_by_ids"][0]
                message = await ctx.send(f"Metadata downloaded. New GID: `{gid}`")
                logger.info("Metadata downloaded, starting following download with GID: %s", gid)
                status = aria2_service.get_status(gid)
                #region Track Torrent progress
                while status["status"] != "complete":
                    # Check for cancellation
                    if extraction_cancel_event.is_set():
                        aria2_service.remove_all_downloads(force=True)
                        file_utils.clear_current_dl()
                        file_utils.clear_temp()
                        await message.edit(content="Download has been cancelled.")
                        logger.info("Download with GID: %s has been cancelled.", gid)
                        return False
                    
                    # Check if complete
                    completed = await download_file(gid, ctx, message)
                    if completed is True:
                        break
                    if completed is False:
                        return False
            #endregion
            except Exception as e:
                await ctx.send(f"An error occurred while downloading file: {e}")
                logger.error("An error occurred while downloading file: %s", e)
                aria2_service.remove_all_downloads(force=True)
                file_utils.clear_current_dl()
                file_utils.clear_temp()
                return False
        #endregion

        dir_path = aria2_service.wait_for_completion(gid)
        await message.edit(content=f"Download complete! Saved to `{dir_path}`", components=[])
        logger.info("Download with GID: %s completed and saved to %s", gid, dir_path)
        #endregion

        #region ---- Stage 2: Extraction ----
        await extract_from_download(gid=gid, ctx=ctx, message=message, dir_path=dir_path)
        return True
    except Exception as e:
        await ctx.send(f"An unexpected error occurred: {e}")
        logger.error("An unexpected error occurred: %s", e)
        return False
