"""Viral segment detection engine.
Analyzes YouTube engagement heatmaps (most-replayed curve), video chapters,
and transcripts to identify high-retention viral moments for YouTube Shorts.
"""
from typing import List, Dict, Any, Optional, Tuple
import math
import re
import json
from pathlib import Path
from config import CACHE_DIR
import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi

BORING_CHAPTER_KEYWORDS = [
    "intro", "introduction", "sponsor", "sponsors", "sponsored", "advertisement",
    "ad", "outro", "newsletter", "supplements", "support", "merch", "disclaimer",
    "thank you", "credits", "preview", "coming up"
]

VIRAL_TOPIC_KEYWORDS = [
    # Health & Science
    "weight loss", "fat loss", "diet", "fasting", "intermittent fasting", "gut",
    "cancer", "muscle", "metabolic", "sugar", "insulin", "glp-1", "food", "hunger",
    "sweeteners", "microbiome", "ulcers", "sleep", "dopamine", "testosterone",
    "brain", "aging", "longevity", "cardio", "protein", "cholesterol",
    # Mind & Psychology
    "lobotomy", "asylums", "psychiatry", "mental illness", "depression", "anxiety",
    "trauma", "freud", "jung", "addiction", "narcissist", "psychopath", "therapy",
    # Wealth & Power
    "money", "wealth", "million", "billion", "rich", "extreme wealth", "invest",
    "business", "economy", "crypto", "real estate", "law changed", "tax",
    # Curiosity & Shock
    "secret", "truth", "lie", "exposed", "crazy", "insane", "worst", "best",
    "shocking", "danger", "died", "death", "prison", "crime", "alien", "ufo",
    "conspiracy", "never", "mistake", "warning", "fight", "brawl", "wild"
]

COMEDY_VIRAL_KEYWORDS = [
    # Laughter & Amusement
    "laughter", "laugh", "laughing", "crying", "tears", "dead", "lmao", "lmfao",
    "hahaha", "cant breathe", "can't breathe", "dying", "funny", "hilarious",
    # Streamer Shock, Disbelief & Rage
    "aint no way", "ain't no way", "bro what", "what did you say", "chat is this real",
    "are you serious", "are you kidding me", "stop the cap", "no way no way",
    "hold on hold on", "wait wait wait", "look at this dude", "who is that", "what is that",
    "rage", "screaming", "freak out", "crash out", "slams desk", "banned", "troll", "trolling",
    "jump scare", "scared", "cooked", "roasted", "caught in 4k", "bruh", "nahhh",
    "what's up brother", "slap", "fight", "freaking out", "what the fuck", "what the hell",
    "oh my god", "holy shit", "loses it", "devil's lettuce", "hang themselves"
]

def count_keyword_matches(text: str, keywords: List[str]) -> int:
    """Counts whole-word occurrences of keywords to prevent false substring matches (e.g. 'sus' in 'Jesus')."""
    text_lower = text.lower()
    count = 0
    for kw in keywords:
        pattern = r'\b' + re.escape(kw.lower()) + r'\b'
        if re.search(pattern, text_lower):
            count += 1
    return count

def truncate_word_safe(text: str, max_chars: int = 42) -> str:
    """Truncates text at whole-word boundaries without chopping words in half."""
    clean = re.sub(r"\[.*?\]", "", text)
    clean = " ".join(clean.strip().split())
    if len(clean) <= max_chars:
        return clean.strip(" ,;:-.")
    chopped = clean[:max_chars]
    last_space = chopped.rfind(" ")
    if last_space > 15:
        chopped = chopped[:last_space]
    return chopped.strip(" ,;:-.")

def generate_smart_hook(
    video_title: str,
    creator_name: Optional[str] = None,
    context_text: Optional[str] = None,
    mode: str = "viral"
) -> str:
    """
    Generates a punchy, human-styled 3-6 word viral hook banner for mobile Shorts.
    Never truncates words mid-syllable, and formats with high-converting emojis.
    """
    clean_t = re.sub(r"(?i)\s*(\||\-|\—)\s*(asmongold tv|asmongold|by asmonboy|stream vod|full stream|episode \d+|ep \d+|part \d+|twitch|youtube).*", "", video_title).strip()
    clean_t = re.sub(r"\[.*?\]|\(.*?\)", "", clean_t).strip()
    clean_t = " ".join(clean_t.split())

    viral_signals = [
        "loses it", "funniest", "best video", "cant believe", "can't believe",
        "insane", "crazy", "rage", "crying", "dies laughing", "what is this",
        "reacts", "worst", "fails", "exposed", "caught", "screaming", "unbelievable"
    ]
    has_strong_title = any(sig in clean_t.lower() for sig in viral_signals)

    if has_strong_title and len(clean_t) >= 10:
        hook_candidate = truncate_word_safe(clean_t, max_chars=58)
    elif context_text and len(context_text) >= 8:
        hook_candidate = truncate_word_safe(context_text, max_chars=55)
    else:
        hook_candidate = truncate_word_safe(clean_t or "VIRAL MOMENT", max_chars=55)

    if creator_name and creator_name.lower() not in hook_candidate.lower() and len(hook_candidate) < 26:
        hook_candidate = f"{creator_name.upper()}: {hook_candidate}"

    hook_candidate = hook_candidate.upper().strip(" ,;:-.")
    has_emoji = any(char in hook_candidate for char in ["💀", "😂", "😭", "🤯", "🔥", "👀"])
    if not has_emoji:
        emoji = "😂" if mode == "funny" else "🤯"
        hook_candidate = f"{hook_candidate} {emoji}"

    return hook_candidate

def extract_video_info(url_or_id: str) -> Dict[str, Any]:
    """Fetches video metadata including heatmap and chapters without downloading media."""
    ydl_opts = {
        "skip_download": True,
        "quiet": True,
        "no_warnings": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url_or_id, download=False)
        return info

def fetch_transcript_safe(video_id: str) -> List[Dict[str, Any]]:
    """Safely retrieves raw transcript snippets as simple dictionaries with disk caching."""
    if not video_id:
        return []

    cache_file = CACHE_DIR / "transcripts" / f"{video_id}.json"
    if cache_file.exists():
        try:
            return json.loads(cache_file.read_text(encoding="utf-8"))
        except Exception:
            pass

    try:
        api = YouTubeTranscriptApi()
        t_list = api.list(video_id)
        chosen = None
        for t in t_list:
            if t.language_code.startswith("en"):
                chosen = t
                break
        if not chosen:
            all_t = list(t_list)
            if all_t:
                chosen = all_t[0]
        if chosen:
            raw = chosen.fetch()
            data = [
                {
                    "start": float(x.start),
                    "dur": float(x.duration),
                    "text": x.text.replace("\n", " ").strip()
                }
                for x in raw
            ]
            cache_file.parent.mkdir(parents=True, exist_ok=True)
            cache_file.write_text(json.dumps(data), encoding="utf-8")
            return data
    except Exception:
        pass
    return []

def snap_to_sentence_context(
    snippets: List[Dict[str, Any]],
    target_start: float,
    clip_duration: float,
    total_duration: float
) -> Tuple[float, float, Optional[str]]:
    """
    Snaps a target timestamp to a natural sentence/conversational setup boundary
    so the Short never starts mid-sentence with no context.
    """
    if not snippets:
        st = max(0.0, target_start)
        et = min(total_duration, st + clip_duration)
        return round(st, 2), round(et, 2), None

    best_start = target_start
    best_score = -999.0
    context_text = None

    hook_triggers = [
        "wait", "bro", "look", "why", "what", "how", "did", "are you", "aint no way",
        "chat", "so", "listen", "can i", "let me", "i said", "he said", "she said",
        "no way", "hold up", "who", "when", "tell me", "watch this", "somebody",
        "name three", "okay", "jesus christ", "did you say"
    ]

    # Look for the natural setup sentence in expanded window [target_start - 20s, target_start + 4s]
    for i, s in enumerate(snippets):
        st = s["start"]
        if target_start - 20.0 <= st <= target_start + 4.0:
            score = 0.0
            if i > 0:
                prev = snippets[i - 1]
                prev_end = prev["start"] + prev["dur"]
                gap = st - prev_end
                # Natural pause in speech
                if gap >= 0.35:
                    score += 3.5
                # Previous sentence ended with punctuation
                if any(prev["text"].endswith(p) for p in [".", "?", "!"]):
                    score += 4.0

            # Hook/premise starter words
            first_words = s["text"].lower().split()[:3]
            fw_str = " ".join(first_words)
            if any(fw_str.startswith(tr) for tr in hook_triggers):
                score += 3.5

            # Question marks in snippet signify setup
            if "?" in s["text"]:
                score += 2.0

            # Closeness penalty
            dist = abs(st - target_start)
            score -= (dist * 0.20)

            if score > best_score:
                best_score = score
                best_start = st
                clean_snippet = re.sub(r"\[.*?\]", "", s["text"]).strip()
                if len(clean_snippet) > 8:
                    context_text = truncate_word_safe(clean_snippet, max_chars=40)

    # Determine optimal end time matching a completed sentence
    desired_end = best_start + clip_duration
    best_end = desired_end
    end_score = -999.0

    for s in snippets:
        s_end = s["start"] + s["dur"]
        if desired_end - 6.0 <= s_end <= desired_end + 6.0:
            score = 0.0
            if any(s["text"].endswith(p) for p in [".", "?", "!"]):
                score += 4.0
            dist = abs(s_end - desired_end)
            score -= (dist * 0.2)
            if score > end_score:
                end_score = score
                best_end = s_end

    final_start = max(0.0, best_start)
    final_end = min(total_duration, max(final_start + 18.0, best_end))
    return round(final_start, 2), round(final_end, 2), context_text

def find_matching_chapter(timestamp: float, chapters: List[Dict[str, Any]]) -> Optional[str]:
    """Finds the chapter title that contains a given timestamp."""
    if not chapters:
        return None
    for ch in chapters:
        st = float(ch.get("start_time", 0.0))
        et = float(ch.get("end_time", st + 9999))
        if st <= timestamp <= et:
            title = ch.get("title", "").strip()
            # If title is not boring, return it
            if not any(b in title.lower() for b in BORING_CHAPTER_KEYWORDS):
                return title
    return None

def detect_segments_from_heatmap(
    heatmap: List[Dict[str, Any]],
    total_duration: float,
    clip_duration: float = 35.0,
    count: int = 1,
    min_separation: float = 90.0,
    chapters: Optional[List[Dict[str, Any]]] = None,
    snippets: Optional[List[Dict[str, Any]]] = None,
    mode: str = "viral"
) -> List[Dict[str, Any]]:
    """
    Finds the top N distinct viral peaks from the YouTube engagement heatmap,
    scoring for comedy/laughter when mode='funny', and snapping boundaries to full sentence context.
    """
    if not heatmap:
        return []

    # Filter out initial video intro (first 2.5 minutes) for videos > 5 minutes
    candidates = []
    min_start_cutoff = 150.0 if total_duration > 300 else 15.0
    max_end_cutoff = max(min_start_cutoff + clip_duration, total_duration - 35.0)

    for point in heatmap:
        st = float(point.get("start_time", 0.0))
        val = float(point.get("value", 0.0))
        if min_start_cutoff <= st <= max_end_cutoff:
            score = val
            # If in funny mode and transcript is available, boost moments with laughter or comedy phrases
            if mode == "funny" and snippets:
                comedy_hits = 0
                for s in snippets:
                    if st - 20.0 <= s["start"] <= st + 25.0:
                        comedy_hits += count_keyword_matches(s["text"], COMEDY_VIRAL_KEYWORDS)
                score += (min(10, comedy_hits) * 0.75)

            candidates.append({"start_time": st, "value": score, "raw_heat": val})

    if not candidates:
        candidates = [{"start_time": float(p.get("start_time", 0.0)), "value": float(p.get("value", 0.0)), "raw_heat": float(p.get("value", 0.0))} for p in heatmap]

    # Sort descending by viewer replay intensity + comedy score
    candidates.sort(key=lambda x: x["value"], reverse=True)

    selected_peaks = []
    for cand in candidates:
        cand_time = cand["start_time"]
        too_close = any(abs(cand_time - p["start_time"]) < min_separation for p in selected_peaks)
        if not too_close:
            selected_peaks.append(cand)
            if len(selected_peaks) >= count:
                break

    if len(selected_peaks) < count and candidates:
        for cand in candidates:
            if cand not in selected_peaks:
                selected_peaks.append(cand)
                if len(selected_peaks) >= count:
                    break

    segments = []
    for idx, peak in enumerate(selected_peaks):
        peak_time = peak["start_time"]
        
        # Position peak ~45% into the Short for optimal setup & reaction delivery
        ideal_start = max(0.0, peak_time - (clip_duration * 0.45))
        if ideal_start + clip_duration > total_duration:
            ideal_start = max(0.0, total_duration - clip_duration)
            
        # Snap start and end times to natural sentence context boundaries
        if snippets:
            start_sec, end_sec, context_hook = snap_to_sentence_context(
                snippets, ideal_start, clip_duration, total_duration
            )
        else:
            start_sec = round(ideal_start, 2)
            end_sec = round(min(total_duration, start_sec + clip_duration), 2)
            context_hook = None
        
        # Try to find a human-readable topic title from video chapters
        chapter_title = find_matching_chapter(peak_time, chapters or [])
        display_title = chapter_title or context_hook
        
        segments.append({
            "index": idx + 1,
            "start": start_sec,
            "end": end_sec,
            "duration": round(end_sec - start_sec, 2),
            "peak_time": round(peak_time, 2),
            "score": round(peak["value"], 3),
            "title": display_title,
            "context_text": context_hook,
            "method": "heatmap"
        })

    return segments

def detect_segments_from_chapters(
    chapters: List[Dict[str, Any]],
    total_duration: float,
    clip_duration: float = 35.0,
    count: int = 1
) -> List[Dict[str, Any]]:
    """Identifies viral segments based on high-interest chapter topics."""
    if not chapters:
        return []

    min_start = 90.0 if total_duration > 300 else 15.0
    scored_chapters = []

    for ch in chapters:
        title_raw = ch.get("title", "").strip()
        title_lower = title_raw.lower()
        st = float(ch.get("start_time", 0.0))
        et = float(ch.get("end_time", st + clip_duration))

        # Skip intro, sponsor reads, or early dead-zone
        if st < min_start or any(b in title_lower for b in BORING_CHAPTER_KEYWORDS):
            continue

        score = 0
        for kw in VIRAL_TOPIC_KEYWORDS:
            if kw in title_lower:
                score += 3

        # Add score for optimal chapter duration (2 to 10 mins)
        dur = et - st
        if 90 <= dur <= 600:
            score += 1

        scored_chapters.append({
            "title": title_raw,
            "start": st,
            "end": et,
            "score": score
        })

    if not scored_chapters:
        # Relax filter if all chapters were filtered
        for ch in chapters:
            if ch.get("start_time", 0) >= min_start:
                scored_chapters.append({
                    "title": ch.get("title", "Highlight"),
                    "start": float(ch.get("start_time", 0)),
                    "end": float(ch.get("end_time", 0)),
                    "score": 1
                })

    scored_chapters.sort(key=lambda x: x["score"], reverse=True)

    segments = []
    for idx, ch in enumerate(scored_chapters[:count]):
        # Start 12-18 seconds into the chapter where the core discussion begins
        ch_dur = ch["end"] - ch["start"]
        offset = 15.0 if ch_dur > 45 else 0.0
        st = min(ch["start"] + offset, total_duration - clip_duration)
        st = max(0.0, st)
        et = min(total_duration, st + clip_duration)
        
        segments.append({
            "index": idx + 1,
            "start": round(st, 2),
            "end": round(et, 2),
            "duration": round(et - st, 2),
            "title": ch["title"],
            "score": ch["score"],
            "method": "chapter"
        })
    return segments

def detect_segments_from_transcript(
    video_id: str,
    total_duration: float,
    clip_duration: float = 35.0,
    count: int = 1,
    snippets: Optional[List[Dict[str, Any]]] = None,
    mode: str = "viral"
) -> List[Dict[str, Any]]:
    """Scans transcript for high-energy dialogue spikes (laughter, shock phrases, comedy, questions, and pace)."""
    transcript = snippets or fetch_transcript_safe(video_id)
    if not transcript:
        return []

    min_start = 120.0 if total_duration > 300 else 15.0
    max_start = max(min_start + clip_duration, total_duration - 60.0)

    # Sliding window search (every 15s step)
    window_step = 15.0
    best_windows = []

    cur_t = min_start
    while cur_t <= max_start:
        win_end = cur_t + clip_duration
        # Gather text in window
        text_tokens = []
        for item in transcript:
            it_st = float(item["start"])
            if it_st >= cur_t and it_st <= win_end:
                text_tokens.extend(item["text"].replace("\n", " ").split())

        raw_str = " ".join(text_tokens).lower()
        score = 0.0

        # Laughter & Comedy weight
        if mode == "funny":
            score += count_keyword_matches(raw_str, COMEDY_VIRAL_KEYWORDS) * 4.5
        else:
            score += count_keyword_matches(raw_str, COMEDY_VIRAL_KEYWORDS[:12]) * 2.5

        # Questions and excitement
        score += raw_str.count("?") * 2.0
        score += raw_str.count("!") * 2.5

        # Viral topic triggers
        score += count_keyword_matches(raw_str, VIRAL_TOPIC_KEYWORDS) * 2.0

        # Speech pace (words per second) - streamers talk fast during intense/funny moments
        wps = len(text_tokens) / max(1.0, clip_duration)
        if 2.8 <= wps <= 5.5:
            score += 3.0

        best_windows.append({"start": cur_t, "end": win_end, "score": score})
        cur_t += window_step

    best_windows.sort(key=lambda w: w["score"], reverse=True)
    segments = []
    for idx, win in enumerate(best_windows[:count]):
        # Snap start and end to natural sentence setup
        st, et, context_hook = snap_to_sentence_context(
            transcript, win["start"], clip_duration, total_duration
        )
        segments.append({
            "index": idx + 1,
            "start": st,
            "end": et,
            "duration": round(et - st, 2),
            "score": round(win["score"], 2),
            "title": context_hook or "Viral Moment",
            "context_text": context_hook,
            "method": "transcript"
        })
    return segments

def get_viral_segments(
    info: Dict[str, Any],
    clip_duration: float = 35.0,
    count: int = 1,
    min_separation: float = 90.0,
    mode: str = "viral"
) -> List[Dict[str, Any]]:
    """
    Main detection pipeline:
    1. Fetches transcript to enable conversational context snapping and comedy scoring.
    2. Evaluates YouTube heatmap engagement peaks with comedy scoring & context snapping.
    3. Falls back to smart chapter topic scoring (skipping sponsors/intros).
    4. Falls back to high-energy transcript search (laughter, shock phrases).
    5. Falls back to golden ratio intervals snapped to sentences.
    """
    total_duration = float(info.get("duration") or 300.0)
    clip_duration = min(clip_duration, total_duration)
    chapters = info.get("chapters") or []
    video_id = info.get("id") or ""

    # Fetch transcript once for boundary snapping and comedy analysis
    snippets = fetch_transcript_safe(video_id) if video_id else []

    # 1. Try Heatmap (with chapters & context snapping)
    heatmap = info.get("heatmap") or []
    if heatmap:
        segments = detect_segments_from_heatmap(
            heatmap, total_duration, clip_duration=clip_duration,
            count=count, min_separation=min_separation, chapters=chapters,
            snippets=snippets, mode=mode
        )
        if segments:
            return segments

    # 2. Try Transcript Comedy & Intensity Search (especially powerful for streamers with no chapters/heatmap)
    if snippets:
        segments = detect_segments_from_transcript(
            video_id, total_duration, clip_duration=clip_duration, count=count,
            snippets=snippets, mode=mode
        )
        if segments:
            return segments

    # 3. Try Chapters (with viral keyword scoring)
    if chapters:
        segments = detect_segments_from_chapters(
            chapters, total_duration, clip_duration=clip_duration, count=count
        )
        if segments:
            # Snap chapters to sentence context if transcript available
            for s in segments:
                if snippets:
                    st, et, context_hook = snap_to_sentence_context(
                        snippets, s["start"], clip_duration, total_duration
                    )
                    s["start"], s["end"] = st, et
                    s["duration"] = round(et - st, 2)
                    if not s.get("title") and context_hook:
                        s["title"] = context_hook
            return segments

    # 4. Fallback: Snapped intervals (safe for both short and long videos)
    segments = []
    if total_duration <= clip_duration + 5.0:
        st = 0.0
        et = total_duration
        if snippets:
            st, et, context_hook = snap_to_sentence_context(snippets, st, clip_duration, total_duration)
            title = context_hook
        else:
            title = None
        segments.append({
            "index": 1,
            "start": round(st, 2),
            "end": round(et, 2),
            "duration": round(et - st, 2),
            "score": 0.8,
            "title": title,
            "method": "short_video_direct"
        })
        return segments

    splits = [0.35, 0.55, 0.72, 0.15]
    min_start_limit = 30.0 if total_duration > 180 else 0.0
    for i in range(min(count, len(splits))):
        target_s = max(0.0, (total_duration - clip_duration) * splits[i])
        st = max(min_start_limit, target_s)
        et = min(total_duration, st + clip_duration)
        if snippets:
            st, et, context_hook = snap_to_sentence_context(
                snippets, st, clip_duration, total_duration
            )
            title = context_hook
        else:
            title = None

        segments.append({
            "index": i + 1,
            "start": round(st, 2),
            "end": round(et, 2),
            "duration": round(et - st, 2),
            "score": 0.5,
            "title": title,
            "method": "fallback"
        })

    return segments
