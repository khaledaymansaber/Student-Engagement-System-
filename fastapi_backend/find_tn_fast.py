import os
import csv
import json
from pipeline import BlendedPipeline

with open("config.json", "r") as f:
    config = json.load(f)
pipeline = BlendedPipeline(config)

LABELS_CSV = r"C:\Users\Compumarts\OneDrive\Desktop\projects\engagement_project\data\extracted_data\test_labels_binary.csv"
TEST_DIR = r"C:\Users\Compumarts\OneDrive\Desktop\projects\DAiSEE\DataSet\Test"

print("Loading negative labels...")
neg_vids = set()
with open(LABELS_CSV, "r") as f:
    reader = csv.reader(f)
    next(reader, None)
    for row in reader:
        if len(row) >= 6 and int(row[5]) == 0:
            neg_vids.add(row[0].strip())

print(f"Loaded {len(neg_vids)} negative labels. Scanning filesystem O(N)...", flush=True)

neg_paths = []
for root, dirs, files in os.walk(TEST_DIR):
    for f in files:
        if f in neg_vids:
            neg_paths.append(os.path.join(root, f))

print(f"Found {len(neg_paths)} paths on disk. Evaluating now...", flush=True)

for path in neg_paths:
    try:
        res = pipeline.predict(path)
        score = res['engagementPercentage']
        if score < 60.0:
            print("="*50, flush=True)
            print(f"FOUND: {os.path.basename(path)} - Score: {score}%", flush=True)
            print("="*50, flush=True)
            import sys
            sys.exit(0)
    except:
        pass
