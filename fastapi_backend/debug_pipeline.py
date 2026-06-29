from pathlib import Path
import sys
sys.path.append(r"C:\Users\Compumarts\OneDrive\Desktop\student_egagment_system\fastapi_backend")
from pipeline import BlendedPipeline

video_path = Path(r"C:\Users\Compumarts\OneDrive\Desktop\projects\DAiSEE\DataSet\Test\826412\8264120150\8264120150.avi")
if not video_path.exists():
    video_path = Path(r"C:\Users\Compumarts\OneDrive\Desktop\projects\DAiSEE\DataSet\Test\8264120150.avi")
    if not video_path.exists():
        video_path = Path(r"C:\Users\Compumarts\OneDrive\Desktop\projects\DAiSEE\DataSet\Test\8264120150.mp4")

model = BlendedPipeline()
pred, final_score, p_score, b_score = model.predict(video_path)
print(f"Prediction: {pred}, Final: {final_score}, Pipeline: {p_score}, Behavior: {b_score}")
