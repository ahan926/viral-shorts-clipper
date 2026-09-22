"""Dynamic animated subtitle generator for viral clips.
Extracts subtitles via YouTubeTranscriptApi or Whisper, formats word-level timestamps,
and compiles modern ASS karaoke-style subtitles for mobile Shorts.
"""
from pathlib import Path
from typing import List, Dict, Any, Optional
import re
from youtube_transcript_api import YouTubeTranscriptApi
from config import (
    VIDEO_WIDTH,
    VIDEO_HEIGHT,
    SUBTITLE_FONT,
    SUBTITLE_PRIMARY_COLOR,
    SUBTITLE_HIGHLIGHT_COLOR,
    SUBTITLE_OUTLINE_COLOR,
    SUBTITLE_OUTLINE_WIDTH,
    SUBTITLE_SHADOW_DEPTH,
    CLIP_SUBTITLE_POS_X,
    CLIP_SUBTITLE_POS_Y,
    CLIP_SUBTITLE_FONT_SIZE,
    CAPTION_LEAD_OFFSET,
)

def format_ass_time(seconds: float) -> str:
    """Format seconds into ASS timestamp: H:MM:SS.cc"""
    seconds = max(0.0, seconds)
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centis = int(round((seconds - int(seconds)) * 100))
    if centis >= 100:
        secs += 1
        centis = 0
    return f"{hrs}:{mins:02d}:{secs:02d}.{centis:02d}"

def clean_word(word: str) -> str:
    """Clean punctuation while retaining emphasis."""
    return re.sub(r"[^\w\s'$%!\?]", "", word).strip()

def extract_subtitles_from_youtube(
    video_id: str,
    clip_start_sec: float,
    clip_end_sec: float
) -> List[Dict[str, Any]]:
    """
    Fetches official or auto-generated YouTube subtitles and extracts word-level timings
    relative to the clip's start time (0.0s = clip_start_sec).
    """
    try:
        api = YouTubeTranscriptApi()
        # Try english transcripts (manual or auto-generated)
        transcript_list = api.list(video_id)
        transcript = None
        for t in transcript_list:
            if t.language_code.startswith("en"):
                transcript = t.fetch()
                break
        if not transcript:
            # Fallback to any first transcript
            all_transcripts = list(transcript_list)
            if all_transcripts:
                transcript = all_transcripts[0].fetch()

        if not transcript:
            return []

        raw_snippets = []
        for item in transcript:
            snippet_start = float(item.start)
            snippet_dur = float(item.duration)
            snippet_end = snippet_start + snippet_dur

            # Check overlap with clip window
            if snippet_end < clip_start_sec or snippet_start > clip_end_sec:
                continue

            raw_text = item.text.replace("\n", " ").strip()
            raw_text = re.sub(r"\[.*?\]", "", raw_text).strip()
            raw_text = re.sub(r"^\s*-\s*", "", raw_text).strip()
            if not raw_text:
                continue

            raw_snippets.append({
                "start": snippet_start,
                "dur": snippet_dur,
                "text": raw_text
            })

        if not raw_snippets:
            return []

        # Sort snippets chronologically
        raw_snippets.sort(key=lambda s: s["start"])

        # Truncate overlapping ends across consecutive snippets
        # YouTube auto-captions overlap each snippet by 1-2 seconds; this prevents overlapping text
        for i in range(len(raw_snippets)):
            st = raw_snippets[i]["start"]
            if i + 1 < len(raw_snippets):
                raw_snippets[i]["end"] = min(st + raw_snippets[i]["dur"], raw_snippets[i + 1]["start"])
            else:
                raw_snippets[i]["end"] = st + raw_snippets[i]["dur"]
            if raw_snippets[i]["end"] <= st:
                raw_snippets[i]["end"] = st + 0.5

        clip_duration = clip_end_sec - clip_start_sec
        words_data: List[Dict[str, Any]] = []

        for s in raw_snippets:
            tokens = [t.strip() for t in s["text"].split() if t.strip()]
            if not tokens:
                continue

            # Calculate relative timestamps with lead offset to sync perfectly with spoken voice
            rel_start = max(0.0, s["start"] - clip_start_sec - CAPTION_LEAD_OFFSET)
            rel_end = max(0.1, s["end"] - clip_start_sec - CAPTION_LEAD_OFFSET)
            rel_end = min(clip_duration, rel_end)
            if rel_end <= rel_start:
                continue

            chunk_duration = max(0.2, rel_end - rel_start)
            per_word_duration = chunk_duration / len(tokens)

            for idx, token in enumerate(tokens):
                cleaned = clean_word(token)
                if not cleaned:
                    continue
                w_start = rel_start + (idx * per_word_duration)
                w_end = min(clip_duration, w_start + per_word_duration)
                words_data.append({
                    "word": cleaned,
                    "start": round(w_start, 3),
                    "end": round(w_end, 3)
                })

        # Strict monotonicity pass: Guarantee zero overlap across all consecutive words
        for i in range(len(words_data)):
            if i > 0 and words_data[i]["start"] < words_data[i - 1]["end"]:
                words_data[i]["start"] = words_data[i - 1]["end"]
            if words_data[i]["end"] <= words_data[i]["start"]:
                words_data[i]["end"] = round(words_data[i]["start"] + 0.2, 3)

        return words_data
    except Exception as e:
        print(f"⚠️  Could not fetch YouTube transcript: {e}")
        return []

def chunk_words(words: List[Dict[str, Any]], max_words_per_chunk: int = 2) -> List[List[Dict[str, Any]]]:
    """Groups words into short, rapid bursts (1-2 words) for mobile short retention."""
    chunks = []
    current_chunk = []
    for item in words:
        current_chunk.append(item)
        if len(current_chunk) >= max_words_per_chunk or item["word"].endswith((".", "!", "?")):
            chunks.append(current_chunk)
            current_chunk = []
    if current_chunk:
        chunks.append(current_chunk)
    return chunks

def generate_clip_ass_subtitles(
    words: List[Dict[str, Any]],
    output_ass_path: Path,
    pos_x: int = CLIP_SUBTITLE_POS_X,
    pos_y: int = CLIP_SUBTITLE_POS_Y,
    font_size: int = CLIP_SUBTITLE_FONT_SIZE,
    words_per_phrase: int = 2
) -> Path:
    """
    Creates high-retention karaoke ASS subtitles with active-word pop and color highlight.
    """
    output_ass_path.parent.mkdir(parents=True, exist_ok=True)

    ass_content = [
        "[Script Info]",
        "Title: Viral Shorts Dynamic Captions",
        "ScriptType: v4.00+",
        f"PlayResX: {VIDEO_WIDTH}",
        f"PlayResY: {VIDEO_HEIGHT}",
        "WrapStyle: 0",
        "ScaledBorderAndShadow: yes",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        f"Style: Default,{SUBTITLE_FONT},{font_size},{SUBTITLE_PRIMARY_COLOR},{SUBTITLE_HIGHLIGHT_COLOR},{SUBTITLE_OUTLINE_COLOR},&H80000000,-1,0,0,0,100,100,1,0,1,{SUBTITLE_OUTLINE_WIDTH},{SUBTITLE_SHADOW_DEPTH},5,0,0,0,1",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]

    chunks = chunk_words(words, max_words_per_chunk=words_per_phrase)

    for chunk in chunks:
        if not chunk:
            continue

        # Smooth timings within chunk so words in the same phrase transition seamlessly
        for j in range(len(chunk) - 1):
            if chunk[j]["end"] < chunk[j + 1]["start"] and (chunk[j + 1]["start"] - chunk[j]["end"]) < 0.35:
                chunk[j]["end"] = chunk[j + 1]["start"]

        for i, target_word in enumerate(chunk):
            start_str = format_ass_time(target_word["start"])
            end_str = format_ass_time(target_word["end"])

            tokens = []
            for j, w in enumerate(chunk):
                raw = w["word"].upper()
                if i == j:
                    # Highlight active word in neon yellow with subtle bounce
                    tokens.append(f"{{\\c{SUBTITLE_HIGHLIGHT_COLOR}\\fscx110\\fscy110}}{raw}{{\\fscx100\\fscy100}}")
                else:
                    # Inactive word in solid crisp white
                    tokens.append(f"{{\\c{SUBTITLE_PRIMARY_COLOR}}}{raw}")

            line_text = f"{{\\pos({pos_x},{pos_y})}}" + " ".join(tokens)
            ass_content.append(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{line_text}")

    output_ass_path.write_text("\n".join(ass_content), encoding="utf-8")
    return output_ass_path
