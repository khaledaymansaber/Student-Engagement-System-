import os
import csv
import json
from pipeline import BlendedPipeline

with open("config.json", "r") as f:
    config = json.load(f)
pipeline = BlendedPipeline(config)

LABELS_CSV = r"C:\Users\Compumarts\OneDrive\Desktop\projects\engagement_project\data\extracted_data\test_labels_binary.csv"
TEST_DIR = r"C:\Users\Compumarts\OneDrive\Desktop\projects\DAiSEE\DataSet\Test"

print("Finding the 88 Negative cases in Ground Truth...")
neg_videos = []
with open(LABELS_CSV, "r") as f:
    reader = csv.reader(f)
    next(reader, None)  # skip header
    for row in reader:
        if len(row) >= 6 and int(row[5]) == 0:
            vid = row[0].strip()
            # Find its folder
            for root, _, files in os.walk(TEST_DIR):
                if vid in files:
                    neg_videos.append(os.path.join(root, vid))
                    break

print(f"Found {len(neg_videos)} negative videos on disk. Evaluating them to find one of the 30 True Negatives...")

for vid_path in neg_videos:
    try:
        res = pipeline.predict(vid_path)
        score = res['engagementPercentage']
        if score < 60.0:
            print("="*50)
            print(f"🎉 FOUND A TRUE NEGATIVE: {os.path.basename(vid_path)}")
            print(f"Score: {score}%")
            print("="*50)
            import sys
            sys.exit(0)
    except:
        pass

print("None found?!")
