"""MKV service module for handling MKV file operations."""

import subprocess
import os
import json
from pathlib import Path
import zipfile

from jsonschema import validate, ValidationError
from config import SCHEMAS_DIR, EXTRACT_DIR
from gen_types import mkvmerge_return_type
from utils.file_utils import DISCORD_MAX_FILE_SIZE, create_split_zip
from utils.logger import get_logger

# Define MKV merge return type
MKVMergeReturnType = mkvmerge_return_type.MkvmergeIdentificationOutput

# Define Extracting funtions return types
class MKVExtractReturnType(dict):
    """Return type for MKV extraction functions."""
    def __init__(self, **data):
        super().__init__(**data)
        self.paths = data.get("paths", Path(EXTRACT_DIR))
        self.count = data.get("count", 0)

    paths: Path
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
    def get_dynamic_timeout(mkv_path: str, extracting_video: bool = False) -> int:
        """
        Calculates a safe timeout in seconds based on MKV file size.
        Assumes a conservative minimum read/write speed of ~25 MB/s (covers HDDs & decent NAS).

        Args:
            mkv_path: Path to the MKV file.
            extracting_video: Whether the extraction includes video tracks (slower).
        """
        file_size_gb = os.path.getsize(mkv_path) / (1024 ** 3)

        # Base 45s overhead + 40s per GB (or 60s per GB if extracting heavy video streams)
        seconds_per_gb = 60 if extracting_video else 40
        calculated = int(45 + (file_size_gb * seconds_per_gb))

        # Enforce a minimum of 60s and a maximum cap of 30 minutes (1800s)
        return max(60, min(calculated, 1800))

    @staticmethod
    def extract_mkv_tracks(cmd: list[str], timeout_sec: int = 300) -> bool:
        """
        Runs mkvextract and catches all possible OS, subprocess, and mkvextract exceptions.

        Args:
            cmd: List of strings representing the command to run]).
            timeout_sec: Maximum seconds to wait before aborting.
        """

        logger = get_logger("mkv_service.extract_mkv_tracks")

        try:
            _result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",  # Prevents UnicodeDecodeError if mkvextract outputs corrupted bytes
                check=True,
                timeout=timeout_sec
            )
            return True

        # 1. mkvextract ran, but returned a non-zero exit code (1 = Warning, 2 = Error, other = Crash)
        except subprocess.CalledProcessError as e:
            output = f"{e.stdout or ''}\n{e.stderr or ''}".strip()

            if e.returncode == 1:
                logger.warning("mkvextract finished with warnings (exit code 1):\n%s", output)
                return True  # Change to False if you want warnings treated as failures
            elif e.returncode == 2:
                logger.error("mkvextract aborted with a fatal error (exit code 2):\n%s", output)
            else:
                logger.critical("[CRASH] mkvextract terminated unexpectedly (exit code %s):\n%s", e.returncode, output)
            return False

        # 2. The process hung (e.g., stalled on a network drive or corrupted file)
        except subprocess.TimeoutExpired as e:
            # Note: e.stdout / e.stderr are bytes here even when text=True
            partial_out = (e.stdout or b"").decode("utf-8", errors="replace")
            partial_err = (e.stderr or b"").decode("utf-8", errors="replace")
            logger.error("[TIMEOUT] mkvextract exceeded %d seconds and was killed.", e.timeout)
            if partial_out or partial_err:
                logger.error("Partial output before timeout:\n%s\n%s", partial_out, partial_err)
            return False

        # 3. mkvextract executable was not found
        except FileNotFoundError:
            logger.error("[SYSTEM ERROR] 'mkvextract' executable not found. Ensure MKVToolNix is installed and in PATH.")
            return False

        # 4. OS denied execution (e.g., mkvextract binary lacks +x permission)
        except PermissionError as e:
            logger.error("[SYSTEM ERROR] Permission denied when trying to execute mkvextract: %s", e.strerror)
            return False

        # 5. Invalid arguments passed to subprocess.run (e.g., null bytes in file paths, bad timeout)
        except ValueError as e:
            logger.error("[ARGUMENT ERROR] Invalid parameters passed to subprocess: %s", e)
            return False

        # 6. Catch-all for remaining OS-level issues (e.g., path too long on Windows, out of memory, E2BIG)
        except OSError as e:
            logger.error("[OS ERROR] Operating system error occurred (errno %d): %s", e.errno, e.strerror)
            return False

        # 7. Catch-all for any unexpected Python/subprocess edge cases
        except subprocess.SubprocessError as e:
            logger.error("[SUBPROCESS ERROR] Unexpected subprocess failure: %s", e)
            return False

    @staticmethod
    def get_mediainfo(file_path: str):
        """Retrieves information about the MKV file."""

        logger = get_logger("mkv_service.get_mediainfo")
        
        try:
            cmd = ["mediainfo", file_path]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",  # Prevents UnicodeDecodeError on weird file tags
                check=True,        # Raises CalledProcessError on non-zero exit codes
                )

            # Ensure output isn't empty before parsing
            if not result.stdout.strip():
                logger.warning("MediaInfo returned empty output for %s. The file may be corrupted or unsupported.", file_path)
            return result.stdout
        except FileNotFoundError as exc:
            logger.error(
                "The 'mediainfo' executable was not found. "
                "Ensure MediaInfo CLI is installed and added to your system PATH."
            )

        except PermissionError as exc:
            logger.error(
                "Permission denied when executing 'mediainfo' or reading '%s'.",
                file_path
            )

        except subprocess.CalledProcessError as exc:
            stderr_msg = exc.stderr.strip() if exc.stderr else "No error details provided."
            logger.error(
                "MediaInfo failed with exit code %d: %s",
                exc.returncode,
                stderr_msg
            )

        except OSError as exc:
            # Catches low-level OS issues (e.g., Exec format error, E2BIG argument list too long)
            logger.error("OS-level error occurred while running MediaInfo: %s", exc)

    @staticmethod
    def get_mkv_formatted_info(file_path: str) -> MKVMergeReturnType | None:
        """Retrieves formatted information about the MKV file."""

        logger = get_logger("mkv_service.get_mkv_formatted_info")
        
        try:
            cmd = ["mkvmerge", "-J", file_path]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",  # Protects against corrupted track names/tags
                check=True
            )
            info = json.loads(result.stdout)

            # Validate against your JSON schema
            validate(instance=info, schema=mkvmerge_schema)
            return info
        # 1. mkvmerge ran, but returned exit code 1 (Warning) or 2 (Fatal Error)
        except subprocess.CalledProcessError as e:
            logger = get_logger("mkv_service.get_mkv_formatted_info.CalledProcessError")
            raw_stdout = (e.stdout or "").strip()
            raw_stderr = (e.stderr or "").strip()

            # mkvmerge -J still outputs valid JSON containing "errors" and "warnings" arrays on exit 1 or 2
            try:
                data = json.loads(raw_stdout)
                errors = data.get("errors", [])
                warnings = data.get("warnings", [])

                if e.returncode == 1:
                    logger.warning("mkvmerge completed with warnings: %s", warnings)
                    # Validate against JSON schema
                    validate(instance=data, schema=mkvmerge_schema)
                    return data  # JSON is still complete and usable on exit code 1
                elif e.returncode == 2:
                    logger.error("mkvmerge failed to identify file: %s", errors)
                    return None

            except json.JSONDecodeError:
                # Fallback if mkvmerge crashed before printing valid JSON
                combined = f"{raw_stdout}\n{raw_stderr}".strip()
                logger.error("[CRASH] mkvmerge exited with code %s and non-JSON output:\n%s", e.returncode, combined)
                return None
        
            except ValidationError as ve:
                logger.error("Schema validation error: %s", ve)
                return None

        # 2. Exit code was 0, but stdout contained malformed or empty JSON
        except json.JSONDecodeError as e:
            logger.error("[JSON ERROR] mkvmerge succeeded, but returned invalid JSON: %s", e)
            return None

        # 4. mkvmerge is not installed or missing from system PATH
        except FileNotFoundError:
            logger.error("[SYSTEM ERROR] 'mkvmerge' executable not found. Ensure MKVToolNix is installed and in PATH.")
            return None

        # 5. OS denied execution permissions
        except PermissionError as e:
            logger.error("[SYSTEM ERROR] Permission denied executing mkvmerge: %s", e)
            return None

        # 6. Invalid arguments passed to subprocess.run (e.g., null bytes in path)
        except ValueError as e:
            logger.error("[ARGUMENT ERROR] Invalid parameters passed to subprocess: %s", e)
            return None

        # 7. Remaining OS-level failures (path too long, disk I/O error, etc.)
        except OSError as e:
            logger.error("[OS ERROR] Operating system error (errno %d): %s", e.errno, e.strerror)
            return None

        # 8. Catch-all for any unexpected subprocess edge cases
        except subprocess.SubprocessError as e:
            logger.error("[SUBPROCESS ERROR] Unexpected subprocess error: %s", e)
            return None
        
        except ValidationError as ve:
            logger.error("Schema validation error: %s", ve)
            return None

    @staticmethod
    def extract_subtitles(
        file_path: str,
        output_dir: Path = Path(EXTRACT_DIR)
    ) -> MKVExtractReturnType | None:
        """
        Extracts subtitles from the MKV file to the specified output directory.

        Args:
            file_path (str): The path to the MKV file.
            output_dir (Path): The directory to save extracted subtitles.

        Returns:
            dict[str, Path|int] | None: A dictionary containing the paths of the extracted subtitle files and their count,
            or None if extraction failed or no subtitles were found.
        """

        logger = get_logger("mkv_service.extract_subtitles")
        
        try:
            os.makedirs(output_dir, exist_ok=True)
            info = MKVService.get_mkv_formatted_info(file_path)

            if not info:
                return None

            extracted_files = []
            idx_subs: int = 0
            for s_id in info.get("tracks", []):
                if s_id.get("type") == "subtitles":
                    try:
                        subtitle_codec = s_id.get("codec", "").strip()
                        codec = subtitle_codec.lower()
                        subtitle_language = s_id.get("properties", {}).get("language", "und")

                        # Determine extension based on mkvmerge / mkvextract codec ID
                        if subtitle_codec in ("SubRip/SRT", "S_TEXT/UTF8", "S_TEXT/ASCII") or any(k in codec for k in ("srt", "subrip", "utf8", "ascii")):
                            extension = "srt"
                        elif subtitle_codec == "S_TEXT/ASS" or "ass" in codec:
                            extension = "ass"
                        elif subtitle_codec in ("SubStationAlpha", "S_TEXT/SSA") or "ssa" in codec:
                            extension = "ass" # mkvextract outputs SSA as .ass, even though the codec is technically SSA
                        elif subtitle_codec == "S_TEXT/WEBVTT" or any(k in codec for k in ("webvtt", "vtt")):
                            extension = "vtt"
                        elif subtitle_codec in ("S_HDMV/PGS", "HDMV PGS") or any(k in codec for k in ("pgs", "sup")):
                            extension = "sup"
                        elif subtitle_codec in ("S_VOBSUB", "VobSub") or "vobsub" in codec:
                            extension = "idx"  # mkvextract takes .idx as the output filename and auto-creates the .sub file
                        elif subtitle_codec == "S_DVBSUB" or "dvbsub" in codec:
                            extension = "dvb"
                        elif subtitle_codec == "S_KATE" or "kate" in codec:
                            extension = "ogg"
                        elif subtitle_codec == "S_TEXT/USF" or "usf" in codec:
                            extension = "usf"
                        elif subtitle_codec == "S_HDMV/TEXTST" or "textst" in codec:
                            extension = "textst"
                        else:
                            logger.warning("Unknown subtitle codec: %s", subtitle_codec)
                            continue

                        # Construct output path
                        out_path = os.path.join(
                            output_dir,
                            f"subtitle_{s_id['id']}.{subtitle_language}.{extension}"
                        )

                        # Command to extract subtitle track
                        cmd = [
                            "mkvextract",
                            "--quiet",
                            file_path,
                            "tracks",
                            f"{s_id['id']}:{out_path}"
                        ]
                        # Get dynamic timeout based on file size and whether it includes extracting the video track
                        timeout_sec = MKVService.get_dynamic_timeout(file_path)

                        # Command to extract subtitle track
                        result = MKVService.extract_mkv_tracks(cmd, timeout_sec=timeout_sec)
                        if not result:
                            continue  # Skip to the next subtitle track if extraction failed
                        extracted_files.append(out_path)
                        # mkvextract automatically creates a .sub file alongside the .idx file
                        if extension == "idx":
                            idx_subs += 1
                            sub_file_path = os.path.join(
                                output_dir,
                                f"subtitle_{s_id['id']}.{subtitle_language}.sub"
                            )
                            if os.path.exists(sub_file_path):
                                extracted_files.append(sub_file_path)
                    except subprocess.CalledProcessError as extract_error:
                        logger.warning("Failed to extract subtitle track %s, skipping: %s", s_id.get("id"), extract_error)
                        continue
                    except Exception as item_error:
                        logger.warning("Error processing subtitle track %s, skipping: %s", s_id.get("id"), item_error)
                        continue

            if not extracted_files:
                return None

            subs_count = len(extracted_files) - idx_subs  # Exclude .sub files from the count
            logger.info("Extracted %d subtitle files.", subs_count)

            return MKVExtractReturnType(
                paths=output_dir,
                count=subs_count
            )
        except subprocess.CalledProcessError as e:
            logger.error("Error extracting subtitles: %s", e)
            return None
        except Exception as ex:
            logger.error("Unexpected error: %s", ex)
            return None

    @staticmethod
    def extract_attachments(file_path: str, output_dir: Path = Path(EXTRACT_DIR)) -> MKVExtractReturnType | None:
        """
        Extracts attachments from the MKV file to the specified output directory.
        
        Args:
            file_path (str): The path to the MKV file.
            output_dir (Path): The directory to save extracted attachments.

        Returns:
            MKVExtractReturnType | None: An instance of MKVExtractReturnType containing the path of the extracted
            attachments or None if extraction failed or no attachments were found.
        """

        logger = get_logger("mkv_service.extract_attachments")

        try:
            os.makedirs(output_dir, exist_ok=True)
            info = MKVService.get_mkv_formatted_info(file_path)

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
                    
                    # Construct output path
                    out_path = os.path.join(output_dir, safe_filename)

                    # Command to extract attachments
                    cmd = [
                        "mkvextract",
                        "--quiet",
                        file_path,
                        "attachments",
                        f"{a_id['id']}:{out_path}"
                    ]
                    # Get dynamic timeout based on file size and whether it includes extracting the video track
                    timeout_sec = MKVService.get_dynamic_timeout(file_path)
                    
                    # Command to extract attachments
                    result = MKVService.extract_mkv_tracks(cmd, timeout_sec=timeout_sec)
                    if not result:
                        continue  # Skip to the next attachment if extraction failed

                    extracted_files.append(out_path)
                except subprocess.CalledProcessError as extract_error:
                    logger.warning("Failed to extract attachment %s, skipping: %s", a_id.get("id"), extract_error)
                    continue
                except Exception as item_error:
                    logger.warning("Error processing attachment %s, skipping: %s", a_id.get("id"), item_error)
                    continue
            
            if not extracted_files:
                return None

            logger.info("Extracted %d attachments.", len(extracted_files))

            return MKVExtractReturnType(
                paths=output_dir,
                count=len(extracted_files)
            )
        except subprocess.CalledProcessError as e:
            logger.error("Error extracting attachments: %s", e)
            return None
        except Exception as ex:
            logger.error("Unexpected error: %s", ex)
            return None

    @staticmethod
    def extract_chapters(file_path: str, output_dir: Path = Path(EXTRACT_DIR)) -> MKVExtractReturnType | None:
        """
        Extracts chapters from the MKV file to the specified output directory.
        
        Args:
            file_path (str): The path to the MKV file.
            output_dir (Path): The directory to save extracted chapters.

        Returns:
            MKVExtractReturnType | None: An instance of MKVExtractReturnType containing the path
            of the extracted chapters or None if extraction failed or no chapters were found.
        """

        logger = get_logger("mkv_service.extract_chapters")

        try:
            os.makedirs(output_dir, exist_ok=True)
            info = MKVService.get_mkv_formatted_info(file_path)

            if not info:
                return None

            chapters = info.get("chapters", [])
            if not chapters:
                return None

            out_path = os.path.join(output_dir, "chapters.xml")

            # Command to extract chapters
            cmd = [
                "mkvextract",
                "--quiet",
                file_path,
                "chapters",
                out_path
            ]
            # Get dynamic timeout based on file size and whether it includes extracting the video track
            timeout_sec = MKVService.get_dynamic_timeout(file_path)

            # Command to extract chapters
            result = MKVService.extract_mkv_tracks(cmd, timeout_sec=timeout_sec)
            if not result:
                return None  # return None if extraction failed

            logger.info("Extracted %d chapters.", chapters[0].get("num_entries", 0) if chapters else 0)

            return MKVExtractReturnType(
                paths=Path(out_path),
                count=chapters[0].get("num_entries", 0) if chapters else 0
            )
        except subprocess.CalledProcessError as e:
            logger.error("Error extracting chapters: %s", e)
            return None
        except Exception as ex:
            logger.error("Unexpected error: %s", ex)
            return None

    @staticmethod
    def extract_audio(file_path: str, output_dir: Path = Path(EXTRACT_DIR)) -> MKVExtractReturnType | None:
        """
        Extracts audio tracks from the MKV file to the specified output directory.
        
        Args:
            file_path (str): The path to the MKV file.
            output_dir (Path): The directory to save extracted audio.

        Returns:
            MKVExtractReturnType | None: An instance of MKVExtractReturnType containing the paths of
            the extracted audio files and their count, or None if extraction failed or no audio
            tracks were found.
        """

        logger = get_logger("mkv_service.extract_audio")

        try:
            os.makedirs(output_dir, exist_ok=True)
            info = MKVService.get_mkv_formatted_info(file_path)

            if not info:
                return None

            extracted_files = []
            audio_track_number = 1

            for a_id in info.get("tracks", []):
                if a_id.get("type") == "audio":
                    try:
                        audio_codec = a_id.get("codec", "unknown").strip()
                        audio_language = a_id.get("properties", {}).get("language", "und")
                        codec = audio_codec.lower()

                        # Determine extension based on mkvmerge / mkvextract audio codec ID
                        if audio_codec.startswith("A_AAC") or "aac" in codec:
                            extension = "aac"
                        elif audio_codec in ("A_AC3", "AC-3") or ("ac3" in codec and "eac3" not in codec):
                            extension = "ac3"
                        elif audio_codec in ("A_EAC3", "E-AC-3") or "eac3" in codec or "e-ac-3" in codec:
                            extension = "eac3"
                        elif audio_codec.startswith("A_DTS") or "dts" in codec:
                            extension = "dts"  # Covers DTS, DTS-HD MA, and DTS-HD HRA (all extract as raw .dts)
                        elif audio_codec == "A_TRUEHD" or "truehd" in codec:
                            extension = "thd"  # Raw TrueHD stream (Note: TrueHD+AC3 core extracts as .thd+ac3)
                        elif audio_codec == "A_MLP" or "mlp" in codec:
                            extension = "mlp"
                        elif audio_codec == "A_FLAC" or "flac" in codec:
                            extension = "flac"
                        elif audio_codec == "A_OPUS" or "opus" in codec:
                            extension = "opus"  # mkvextract wraps raw Opus packets into an .opus (Ogg) container
                        elif audio_codec == "A_VORBIS" or "vorbis" in codec:
                            extension = "ogg"
                        elif audio_codec == "A_MPEG/L3" or "mp3" in codec:
                            extension = "mp3"
                        elif audio_codec in ("A_MPEG/L2", "A_MPEG/L1") or "mp2" in codec:
                            extension = "mp2"
                        elif audio_codec.startswith("A_PCM") or "pcm" in codec:
                            extension = "wav"  # mkvextract automatically writes a WAV header for PCM tracks
                        elif audio_codec == "A_ALAC" or "alac" in codec:
                            extension = "caf"  # mkvextract wraps ALAC inside a Core Audio Format (.caf) container
                        elif audio_codec == "A_WAVPACK4" or "wavpack" in codec:
                            extension = "wv"
                        elif audio_codec == "A_TTA1" or "tta" in codec:
                            extension = "tta"
                        else:
                            extension = "mka"  # Fallback: wrap unknown audio codecs cleanly in a Matroska Audio container

                        # Naming: single track as "audio", multiple tracks as "audio_2", "audio_3", etc.
                        if audio_track_number == 1:
                            audio_name = f"audio_{a_id['id']}.{audio_language}.{extension}"
                        else:
                            audio_name = f"audio_{audio_track_number}_{a_id['id']}.{audio_language}.{extension}"

                        out_path = os.path.join(output_dir, audio_name)

                        # Command to extract audio track
                        cmd = [
                            "mkvextract",
                            "--quiet",
                            file_path,
                            "tracks",
                            f"{a_id['id']}:{out_path}"
                        ]
                        # Get dynamic timeout based on file size and whether it includes extracting the video track
                        timeout_sec = MKVService.get_dynamic_timeout(file_path)

                        # Command to extract audio track
                        result = MKVService.extract_mkv_tracks(cmd, timeout_sec=timeout_sec)
                        if not result:
                            continue  # Skip to the next audio track if extraction failed

                        # Append the successfully extracted file path to the list
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

            logger.info("Extracted %d audio files.", len(extracted_files))

            return MKVExtractReturnType(
                paths=output_dir,
                count=len(extracted_files)
            )
        except subprocess.CalledProcessError as e:
            logger.error("Error extracting audio: %s", e)
            return None
        except Exception as ex:
            logger.error("Unexpected error: %s", ex)
            return None

    @staticmethod
    def extract_tracks(file_path: str, output_dir: Path = Path(EXTRACT_DIR)):
        """Extracts tracks from the MKV file to the specified output directory.
        
        Args:
            filepath (str): The path to the MKV file.
            output_dir (Path): The directory to save extracted tracks.
        """

        logger = get_logger("mkv_service.extract_tracks")

        os.makedirs(output_dir, exist_ok=True)
        info = MKVService.get_mkv_formatted_info(file_path)

        if not info:
            return []

        extracted_files = []
        for t_id in info.get("tracks", []):
            if t_id.get("type") == "video":
                out_path = os.path.join(output_dir, f"track_{t_id['id']}.mkv")
                logger.info("Extracting video track %d.", t_id["id"])
                subprocess.run(
                    ["mkvextract", "tracks", file_path, f"{t_id['id']}:{out_path}"],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                logger.info("Extracted video track %d.", t_id["id"])
                extracted_files.append(out_path)
        return extracted_files
