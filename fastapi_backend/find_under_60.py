import os
import json
from pipeline import BlendedPipeline

with open("config.json", "r") as f:
    config = json.load(f)
pipeline = BlendedPipeline(config)

TEST_DIR = r"C:\Users\Compumarts\OneDrive\Desktop\projects\DAiSEE\DataSet\Test"

video_path = r"C:\Users\Compumarts\OneDrive\Desktop\projects\DAiSEE\DataSet\Test\510034\5100342022\5100342022.avi"
print(f"Testing video: {video_path}")
try:
    res = pipeline.predict(video_path)
    print(f"Engagement: {res['engagementPercentage']}%")
except Exception as e:
    print(f"Error: {e}")
