import os
import json
from pathlib import Path
from pipeline import BlendedPipeline

with open("config.json", "r") as f:
    config = json.load(f)

pipeline = BlendedPipeline(config)
video_path = r"C:\Users\Compumarts\OneDrive\Desktop\projects\DAiSEE\DataSet\Test\928901\9289010276\9289010276.avi"
print(f"Testing video: {video_path}")
try:
    res = pipeline.predict(video_path)
    print(json.dumps(res, indent=2))
except Exception as e:
    print(f"Error: {e}")
