import os
import shutil
import subprocess
from pathlib import Path

from django.conf import settings


def lecture_hls_output_dir(lecture_id: int) -> Path:
    return Path(settings.MEDIA_ROOT) / settings.HLS_OUTPUT_SUBDIR / f"lecture_{lecture_id}"


def lecture_hls_manifest_path(lecture_id: int) -> Path:
    return lecture_hls_output_dir(lecture_id) / "index.m3u8"


def transcode_to_hls(*, input_path: str, lecture_id: int) -> tuple[Path, Path]:
    """Transcode an input video to a single-variant HLS output.

    Returns: (output_dir, manifest_path)

    Requires ffmpeg to be installed and available on PATH.
    """

    output_dir = lecture_hls_output_dir(lecture_id)
    manifest_path = lecture_hls_manifest_path(lecture_id)

    output_dir.mkdir(parents=True, exist_ok=True)

    segment_pattern = str(output_dir / "seg_%05d.ts")

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        input_path,
        "-codec:v",
        "libx264",
        "-codec:a",
        "aac",
        "-hls_time",
        "6",
        "-hls_playlist_type",
        "vod",
        "-hls_segment_filename",
        segment_pattern,
        str(manifest_path),
    ]

    try:
        completed = subprocess.run(cmd, capture_output=True, text=True)
    except FileNotFoundError as exc:
        raise RuntimeError(
            "FFmpeg not found. Install FFmpeg and add it to PATH (so `ffmpeg -version` works)."
        ) from exc

    if completed.returncode != 0:
        # Clean the directory to avoid partial artifacts
        shutil.rmtree(output_dir, ignore_errors=True)
        stderr = (completed.stderr or "").strip()
        raise RuntimeError(f"FFmpeg failed: {stderr[-2000:]}")

    if not manifest_path.exists():
        raise RuntimeError("HLS manifest was not created")

    return output_dir, manifest_path


def is_safe_child_path(parent: Path, child: Path) -> bool:
    try:
        parent_resolved = parent.resolve()
        child_resolved = child.resolve()
    except FileNotFoundError:
        return False
    return str(child_resolved).startswith(str(parent_resolved) + os.sep)
