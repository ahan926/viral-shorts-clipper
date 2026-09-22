"""Batch generator to automatically produce a 7-day schedule of viral YouTube Shorts."""
import sys
import time
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import config
from creators import get_creator
from clip_detector import extract_video_info, get_viral_segments
from clipper import get_latest_creator_video, process_single_clip

SCHEDULE_PLAN = [
    {"day": "Day 1 (Monday)", "creator": "rogan", "duration": 35, "layout": "blur_bg"},
    {"day": "Day 2 (Tuesday)", "creator": "mrbeast", "duration": 30, "layout": "blur_bg"},
    {"day": "Day 3 (Wednesday)", "creator": "theovon", "duration": 35, "layout": "blur_bg"},
    {"day": "Day 4 (Thursday)", "creator": "huberman", "duration": 35, "layout": "blur_bg"},
    {"day": "Day 5 (Friday)", "creator": "lexfridman", "duration": 35, "layout": "blur_bg"},
    {"day": "Day 6 (Saturday)", "creator": "modernwisdom", "duration": 35, "layout": "blur_bg"},
    {"day": "Day 7 (Sunday)", "creator": "kaicenat", "duration": 30, "layout": "blur_bg"},
]

def run_batch():
    print("==================================================================")
    print("🚀 STARTING 7-DAY VIRAL YOUTUBE SHORTS BATCH GENERATION")
    print("==================================================================")
    
    generated_shorts = []
    start_all = time.time()

    for i, item in enumerate(SCHEDULE_PLAN, 1):
        creator_key = item["creator"]
        day_label = item["day"]
        duration = item["duration"]
        layout = item["layout"]

        print(f"\n------------------------------------------------------------------")
        print(f"📦 [{i}/7] Producing Short for {day_label}: Creator preset '{creator_key}'")
        print(f"------------------------------------------------------------------")

        creator_data = get_creator(creator_key)
        if not creator_data:
            print(f"⚠️ Warning: Creator '{creator_key}' not found. Skipping.")
            continue

        try:
            # 1. Fetch latest video
            latest = get_latest_creator_video(creator_data["channel_url"])
            url = latest.get("webpage_url") or f"https://www.youtube.com/watch?v={latest['id']}"
            print(f"   Video: '{latest.get('title')}'")

            # 2. Extract metadata & heatmap
            video_info = extract_video_info(url)
            segments = get_viral_segments(video_info, clip_duration=duration, count=1)
            
            if not segments:
                print(f"⚠️ No segments detected for {url}. Skipping.")
                continue

            seg = segments[0]
            print(f"   Viral Peak: {int(seg['start'])//60:02d}:{int(seg['start'])%60:02d} (Score: {seg.get('score', 0):.2f})")
            if seg.get("title"):
                print(f"   Detected Topic: '{seg['title']}'")

            # 3. Process and render
            topic_hook = seg.get("title") or f"{creator_data['name'].upper()}: {video_info.get('title', '')[:28]}"

            out_mp4 = process_single_clip(
                url=url,
                video_info=video_info,
                start_sec=seg["start"],
                end_sec=seg["end"],
                clip_index=i,
                layout=layout,
                hook_text=topic_hook,
                with_subtitles=True,
                creator_data=creator_data,
                sub_y=config.CLIP_SUBTITLE_POS_Y
            )
            generated_shorts.append({"day": day_label, "creator": creator_data["name"], "path": out_mp4})
            print(f"   ✅ Short #{i} completed successfully!")

        except Exception as e:
            print(f"❌ Error generating Short for {creator_key}: {e}")

    total_time = time.time() - start_all
    print("\n==================================================================")
    print(f"🎉 BATCH COMPLETE! Generated {len(generated_shorts)}/7 Shorts in {total_time/60:.1f} minutes:")
    for res in generated_shorts:
        print(f"   • {res['day']:<18} | {res['creator']:<22} -> {res['path'].name}")
    print("==================================================================\n")

if __name__ == "__main__":
    run_batch()
