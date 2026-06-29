import os
import cv2
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Optional
from tqdm import tqdm
from pipeline import BlendedPipeline, VIDEO_ROOT_PATH, FINAL_THRESHOLD

def find_video_file(base_folder: Path, clip_id_str: str) -> Optional[Path]:
    filename = f"{clip_id_str}.avi"
    filename_mp4 = f"{clip_id_str}.mp4"
    direct_path = base_folder / filename
    if direct_path.exists(): return direct_path
    direct_path_mp4 = base_folder / filename_mp4
    if direct_path_mp4.exists(): return direct_path_mp4
    try:
        prefix = clip_id_str[:6] 
        nested_path = base_folder / prefix / clip_id_str / filename
        if nested_path.exists(): return nested_path
        nested_path_mp4 = base_folder / prefix / clip_id_str / filename_mp4
        if nested_path_mp4.exists(): return nested_path_mp4
    except:
        pass
    return None

ids = [
    "5000441024", "5000441058", "5000441067", "5000671041", "5000671042",
    "5000671048", "5000671049", "5000671058", "5000671061", "5000671069",
    "5000671070", "5000951019", "5000951023", "5000951024", "5000951027",
    "5000952034", "5000952062", "5000952083", "5100091049", "5100341043",
    "5100341074", "5100342022", "5100342023", "5100342024", "5100342028",
    "5100342036", "5100342048", "5100351001", "5100351002", "5100351013",
    "5100351022", "5100351042", "5100352022", "5100352043", "5100352054",
    "5100401023", "5100401034", "5100401043", "5100401065", "5100402001",
    "5100402062", "5100402063", "5100452016", "5100461007", "5100462003",
    "5100472001", "5100472058", "8264120116", "8264120120", "8264120123",
    "8264120127", "826412013", "8264120150", "8264120156", "8264120169",
    "8264120211", "8264120231", "8264120239", "8264120240", "8264120243",
    "8264120249", "8264120254", "8264120256", "8264120261", "8264120262",
    "8264120263", "8264120265", "8264120266", "8264120269", "8264120279",
    "8264120282", "8264120284", "88265401750", "907001480", "907001950",
    "9289010114", "928901014", "9289010145", "9289010152", "9289010276",
    "9403280271", "9877360120", "9877360133", "9877360157", "9877360169",
    "9877360172", "9877360256", "9877360270"
]

print("Loading models...")
model = BlendedPipeline()

def analyze_video(clip_id):
    video_path = find_video_file(VIDEO_ROOT_PATH, clip_id)
    if not video_path:
        return f"Video {clip_id} not found."
    
    try:
        pred, f_score, p_score, b_score = model.predict(video_path)
        
        status = "Engaged (FP)" if pred == 1 else "Not Engaged (TN)"
        
        report = (
            f"--- Video: {clip_id} ---\n"
            f"Result: {status} (Score: {f_score*100:.1f}%)\n"
            f"Reasoning:\n"
            f"  - Final Score ({f_score*100:.1f}%) = [Pipeline Weight 40% * {p_score*100:.1f}%] + [Behavior Weight 60% * {b_score*100:.1f}%]\n"
            f"  - Since Final Score ({f_score*100:.1f}%) is >= {FINAL_THRESHOLD*100}%, the video is marked as '{status}'.\n"
        )
        return report
    except Exception as e:
        return f"Video {clip_id} error: {e}"

results = []
for cid in tqdm(ids, desc="Analyzing 88 zero-engagement videos"):
    res = analyze_video(cid)
    results.append(res)

with open("88_videos_detailed_report.txt", "w", encoding="utf-8") as f:
    f.write("\n\n".join(results))

print("Detailed report saved to 88_videos_detailed_report.txt")
