import cv2
import dlib
import numpy as np
from pathlib import Path

landmark_path = r"C:\Users\Compumarts\OneDrive\Desktop\projects\final_notebooks\models_of_project\shape_predictor_68_face_landmarks.dat"
print("Loading predictor...")
predictor = dlib.shape_predictor(str(landmark_path))
print("Predictor loaded successfully.")

face_bgr = np.zeros((100, 100, 3), dtype=np.uint8)
gray = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2GRAY)
h, w = gray.shape
rect = dlib.rectangle(0, 0, w - 1, h - 1)

formats = {
    "gray": gray,
    "gray.copy()": gray.copy(),
    "np.ascontiguousarray(gray)": np.ascontiguousarray(gray),
    "face_bgr": face_bgr,
    "face_bgr.copy()": face_bgr.copy(),
    "gray.astype(np.uint8)": gray.astype(np.uint8)
}

for name, img in formats.items():
    try:
        shape = predictor(img, rect)
        print(f"SUCCESS: {name}")
    except Exception as e:
        print(f"FAILED: {name} -> {e}")
