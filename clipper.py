"""Main CLI tool to generate viral YouTube Shorts from popular creators and social media clips."""
import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Optional, List, Dict, Any

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from config import (
    CLIPS_OUTPUT_DIR,
    CLIPS_CACHE_DIR,
    DEFAULT_CLIP_LAYOUT,
    DEFAULT_CLIP_DURATION,
    CLIP_SUBTITLE_POS_Y,
)
import yt_dlp
from creators import get_creator, list_creators, CREATOR_REGISTRY
from clip_detector import extract_video_info, get_viral_segments
from clip_downloader import download_video_segment, trim_local_video
from clip_subtitles import extract_subtitles_from_youtube, generate_clip_ass_subtitles
from clip_compositor import compose_short_clip

def parse_time_str(val: str) -> float:
    """Parses timestamp strings like '14:20', '1:05:30', or '85.5' into seconds."""
    parts = val.strip().split(":")
    if len(parts) == 1:
        return float(parts[0])
    elif len(parts) == 2:
        return int(parts[0]) * 60 + float(parts[1])
    elif len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    raise ValueError(f"Invalid timestamp format: {val}")

def slugify(text: str) -> str:
    """Creates a filesystem-safe filename slug."""
    text = re.sub(r"[^\w\s-]", "", text).strip().lower()
    return re.sub(r"[-\s]+", "_", text)[:40]

def search_viral_video(query: str, min_duration: float = 90.0, max_duration: float = 5400.0) -> Dict[str, Any]:
    """
    Searches YouTube for viral clips, compilations, or stream highlights matching a query.
    Filters out sponsored ads and live streams, prioritizing high view counts and strong viral engagement.
    """
    print(f"🔎 Searching YouTube for viral content: '{query}'...")
    ydl_opts = {
        "skip_download": True,
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        res = ydl.extract_info(f"ytsearch8:{query}", download=False)
        entries = res.get("entries") or []
        if not entries:
            raise ValueError(f"No viral videos found matching query: '{query}'")

        # Score candidates
        candidates = []
        boring_ad_words = ["#ad", "#sponsored", "#partner", "trailer", "teaser"]
        for e in entries:
            t = e.get("title", "")
            t_lower = t.lower()
            if any(b in t_lower for b in boring_ad_words):
                continue

            views = float(e.get("view_count") or 0.0)
            dur = float(e.get("duration") or 300.0)
            if dur < min_duration or dur > max_duration:
                continue

            # Prefer titles mentioning funny/viral/rage/highlights
            viral_score = views
            if any(w in t_lower for w in ["funny", "hilarious", "rage", "stream", "reaction", "fails", "moments"]):
                viral_score *= 1.5

            candidates.append({"entry": e, "score": viral_score})

        if candidates:
            candidates.sort(key=lambda x: x["score"], reverse=True)
            chosen = candidates[0]["entry"]
        else:
            chosen = entries[0]

        chosen_title = chosen.get("title", "").encode("ascii", "replace").decode()
        print(f"   ✨ Selected: '{chosen_title}'")
        return chosen

def get_latest_creator_video(channel_url: str) -> Dict[str, Any]:
    """Retrieves the best recent video from a creator's channel, filtering out ads and shorts."""
    print(f"🔍 Inspecting recent uploads from creator channel: {channel_url}...")
    ydl_opts = {
        "skip_download": True,
        "playlist_items": "1-5",
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        res = ydl.extract_info(channel_url, download=False)
        entries = res.get("entries") or []
        if not entries:
            raise ValueError(f"No videos found for channel {channel_url}")

        boring_words = ["#ad", "#sponsored", "#partner", "trailer", "announcement"]
        for e in entries:
            t_lower = (e.get("title") or "").lower()
            if not any(b in t_lower for b in boring_words):
                return e
        return entries[0]

def get_entertaining_creator_video(
    creator_data: Dict[str, Any],
    query: Optional[str] = None,
    funny_mode: bool = False,
    recent_only: bool = False
) -> Dict[str, Any]:
    """
    Finds the most entertaining, hilarious, or viral video for a given creator.
    For streamers and comedians, automatically searches for top viral stream moments and compilations.
    """
    c_name = creator_data["name"]
    category = creator_data.get("category", "")
    is_streamer = "Streaming" in category or "Gaming" in category or "Comedy" in category

    # 1. User specific topic query
    if query:
        return search_viral_video(f"{c_name} {query}")

    # 2. Funny / Streamer mode: search for top viral stream highlights & funny compilations
    if (funny_mode or is_streamer) and not recent_only:
        try:
            return search_viral_video(f"{c_name} funniest viral stream moments reaction")
        except Exception:
            pass

    # 3. Channel uploads inspection
    return get_latest_creator_video(creator_data["channel_url"])

def generate_metadata_file(
    output_txt_path: Path,
    video_title: str,
    creator_name: str,
    original_url: str,
    hashtags: List[str],
    hook_text: Optional[str] = None
) -> None:
    """Generates an SEO-optimized companion metadata file for YouTube upload."""
    title_hook = hook_text if hook_text else video_title
    short_title = f"{title_hook[:60]} 🤯 #shorts"
    tags_str = " ".join(hashtags) if hashtags else "#shorts #viral #podcast"
    
    content = f"""Title:
{short_title}

Description:
Unbelievable moment from {creator_name}! 

Watch the full video: {original_url}
Clip from: {video_title}

{tags_str}

Tags:
youtube shorts, viral clips, {creator_name.lower()}, trending, highlights
"""
    output_txt_path.write_text(content, encoding="utf-8")

def process_single_clip(
    url: str,
    video_info: Dict[str, Any],
    start_sec: float,
    end_sec: float,
    clip_index: int,
    layout: str,
    hook_text: Optional[str] = None,
    with_subtitles: bool = True,
    creator_data: Optional[Dict[str, Any]] = None,
    sub_y: Optional[int] = None
) -> Path:
    """End-to-end processing pipeline for an individual viral clip."""
    video_id = video_info.get("id") or "clip"
    raw_title = video_info.get("title") or "Viral Moment"
    duration = end_sec - start_sec
    slug = slugify(f"{raw_title}_{clip_index}")
    
    work_dir = CLIPS_CACHE_DIR / f"{video_id}_{clip_index}_{int(time.time())}"
    work_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n=======================================================")
    print(f"🎬 Processing Short #{clip_index}: [{start_sec:.1f}s -> {end_sec:.1f}s] ({duration:.1f}s)")
    print(f"   Source Video: {raw_title}")
    print(f"   Layout Mode:  {layout}")
    print(f"=======================================================")

    # 1. Download Segment
    raw_clip_path = work_dir / "raw_segment.mp4"
    download_video_segment(url, start_sec, end_sec, raw_clip_path, video_title=raw_title)

    # 2. Subtitles
    sub_path = None
    if with_subtitles and video_id:
        print("📝 Fetching transcript & generating dynamic subtitles...")
        words = extract_subtitles_from_youtube(video_id, start_sec, end_sec)
        if words:
            sub_path = work_dir / "clip_subtitles.ass"
            # Set subtitle position in safe zone (Y=1350) or user override
            target_pos_y = sub_y if sub_y is not None else CLIP_SUBTITLE_POS_Y
            generate_clip_ass_subtitles(words, sub_path, pos_y=target_pos_y, words_per_phrase=3)
            print(f"   Generated {len(words)} animated subtitle words!")
        else:
            print("   (No captions available for this segment — continuing without subtitles)")

    # 3. Determine Hook Text
    if not hook_text:
        if creator_data:
            hook_text = f"{creator_data['name'].upper()}: {raw_title[:28]}"
        else:
            hook_text = raw_title[:32].upper()

    # 4. Compose Vertical 9:16 Short
    final_output = CLIPS_OUTPUT_DIR / f"{slug}.mp4"
    compose_short_clip(
        input_clip_path=raw_clip_path,
        output_mp4_path=final_output,
        layout=layout,
        subtitle_ass_path=sub_path,
        hook_text=hook_text,
        duration_sec=duration
    )

    # 5. Export YouTube Metadata
    meta_txt = CLIPS_OUTPUT_DIR / f"{slug}_metadata.txt"
    creator_name = creator_data["name"] if creator_data else "Creator"
    hashtags = creator_data.get("hashtags", ["#shorts", "#viral"]) if creator_data else ["#shorts", "#viral"]
    generate_metadata_file(
        meta_txt,
        video_title=raw_title,
        creator_name=creator_name,
        original_url=url,
        hashtags=hashtags,
        hook_text=hook_text
    )
    print(f"📄 Metadata saved to: {meta_txt.name}")

    return final_output

def main():
    parser = argparse.ArgumentParser(
        description="🔥 Automated Viral YouTube Shorts Clipper for Popular Social Media Creators"
    )
    parser.add_argument("--url", type=str, help="YouTube video or clip URL to process")
    parser.add_argument("--creator", type=str, help="Popular creator preset (e.g., rogan, mrbeast, huberman, theovon, speed, kaicenat, caseoh, asmongold)")
    parser.add_argument("--list-creators", action="store_true", help="List all available creator presets")
    parser.add_argument("--auto", action="store_true", help="Automatically detect viral highlights using YouTube engagement heatmap")
    parser.add_argument("--funny", action="store_true", help="Search for the most hilarious stream/reaction moments and score for laughter/rage")
    parser.add_argument("--query", type=str, help="Search for specific viral topic, guest, or moment (e.g., 'rage', 'fails', 'druski', 'kevin hart')")
    parser.add_argument("--recent", action="store_true", help="Strictly use the most recent upload from the creator's channel rather than searching viral highlights")
    parser.add_argument("--count", type=int, default=1, help="Number of viral shorts to generate (default: 1)")
    parser.add_argument("--start", type=str, help="Manual start time (e.g., '14:20' or '860')")
    parser.add_argument("--end", type=str, help="Manual end time (e.g., '15:05' or '905')")
    parser.add_argument("--duration", type=float, default=DEFAULT_CLIP_DURATION, help="Clip duration in seconds (default: 45)")
    parser.add_argument("--layout", type=str, choices=["blur_bg", "split_podcast", "face_crop"], help="Vertical layout framing")
    parser.add_argument("--hook", type=str, help="Custom top hook banner text (e.g., 'HE CANNOT BELIEVE THIS 🤯')")
    parser.add_argument("--sub-y", type=int, default=None, help="Vertical Y position for subtitles (default: 1350 in safe zone)")
    parser.add_argument("--no-subs", action="store_true", help="Disable dynamic subtitles")
    parser.add_argument("--file", type=str, help="Path to local video file instead of URL")

    args = parser.parse_args()

    if args.list_creators:
        print("\n🌟 Available Popular Creator Presets:")
        print("---------------------------------------------------------------")
        for c in list_creators():
            print(f"  • {c['key']:<14} | {c['name']:<24} | Default Layout: {c['layout']}")
        print("---------------------------------------------------------------")
        print("Usage: uv run python clipper.py --creator <key> --auto\n")
        return

    # Sourcing
    url = args.url
    creator_data = None

    if args.creator:
        creator_data = get_creator(args.creator)
        if not creator_data:
            print(f"❌ Error: Creator preset '{args.creator}' not found. Run --list-creators to view options.")
            sys.exit(1)
        print(f"🎯 Target Creator: {creator_data['name']} ({creator_data['category']})")
        if not url:
            selected_video = get_entertaining_creator_video(
                creator_data,
                query=args.query,
                funny_mode=args.funny,
                recent_only=args.recent
            )
            url = selected_video.get("webpage_url") or f"https://www.youtube.com/watch?v={selected_video['id']}"
            vid_title = selected_video.get("title", "").encode("ascii", "replace").decode()
            print(f"   🎬 Selected Source Video: '{vid_title}'")

    if not url and not args.file:
        print("❌ Error: You must provide either --url, --creator, or --file.")
        parser.print_help()
        sys.exit(1)

    # Selected layout
    layout = args.layout
    if not layout:
        if creator_data:
            layout = creator_data.get("default_layout", DEFAULT_CLIP_LAYOUT)
        else:
            layout = DEFAULT_CLIP_LAYOUT

    # Process Local File
    if args.file:
        local_p = Path(args.file)
        if not local_p.exists():
            print(f"❌ Error: Local file '{args.file}' does not exist.")
            sys.exit(1)
        st = parse_time_str(args.start) if args.start else 0.0
        et = parse_time_str(args.end) if args.end else (st + args.duration)
        trimmed = CLIPS_CACHE_DIR / f"trimmed_{local_p.stem}.mp4"
        trim_local_video(local_p, st, et, trimmed)
        out = CLIPS_OUTPUT_DIR / f"{local_p.stem}_short.mp4"
        compose_short_clip(
            input_clip_path=trimmed,
            output_mp4_path=out,
            layout=layout,
            hook_text=args.hook or local_p.stem.replace("_", " ").upper(),
            duration_sec=et - st
        )
        print(f"\n🎉 Short successfully created: {out.resolve()}")
        return

    # Extract Video Metadata
    print(f"\n📊 Fetching video metadata and engagement curves...")
    video_info = extract_video_info(url)
    total_dur = float(video_info.get("duration") or 300.0)
    raw_title = video_info.get("title") or "Viral Moment"
    clean_title = raw_title.encode("ascii", "replace").decode()
    print(f"   Video: '{clean_title}' ({total_dur/60:.1f} minutes)")

    # Segments Detection
    segments = []
    is_streamer_or_comedy = creator_data and (
        "Streaming" in creator_data.get("category", "") or
        "Gaming" in creator_data.get("category", "") or
        "Comedy" in creator_data.get("category", "")
    )
    detect_mode = "funny" if (args.funny or is_streamer_or_comedy) else "viral"

    if args.start:
        st = parse_time_str(args.start)
        et = parse_time_str(args.end) if args.end else (st + args.duration)
        segments.append({"index": 1, "start": st, "end": et, "duration": et - st})
    elif args.auto or not args.start:
        mode_desc = "hilarious & viral comedy moments" if detect_mode == "funny" else "viral engagement moments"
        print(f"🔥 Detecting top {args.count} {mode_desc} with conversational context snapping...")
        segments = get_viral_segments(video_info, clip_duration=args.duration, count=args.count, mode=detect_mode)
        for s in segments:
            m, sec = divmod(int(s['start']), 60)
            score_desc = f"(Score: {s.get('score', 0):.2f})" if s.get('score') else ""
            topic_label = f"| '{s.get('title')}'" if s.get('title') else ""
            print(f"   ✨ Moment #{s['index']}: {m:02d}:{sec:02d} - {s['duration']:.0f}s {score_desc} {topic_label}")

    # Generate Shorts
    created_shorts = []
    for seg in segments:
        topic_hook = args.hook or seg.get("title") or seg.get("context_text")
        if not topic_hook and creator_data:
            topic_hook = f"{creator_data['name'].upper()}: {raw_title[:28]}"

        out_mp4 = process_single_clip(
            url=url,
            video_info=video_info,
            start_sec=seg["start"],
            end_sec=seg["end"],
            clip_index=seg["index"],
            layout=layout,
            hook_text=topic_hook,
            with_subtitles=not args.no_subs,
            creator_data=creator_data,
            sub_y=args.sub_y
        )
        created_shorts.append(out_mp4)

    print("\n=======================================================")
    print(f"🎉 Complete! Successfully generated {len(created_shorts)} viral YouTube Shorts:")
    for s in created_shorts:
        print(f"   👉 {s.resolve()}")
    print("=======================================================\n")

if __name__ == "__main__":
    main()
