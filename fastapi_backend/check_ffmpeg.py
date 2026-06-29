import cv2
import pandas as pd
from pathlib import Path
from tqdm import tqdm

VIDEO_ROOT_PATH = Path(r"C:\Users\Compumarts\OneDrive\Desktop\projects\DAiSEE\DataSet\Test")
CSV_LABELS_PATH = Path(r"C:\Users\Compumarts\OneDrive\Desktop\projects\DAiSEE\test_labels_binary.csv")

def find_video_file(base_folder: Path, clip_id_str: str):
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

df = pd.read_csv(CSV_LABELS_PATH)
failed_count = 0
failed_tn = 0
failed_fn = 0

print("Checking all 1784 videos with cv2.CAP_FFMPEG...")

for idx, row in tqdm(df.iterrows(), total=len(df)):
    clip_id = str(row['ClipID']).replace('.avi', '').replace('.mp4', '')
    gt = 0
    if 'Engagement' in df.columns:
        gt = int(row['Engagement'] >= 2)
    elif 'Label' in df.columns:
        gt = int(row['Label'])

    video_path = find_video_file(VIDEO_ROOT_PATH, clip_id)
    if video_path:
        # Here we test their exact code: cv2.CAP_FFMPEG
        cap = cv2.VideoCapture(str(video_path), cv2.CAP_FFMPEG)
        if not cap.isOpened():
            failed_count += 1
            if gt == 0:
                failed_tn += 1
            else:
                failed_fn += 1
        cap.release()

print(f"\n--- PROOF RESULTS ---")
print(f"Total videos that FAILED to open with CAP_FFMPEG: {failed_count}")
print(f"Failed videos that were actually NOT Engaged (TN): {failed_tn}")
print(f"Failed videos that were actually Engaged (FN): {failed_fn}")
