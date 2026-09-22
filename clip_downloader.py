import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any
import imageio_ffmpeg
import yt_dlp

def ensure_ffmpeg_setup() -> Path:
    """Ensures ffmpeg.exe exists and is added to system PATH for yt-dlp compatibility."""
    exe_path = Path(imageio_ffmpeg.get_ffmpeg_exe())
    bin_dir = exe_path.parent
    std_ffmpeg = bin_dir / "ffmpeg.exe"
    if not std_ffmpeg.exists():
        shutil.copyfile(exe_path, std_ffmpeg)
        
    bin_dir_str = str(bin_dir.resolve())
    curr_path = os.environ.get("PATH", "")
    if bin_dir_str not in curr_path:
        os.environ["PATH"] = bin_dir_str + os.pathsep + curr_path
    return std_ffmpeg

def get_ffmpeg_binary() -> str:
    """Returns the bundled FFmpeg binary path."""
    return str(ensure_ffmpeg_setup())

def download_video_segment(
    url: str,
    start_sec: float,
    end_sec: float,
    output_path: Path,
    video_title: Optional[str] = None
) -> Path:
    """
    Downloads only the specified segment (start_sec to end_sec) from a video URL.
    Uses stream range downloading via yt-dlp + FFmpeg to avoid downloading full long videos.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg_exe = ensure_ffmpeg_setup()
    bin_dir_str = str(ffmpeg_exe.parent.resolve())

    # yt-dlp options for range downloading
    # Prefer HTTP range formats over m3u8_native so range requests fetch video frames properly
    ydl_opts: Dict[str, Any] = {
        "ffmpeg_location": bin_dir_str,
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "ios", "web"]
            }
        },
        "format": "bestvideo[height<=1080]+bestaudio/best[height<=1080]/best",
        "download_ranges": yt_dlp.utils.download_range_func(None, [(start_sec, end_sec)]),
        "force_keyframes_at_cuts": False,
        "outtmpl": str(output_path.with_suffix("").resolve()) + ".%(ext)s",
        "overwrites": True,
        "quiet": False,
        "no_warnings": True,
    }

    print(f"📥 Downloading segment {start_sec:.1f}s to {end_sec:.1f}s ({end_sec - start_sec:.1f}s duration)...")
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    # Find the downloaded file (yt-dlp may add extension like .webm or .mkv or .mp4)
    stem = output_path.stem
    parent = output_path.parent
    matching = [f for f in parent.glob(f"{stem}.*") if not f.name.endswith(".part")]

    if not matching:
        raise FileNotFoundError(f"Failed to find downloaded segment for {stem}")

    actual_file = matching[0]

    # If it's not the target output MP4 or needs remuxing, standardize to MP4
    if actual_file != output_path:
        cmd = [
            str(ffmpeg_exe.resolve()),
            "-y",
            "-i", str(actual_file.resolve()),
            "-c:v", "libx264",
            "-preset", "fast",
            "-c:a", "aac",
            "-pix_fmt", "yuv420p",
            str(output_path.resolve())
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"FFmpeg remux failed: {res.stderr[-300:]}")
        if actual_file.exists() and actual_file != output_path:
            try:
                actual_file.unlink()
            except Exception:
                pass

    return output_path

def trim_local_video(
    input_path: Path,
    start_sec: float,
    end_sec: float,
    output_path: Path
) -> Path:
    """Trims an existing local video file to the specified time window."""
    ffmpeg_exe = get_ffmpeg_binary()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    duration = end_sec - start_sec

    cmd = [
        ffmpeg_exe,
        "-y",
        "-ss", f"{start_sec:.3f}",
        "-i", str(input_path.resolve()),
        "-t", f"{duration:.3f}",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-pix_fmt", "yuv420p",
        str(output_path.resolve())
    ]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    return output_path
