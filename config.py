import os
import shutil
from pathlib import Path
from dotenv import load_dotenv
import imageio_ffmpeg

# Ensure ffmpeg.exe exists and is in system PATH for yt-dlp & subprocess
_ffmpeg_exe = Path(imageio_ffmpeg.get_ffmpeg_exe())
_bin_dir = _ffmpeg_exe.parent
_std_ffmpeg = _bin_dir / "ffmpeg.exe"
if not _std_ffmpeg.exists():
    try:
        shutil.copyfile(_ffmpeg_exe, _std_ffmpeg)
    except Exception:
        pass
_bin_dir_str = str(_bin_dir.resolve())
if _bin_dir_str not in os.environ.get("PATH", ""):
    os.environ["PATH"] = _bin_dir_str + os.pathsep + os.environ.get("PATH", "")

# Base Paths
BASE_DIR = Path(__file__).parent.resolve()
load_dotenv(BASE_DIR / ".env")

ASSETS_DIR = BASE_DIR / "assets"
IMAGES_DIR = ASSETS_DIR / "images"
VIDEOS_DIR = ASSETS_DIR / "videos"
MUSIC_DIR = ASSETS_DIR / "music"
OUTPUT_DIR = BASE_DIR / "output"
CACHE_DIR = BASE_DIR / "cache"

# Ensure directories exist
for p in [IMAGES_DIR, VIDEOS_DIR, MUSIC_DIR, OUTPUT_DIR, CACHE_DIR]:
    p.mkdir(parents=True, exist_ok=True)

# Pexels API Settings (100% Free API key from pexels.com/api)
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "")
PREFER_STOCK_VIDEOS = True  # Prioritize downloading real stock video clips over static photos

# Default Call to Action (Appended to all shorts for subscriber growth)
DEFAULT_CTA = "For more related content, make sure you subscribe for daily uploads."



# Video Specs (YouTube Shorts: 9:16 vertical)
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
VIDEO_FPS = 30

# Edge-TTS Settings (100% Free, Natural Azure Neural Voices)
# Options:
# "en-US-ChristopherNeural" (Deep, authoritative male, great for facts/curiosities)
# "en-US-GuyNeural" (Energetic, engaging male)
# "en-US-JennyNeural" (Warm, clear female)
# "en-US-AriaNeural" (Expressive female)
# "en-GB-RyanNeural" (British documentary narrator)
DEFAULT_VOICE = "en-US-ChristopherNeural"
VOICE_RATE = "+5%"  # slightly faster for snappy shorts retention
VOICE_PITCH = "+0Hz"

# Subtitle Styling (Modern Short viral style)
SUBTITLE_FONT = "Impact"  # Fallback to Arial Black / Arial if not installed
SUBTITLE_FONT_SIZE = 64
# Colors in ASS format: &HAABBGGRR& (AA=transparency, BB=blue, GG=green, RR=red)
SUBTITLE_PRIMARY_COLOR = "&H00FFFFFF&"   # White text
SUBTITLE_HIGHLIGHT_COLOR = "&H0000FFFF&" # Bright Yellow for active word (&H0000FFFF = Red:FF, Green:FF, Blue:00)
SUBTITLE_OUTLINE_COLOR = "&H00000000&"   # Deep black outline
SUBTITLE_OUTLINE_WIDTH = 4
SUBTITLE_SHADOW_DEPTH = 2

# Vertical placement & Center Coordinates
SUBTITLE_POS_X = 540  # Exactly 1080 / 2 (Dead Center horizontally)
SUBTITLE_POS_Y = 960  # Exactly 1920 / 2 (Dead Center vertically)
SUBTITLE_MARGIN_V = 960


# Background Audio
MUSIC_VOLUME = 0.10  # 10% volume (ducked under voiceover)

# ==========================================
# Viral Clipper Settings
# ==========================================
CLIPS_OUTPUT_DIR = OUTPUT_DIR / "clips"
CLIPS_CACHE_DIR = CACHE_DIR / "clips"
for p in [CLIPS_OUTPUT_DIR, CLIPS_CACHE_DIR]:
    p.mkdir(parents=True, exist_ok=True)

DEFAULT_CLIP_LAYOUT = "blur_bg"       # "blur_bg", "split_podcast", "face_crop"
DEFAULT_CLIP_DURATION = 35           # 30 to 45 seconds optimal for Shorts retention
MIN_CLIP_DURATION = 20
MAX_CLIP_DURATION = 60

# Clipper Subtitle Styling (Positioned in safe lower focus zone above mobile UI)
CLIP_SUBTITLE_POS_X = 540
CLIP_SUBTITLE_POS_Y = 1350            # Safe zone: above mobile Shorts UI, below 16:9 frame
CLIP_SUBTITLE_FONT_SIZE = 62          # Bold, high-retention mobile font size
CAPTION_LEAD_OFFSET = 0.38            # Lead time in seconds so captions trigger on speech beat

# Hook Banner Styling
HOOK_FONT = "Impact"
HOOK_FONT_SIZE = 48
HOOK_POS_Y = 240                      # Clean upper card position
