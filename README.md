# 🔥 Viral Creator YouTube Shorts Clipper

A fully automated, zero-cost Python pipeline that turns viral moments from popular content creators, podcasters, and Twitch/YouTube streamers (Kai Cenat, IShowSpeed, CaseOh, Joe Rogan, Andrew Huberman, Asmongold, etc.) into high-retention 9:16 vertical YouTube Shorts with dynamic animated captions.

---

## ⚡ Quick Start: Viral Creator Clipper (`clipper.py`)

### 1. View Supported Creators (26+ Channels & Aliases)
```powershell
& "C:\Users\jpsh9\.local\bin\uv.exe" run python clipper.py --list-creators
```
Supported presets include: `rogan`, `mrbeast`, `huberman`, `theovon`, `kaicenat` (`kai`), `speed` (`ishowspeed`), `caseoh`, `penguinz0` (`charlie`), `hormozi`, `flagrant` (`schulz`), `pbd`, `rawtalk`, `xqc`, `sketch`, `jocko`, `fullsend`, `mkbhd`, `impacttheory`, `asmongold` (`asmon`), `lexfridman`, `modernwisdom`, `diaryofaceo`, `jordanpeterson`, `impaulsive`, `markrober`, `veritasium`.

### 2. Auto-Clip Hilarious & Viral Stream Moments (`--funny`)
Searches for top-viewed stream reactions, rage moments, and funny compilations with conversational context snapping:

```powershell
# Automatically clip the funniest moment from Kai Cenat:
& "C:\Users\jpsh9\.local\bin\uv.exe" run python clipper.py --creator kai --funny --duration 30

# Clip IShowSpeed's wildest stream moments:
& "C:\Users\jpsh9\.local\bin\uv.exe" run python clipper.py --creator speed --funny --duration 30

# Clip CaseOh's funniest moments:
& "C:\Users\jpsh9\.local\bin\uv.exe" run python clipper.py --creator caseoh --funny --duration 25
```

### 3. Search Specific Themes or Moments (`--query`)
Target exact topics, guests, or funny moments across any creator:

```powershell
# Search CaseOh desk slam rage:
& "C:\Users\jpsh9\.local\bin\uv.exe" run python clipper.py --creator caseoh --query "rage" --duration 25

# Search Joe Rogan alien conspiracy debates:
& "C:\Users\jpsh9\.local\bin\uv.exe" run python clipper.py --creator rogan --query "alien conspiracy" --duration 35
```

### 4. Auto-Clip ANY YouTube Video or Podcast URL
Pass any YouTube URL and let the algorithm locate the peak viral moment:

```powershell
& "C:\Users\jpsh9\.local\bin\uv.exe" run python clipper.py `
  --url "https://www.youtube.com/watch?v=DuRcrbP3kag" `
  --auto `
  --count 1 `
  --duration 35
```

### 5. Automated 7-Day Batch Schedule (`batch_7_shorts.py`)
Produces a complete week of Shorts from 7 different top creators in minutes:

```powershell
& "C:\Users\jpsh9\.local\bin\uv.exe" run python batch_7_shorts.py
```

---

## 🎨 Vertical Layout Framing Options

| Layout | Description | Best For |
|---|---|---|
| `--layout blur_bg` (Default) | Sharp 16:9 video centered with a 1080x1920 blurred background. Never crops faces or visual context. | Universal (Streamers, Podcasts, Gaming) |
| `--layout split_podcast` | Splits landscape video in half: Host on top, Guest on bottom (stacked 1080x960 each). | Wide 2-shot interviews |
| `--layout face_crop` | Direct 9:16 vertical crop centered on the frame. | Solo talking heads, monologues |

---

## 📝 High-Retention Features Built-In

1. **Conversational Context Snapping**: Snaps clip start timestamps to natural sentence beginnings so the Short never starts mid-word or without context.
2. **Zero-Lag Subtitles (`CAPTION_LEAD_OFFSET = 0.38s`)**: Dynamic word-by-word karaoke captions with vocal hit synchronization and safe-zone positioning (`Y=1350`).
3. **YouTube Heatmap Analysis**: Identifies exact timestamps where millions of viewers repeatedly replayed the video.
4. **Lightning-Fast Stream Range Slicing**: Downloads *only* the required 30-50s slice in seconds via stream range slicing without downloading full multi-gigabyte videos.
5. **Dynamic Hook Card**: Auto-generates bold upper banner cards (`Y=240`) based on discussion topic or opening setup sentence.
6. **Loudness Normalization**: FFmpeg EBU R128 (`loudnorm`) filter so speech sounds loud and punchy on mobile speakers.
7. **Auto SEO Metadata**: Generates companion `_metadata.txt` with title, hashtags, description, and creator attribution.

---

## 📁 Project Structure

```
shorts_generator/
│
├── clipper.py            # Main CLI runner for Viral Creator Clipper
├── clip_detector.py      # Heatmap analyzer, comedy scorer & context snappper
├── clip_downloader.py    # Stream range slice downloader (yt-dlp + FFmpeg)
├── clip_compositor.py    # 9:16 vertical layout engine (blur_bg, split_podcast, etc.)
├── clip_subtitles.py     # High-retention zero-lag karaoke ASS subtitle generator
├── creators.py           # 26 popular creator channels registry & alias resolver
├── batch_7_shorts.py     # Automated 7-day batch generator
│
├── generate.py           # Faceless AI short generator (TTS + Stock media)
├── config.py             # Global resolution, fonts, colors, paths
│
└── output/
    └── clips/            # Rendered 1080x1920 MP4 Shorts + companion metadata .txt
```
