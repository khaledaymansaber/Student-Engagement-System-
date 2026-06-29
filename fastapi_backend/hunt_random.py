import os
import json
import random
from pipeline import BlendedPipeline

with open("config.json", "r") as f:
    config = json.load(f)
pipeline = BlendedPipeline(config)

TEST_DIR = r"C:\Users\Compumarts\OneDrive\Desktop\projects\DAiSEE\DataSet\Test"

print("Hunting for a True Negative (< 60%) video randomly...")
video_files = []
for root, dirs, files in os.walk(TEST_DIR):
    for file in files:
        if file.endswith(".avi"):
            video_files.append(os.path.join(root, file))

random.seed(42)  # reproducible random
random.shuffle(video_files)

for path in video_files:
    try:
        res = pipeline.predict(path)
        if res['engagementPercentage'] < 60.0:
            print(f"FOUND ONE! {os.path.basename(path)} - Score: {res['engagementPercentage']}%")
            break
    except Exception as e:
        pass
