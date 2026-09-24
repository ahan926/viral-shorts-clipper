"""Video composition engine for converting landscape creator clips into 9:16 vertical YouTube Shorts."""
import subprocess
import shutil
import re
from pathlib import Path
from typing import Optional
import imageio_ffmpeg

from config import (
    VIDEO_WIDTH,
    VIDEO_HEIGHT,
    VIDEO_FPS,
    CLIPS_CACHE_DIR,
    HOOK_FONT,
    HOOK_FONT_SIZE,
    HOOK_POS_Y
)

def get_ffmpeg_binary() -> str:
    """Gets the path to the ffmpeg executable."""
    return imageio_ffmpeg.get_ffmpeg_exe()

def format_hook_banner(text: str, max_chars_per_line: int = 22, max_lines: int = 3) -> tuple[str, int, int]:
    """
    Wraps and formats hook titles with word-safe boundaries and dynamic font scaling.
    Returns: (formatted_text_with_newline_codes, font_size, pos_y)
    """
    # Clean text: remove excessive whitespace, normalize quotes
    clean_text = " ".join(text.strip().split())
    clean_text = clean_text.replace("’", "'").replace("“", '"').replace("”", '"')
    
    words = clean_text.upper().split()
    lines = []
    curr = []
    curr_len = 0
    for w in words:
        if curr_len + len(w) > max_chars_per_line and curr:
            lines.append(" ".join(curr))
            curr = [w]
            curr_len = len(w)
        else:
            curr.append(w)
            curr_len += len(w) + 1
    if curr:
        lines.append(" ".join(curr))

    # If exceeding max_lines, safely combine or truncate at whole word
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        # Ensure the last line ends cleanly without trailing punctuation
        last_line = re.sub(r"[,;:\-\.]+$", "", lines[-1]).strip()
        lines[-1] = last_line + "..."

    num_lines = len(lines)
    # Dynamic font scaling so long titles never overflow off-screen
    if num_lines == 1:
        font_size = 50
        pos_y = 250
    elif num_lines == 2:
        font_size = 42
        pos_y = 230
    else:
        font_size = 34
        pos_y = 205

    formatted_text = "\\N".join(lines)
    return formatted_text, font_size, pos_y

def append_hook_to_ass(ass_path: Path, hook_text: str, duration_sec: float) -> None:
    """Adds a stylish, high-contrast hook title card to the ASS subtitle file."""
    if not hook_text or not ass_path.exists():
        return

    content = ass_path.read_text(encoding="utf-8")
    formatted_hook, font_size, pos_y = format_hook_banner(hook_text)
    
    # Define Hook Style with bold high-contrast outline and dark box shadow
    hook_style = (
        f"Style: HookStyle,{HOOK_FONT},{font_size},"
        "&H00FFFFFF&,&H0000FFFF&,&H00000000&,&H90000000,"
        "-1,0,0,0,100,100,1,0,1,5,3,5,0,0,0,1\n"
    )
    
    if "[V4+ Styles]" in content and "HookStyle" not in content:
        content = content.replace("[Events]", f"{hook_style}\n[Events]")
    elif "HookStyle" in content:
        # Replace existing HookStyle with dynamically sized style
        content = re.sub(r"Style: HookStyle[^\n]*\n", f"{hook_style}", content)

    # Calculate end time string
    hrs = int(duration_sec // 3600)
    mins = int((duration_sec % 3600) // 60)
    secs = int(duration_sec % 60)
    centis = int(round((duration_sec - int(duration_sec)) * 100))
    end_str = f"{hrs}:{mins:02d}:{secs:02d}.{centis:02d}"

    # Hook dialogue line centered near top (Y=pos_y) with auto line wrapping
    hook_dialogue = f"Dialogue: 2,0:00:00.00,{end_str},HookStyle,,0,0,0,,{{\\pos(540,{pos_y})}}{formatted_hook}\n"

    content += f"\n{hook_dialogue}"
    ass_path.write_text(content, encoding="utf-8")

def build_filter_graph(layout: str, has_subtitles: bool, sub_filename: str) -> str:
    """
    Constructs the FFmpeg video filtergraph based on the selected layout:
    - 'blur_bg': 16:9 centered over 1080x1920 blurred background (Best general layout)
    - 'split_podcast': Left speaker on top, right speaker on bottom with divider bar
    - 'face_crop': 9:16 center vertical crop
    """
    sub_filter = f",subtitles='{sub_filename}'" if has_subtitles else ""

    if layout == "split_podcast":
        # Divide into left half and right half, scale both to 1080x960, and stack vertically
        filter_str = (
            f"[0:v]crop=iw/2:ih:0:0,scale={VIDEO_WIDTH}:{VIDEO_HEIGHT//2}:force_original_aspect_ratio=increase,crop={VIDEO_WIDTH}:{VIDEO_HEIGHT//2}[top];"
            f"[0:v]crop=iw/2:ih:iw/2:0,scale={VIDEO_WIDTH}:{VIDEO_HEIGHT//2}:force_original_aspect_ratio=increase,crop={VIDEO_WIDTH}:{VIDEO_HEIGHT//2}[bot];"
            f"[top][bot]vstack[stacked];"
            f"[stacked]fps={VIDEO_FPS}{sub_filter}[outv]"
        )
        return filter_str

    elif layout == "face_crop":
        # 9:16 center crop
        filter_str = (
            f"[0:v]crop=ih*9/16:ih:(iw-ow)/2:0,scale={VIDEO_WIDTH}:{VIDEO_HEIGHT},fps={VIDEO_FPS}{sub_filter}[outv]"
        )
        return filter_str

    else:
        # Default: blur_bg layout
        filter_str = (
            f"[0:v]scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=increase,crop={VIDEO_WIDTH}:{VIDEO_HEIGHT},boxblur=25:25[bg];"
            f"[0:v]scale={VIDEO_WIDTH}:-2[fg];"
            f"[bg][fg]overlay=(W-w)/2:(H-h)/2[base];"
            f"[base]fps={VIDEO_FPS}{sub_filter}[outv]"
        )
        return filter_str

def compose_short_clip(
    input_clip_path: Path,
    output_mp4_path: Path,
    layout: str = "blur_bg",
    subtitle_ass_path: Optional[Path] = None,
    hook_text: Optional[str] = None,
    duration_sec: Optional[float] = None
) -> Path:
    """
    Renders the final 9:16 vertical YouTube Short with layout framing,
    dynamic animated subtitles, hook banner, and normalized audio.
    """
    ffmpeg_exe = get_ffmpeg_binary()
    output_mp4_path.parent.mkdir(parents=True, exist_ok=True)

    temp_dir = CLIPS_CACHE_DIR / f"render_{output_mp4_path.stem}"
    temp_dir.mkdir(parents=True, exist_ok=True)

    # Prepare local copy of subtitles in temp_dir to prevent path escaping issues
    sub_filename = "subs.ass"
    has_subtitles = False
    if subtitle_ass_path and subtitle_ass_path.exists():
        local_sub = temp_dir / sub_filename
        shutil.copy(subtitle_ass_path, local_sub)
        
        # Append hook header if provided
        if hook_text and duration_sec:
            append_hook_to_ass(local_sub, hook_text, duration_sec)
        has_subtitles = True
    elif hook_text and duration_sec:
        # Create a standalone ASS file just for the hook banner
        local_sub = temp_dir / sub_filename
        local_sub.write_text(
            f"[Script Info]\nTitle: Hook Banner\nScriptType: v4.00+\nPlayResX: {VIDEO_WIDTH}\nPlayResY: {VIDEO_HEIGHT}\n\n"
            f"[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
            f"Style: HookStyle,{HOOK_FONT},{HOOK_FONT_SIZE},&H0000FFFF&,&H00FFFFFF&,&H00000000&,&H80000000,-1,0,0,0,100,100,1,0,1,5,3,5,0,0,0,1\n\n"
            f"[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n",
            encoding="utf-8"
        )
        append_hook_to_ass(local_sub, hook_text, duration_sec)
        has_subtitles = True

    filter_graph = build_filter_graph(layout, has_subtitles, sub_filename)

    # FFmpeg command
    cmd = [
        ffmpeg_exe,
        "-y",
        "-i", str(input_clip_path.resolve()),
        "-filter_complex", filter_graph,
        "-map", "[outv]",
        "-map", "0:a?",
        "-af", "loudnorm=I=-14:TP=-1.5:LRA=11",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "20",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        str(output_mp4_path.resolve())
    ]

    print(f"🎬 Rendering vertical 9:16 Short (Layout: '{layout}')...")
    res = subprocess.run(cmd, cwd=str(temp_dir), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    if res.returncode != 0:
        print(f"FFmpeg render error:\n{res.stderr[-800:]}")
        raise RuntimeError(f"FFmpeg failed to render short: {res.stderr[-300:]}")

    # Cleanup temp dir
    try:
        shutil.rmtree(temp_dir, ignore_errors=True)
    except Exception:
        pass

    print(f"✨ Successfully generated Short: {output_mp4_path.name}")
    return output_mp4_path
