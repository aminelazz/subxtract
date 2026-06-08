"""MKV service module for handling MKV file operations."""

import subprocess
import os
import json
from pathlib import Path
import zipfile

from jsonschema import validate, ValidationError
from config import SCHEMAS_DIR, EXTRACT_DIR
from gen_types import mkvmerge_return_type
from utils.file_utils import create_split_zip
from utils.logger import get_logger

# Define logger
logger = get_logger("mkv_service")

# Define MKV merge return type
MKVMergeReturnType = mkvmerge_return_type.MkvmergeIdentificationOutput

# Define Extracting funtions return types
class MKVExtractReturnType(dict):
    """Return type for MKV extraction functions."""
    def __init__(self, **data):
        super().__init__(**data)
        self.paths = data.get("paths", [])
        self.count = data.get("count", 0)

    paths: list[Path]
    """List of extracted file paths."""
    count: int
    """Count of extracted items."""

# Load MKV merge JSON schema
mkvmerge_schema: dict = {}
schema_path = os.path.join(SCHEMAS_DIR, "mkvmerge_schema.json")
with open(schema_path, "r", encoding="utf-8") as schema_file:
    mkvmerge_schema = json.load(schema_file)

class MKVService:
    """Service class for MKV file operations."""

    @staticmethod
    def get_mediainfo(filepath: str):
        """Retrieves information about the MKV file."""
        cmd = ["mediainfo", filepath]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout

    @staticmethod
    def get_mkv_formatted_info(filepath: str) -> MKVMergeReturnType | None:
        """Retrieves formatted information about the MKV file."""
        try:
            cmd = ["mkvmerge", "-J", filepath]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            info = json.loads(result.stdout)

            # Validate against your JSON schema
            validate(instance=info, schema=mkvmerge_schema)
            return info
        except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
            print(f"Error retrieving MKV info: {e}")
            return None
        except ValidationError as ve:
            print(f"Schema validation error: {ve}")
            return None

    @staticmethod
    def extract_subtitles(filepath: str, output_dir: Path = Path(EXTRACT_DIR)) -> MKVExtractReturnType | None:
        """
        Extracts subtitles from the MKV file to the specified output directory.

        Args:
            filepath (str): The path to the MKV file.
            output_dir (Path): The directory to save extracted subtitles.

        Returns:
            dict[str, Path|int] | None: A dictionary containing the paths of the extracted subtitle files and their count,
            or None if extraction failed or no subtitles were found.
        """
        try:
            os.makedirs(output_dir, exist_ok=True)
            info = MKVService.get_mkv_formatted_info(filepath)

            if not info:
                return None

            extracted_files = []
            for s_id in info.get("tracks", []):
                if s_id.get("type") == "subtitles":
                    try:
                        subtitle_codec = s_id.get("codec", "").strip()
                        subtitle_language = s_id.get("properties", {}).get("language", "und")

                        # Determine extension based on codec
                        if subtitle_codec == "SubRip/SRT" or "srt" in subtitle_codec.lower():
                            extension = "srt"
                        elif subtitle_codec == "S_TEXT/UTF8" or "utf8" in subtitle_codec.lower():
                            extension = "srt"
                        elif subtitle_codec == "SubStationAlpha" or "ass" in subtitle_codec.lower():
                            extension = "ass"
                        else:
                            extension = "txt"

                        # Construct output path
                        out_path = os.path.join(
                            output_dir,
                            f"subtitle_{s_id['id']}.{subtitle_language}.{extension}"
                        )

                        # Command to extract subtitle track
                        subprocess.run(
                            ["mkvextract", filepath, "tracks", f"{s_id['id']}:{out_path}"], check=True
                        )
                        extracted_files.append(out_path)
                    except subprocess.CalledProcessError as extract_error:
                        logger.warning("Failed to extract subtitle track %s, skipping: %s", s_id.get("id"), extract_error)
                        continue
                    except Exception as item_error:
                        logger.warning("Error processing subtitle track %s, skipping: %s", s_id.get("id"), item_error)
                        continue

            if not extracted_files:
                return None

            zip_file_path = os.path.join(output_dir, "subtitles.zip")
            with zipfile.ZipFile(zip_file_path, "w") as zipf:
                for file in extracted_files:
                    zipf.write(file, arcname=os.path.basename(file))

            # Check zip file size
            zip_file_size = os.path.getsize(zip_file_path)
            if zip_file_size > 10 * 1024 * 1024:  # 10 MB limit
                logger.warning("Subtitles zip file exceeds 10 MB, splitting...")
                try:
                    split_files = create_split_zip(Path(zip_file_path), part_size=10 * 1024 * 1024)  # 10 MB parts
                    return MKVExtractReturnType(
                        paths=split_files,
                        count=len(extracted_files)
                    )
                except Exception as split_ex:
                    logger.error("Error splitting subtitles zip file: %s", split_ex)
                    return None
            
            return MKVExtractReturnType(
                paths=[Path(zip_file_path)],
                count=len(extracted_files)
            )
        except subprocess.CalledProcessError as e:
            print(f"Error extracting subtitles: {e}")
            return None
        except Exception as ex:
            print(f"Unexpected error: {ex}")
            return None

    @staticmethod
    def extract_attachments(filepath: str, output_dir: Path = Path(EXTRACT_DIR)) -> MKVExtractReturnType | None:
        """
        Extracts attachments from the MKV file to the specified output directory.
        
        Args:
            filepath (str): The path to the MKV file.
            output_dir (Path): The directory to save extracted attachments.

        Returns:
            dict[str, Path|int] | None: A dictionary containing the path of the extracted attachments or
            None if extraction failed or no attachments were found.
        """
        try:
            os.makedirs(output_dir, exist_ok=True)
            info = MKVService.get_mkv_formatted_info(filepath)

            if not info:
                return None

            extracted_files = []
            for a_id in info.get("attachments", []):
                try:
                    # Safely get content_type
                    content_type = a_id.get("content_type", "").strip()
                    
                    # Guess extension if not provided
                    if a_id.get("content_type") == "application/font-sfnt":
                        extension = "ttf"
                    elif a_id.get("content_type") == "application/x-truetype-font":
                        extension = "ttf"
                    elif a_id.get("content_type") == "font/ttf":
                        extension = "ttf"
                    elif a_id.get("content_type") == "application/vnd.ms-opentype":
                        extension = "otf"
                    elif a_id.get("content_type") == "font/otf":
                        extension = "otf"
                    elif a_id.get("content_type") == "image/png":
                        extension = "png"
                    elif a_id.get("content_type") == "image/jpeg":
                        extension = "jpg"
                    else:
                        extension = "bin"
                    
                    # Get attachment name and sanitize it
                    attachment_name = a_id.get("file_name", f"attachment_{a_id['id']}")
                    
                    # Ensure the filename is not too long by truncating if necessary
                    name_without_ext = os.path.splitext(attachment_name)[0][:50]
                    safe_filename = f"{name_without_ext}.{extension}"
                    
                    out_path = os.path.join(output_dir, safe_filename)
                    
                    subprocess.run(["mkvextract", filepath, "attachments", f"{a_id['id']}:{out_path}"], check=True)
                    extracted_files.append(out_path)
                except subprocess.CalledProcessError as extract_error:
                    logger.warning("Failed to extract attachment %s, skipping: %s", a_id.get("id"), extract_error)
                    continue
                except Exception as item_error:
                    logger.warning("Error processing attachment %s, skipping: %s", a_id.get("id"), item_error)
                    continue
            
            if not extracted_files:
                return None

            zip_file_path = os.path.join(output_dir, "attachments.zip")
            with zipfile.ZipFile(zip_file_path, "w") as zipf:
                for file in extracted_files:
                    zipf.write(file, arcname=os.path.basename(file))

            # Check zip file size
            zip_file_size = os.path.getsize(zip_file_path)
            if zip_file_size > 10 * 1024 * 1024:  # 10 MB limit, since discord file limit is 10 MB
                logger.warning("Attachments zip file exceeds 10 MB, splitting...")
                try:
                    split_files = create_split_zip(Path(zip_file_path), part_size=10 * 1024 * 1024)  # 10 MB parts
                    return MKVExtractReturnType(
                        paths=split_files,
                        count=len(extracted_files)
                    )
                except Exception as split_ex:
                    logger.error("Error splitting attachments zip file: %s", split_ex)
                    return None
            
            return MKVExtractReturnType(
                paths=[Path(zip_file_path)],
                count=len(extracted_files)
            )
        except subprocess.CalledProcessError as e:
            print(f"Error extracting attachments: {e}")
            return None
        except Exception as ex:
            print(f"Unexpected error: {ex}")
            return None

    @staticmethod
    def extract_chapters(filepath: str, output_dir: Path = Path(EXTRACT_DIR)) -> dict[str, Path|int] | None:
        """
        Extracts chapters from the MKV file to the specified output directory.
        
        Args:
            filepath (str): The path to the MKV file.
            output_dir (Path): The directory to save extracted chapters.

        Returns:
            dict[str, Path|int] | None: A dictionary containing the path of the extracted chapters or
            None if extraction failed or no chapters were found.
        """
        try:
            os.makedirs(output_dir, exist_ok=True)
            info = MKVService.get_mkv_formatted_info(filepath)

            if not info:
                return None

            chapters = info.get("chapters", [])
            if not chapters:
                return None

            out_path = os.path.join(output_dir, "chapters.xml")
            subprocess.run(["mkvextract", filepath, "chapters", ">", out_path], check=True)

            return {
                "path": Path(out_path),
                "count": chapters[0].get("num_entries", 0) if chapters else 0
            }
        except subprocess.CalledProcessError as e:
            print(f"Error extracting chapters: {e}")
            return None
        except Exception as ex:
            print(f"Unexpected error: {ex}")
            return None

    @staticmethod
    def extract_audio(filepath: str, output_dir: Path = Path(EXTRACT_DIR)) -> MKVExtractReturnType | None:
        """
        Extracts audio tracks from the MKV file to the specified output directory.
        
        Args:
            filepath (str): The path to the MKV file.
            output_dir (Path): The directory to save extracted audio.

        Returns:
            MKVExtractReturnType | None: A dictionary containing the paths of the extracted audio files and their count,
            or None if extraction failed or no audio tracks were found.
        """
        try:
            os.makedirs(output_dir, exist_ok=True)
            info = MKVService.get_mkv_formatted_info(filepath)

            if not info:
                return None

            extracted_files = []
            audio_track_number = 1
            
            for a_id in info.get("tracks", []):
                if a_id.get("type") == "audio":
                    try:
                        audio_codec = a_id.get("codec", "unknown").strip()
                        audio_language = a_id.get("properties", {}).get("language", "und")
                        
                        # Determine file extension based on codec
                        if audio_codec == "AAC" or "aac" in audio_codec.lower():
                            extension = "aac"
                        elif audio_codec == "MP3" or "mp3" in audio_codec.lower():
                            extension = "mp3"
                        elif audio_codec == "FLAC" or "flac" in audio_codec.lower():
                            extension = "flac"
                        elif audio_codec == "Opus" or "opus" in audio_codec.lower():
                            extension = "opus"
                        elif audio_codec == "Vorbis" or "vorbis" in audio_codec.lower():
                            extension = "ogg"
                        else:
                            extension = "mka"  # Matroska Audio as fallback

                        # Naming: single track as "audio", multiple tracks as "audio_2", "audio_3", etc.
                        if audio_track_number == 1:
                            audio_name = f"audio_{a_id['id']}.{audio_language}.{extension}"
                        else:
                            audio_name = f"audio_{audio_track_number}_{a_id['id']}.{audio_language}.{extension}"

                        out_path = os.path.join(output_dir, audio_name)

                        # Command to extract audio track
                        subprocess.run(
                            ["mkvextract", filepath, "tracks", f"{a_id['id']}:{out_path}"], check=True
                        )
                        extracted_files.append(out_path)
                        audio_track_number += 1
                    except subprocess.CalledProcessError as extract_error:
                        logger.warning("Failed to extract audio track %s, skipping: %s", a_id.get("id"), extract_error)
                        audio_track_number += 1
                        continue
                    except Exception as item_error:
                        logger.warning("Error processing audio track %s, skipping: %s", a_id.get("id"), item_error)
                        audio_track_number += 1
                        continue

            if not extracted_files:
                return None

            zip_file_path = os.path.join(output_dir, "audio.zip")
            with zipfile.ZipFile(zip_file_path, "w") as zipf:
                for file in extracted_files:
                    zipf.write(file, arcname=os.path.basename(file))

            # Check zip file size
            zip_file_size = os.path.getsize(zip_file_path)
            if zip_file_size > 10 * 1024 * 1024:  # 10 MB limit
                logger.warning("Audio zip file exceeds 10 MB, splitting...")
                try:
                    split_files = create_split_zip(Path(zip_file_path), part_size=10 * 1024 * 1024)  # 10 MB parts
                    return MKVExtractReturnType(
                        paths=split_files,
                        count=len(extracted_files)
                    )
                except Exception as split_ex:
                    logger.error("Error splitting audio zip file: %s", split_ex)
                    return None
            
            return MKVExtractReturnType(
                paths=[Path(zip_file_path)],
                count=len(extracted_files)
            )
        except subprocess.CalledProcessError as e:
            print(f"Error extracting audio: {e}")
            return None
        except Exception as ex:
            print(f"Unexpected error: {ex}")
            return None

    @staticmethod
    def extract_tracks(filepath: str, output_dir: Path = Path(EXTRACT_DIR)):
        """Extracts tracks from the MKV file to the specified output directory."""
        os.makedirs(output_dir, exist_ok=True)
        info = MKVService.get_mkv_formatted_info(filepath)

        if not info:
            return []

        extracted_files = []
        for t_id in info.get("tracks", []):
            if t_id.get("type") == "video":
                out_path = os.path.join(output_dir, f"track_{t_id['id']}.mkv")
                subprocess.run(["mkvextract", "tracks", filepath, f"{t_id['id']}:{out_path}"], check=True)
                extracted_files.append(out_path)
        return extracted_files
