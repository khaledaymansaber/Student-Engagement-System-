import os

with open("notebook_original.py", "r", encoding="utf-8") as f:
    code = f.read()

# Replace paths
replacements = {
    r"Path(r'D:\Huss\final\DAiSEE\DataSet\Test')": r"Path(r'C:\Users\Compumarts\OneDrive\Desktop\projects\DAiSEE\DataSet\Test')",
    r"Path(r'D:\Huss\final\DAiSEE\Labels\TestLabels.csv')": r"Path(r'C:\Users\Compumarts\OneDrive\Desktop\projects\engagement_project\data\extracted_data\test_labels_binary.csv')",
    r"Path(r'D:\Project\models_of_project\shape_predictor_68_face_landmarks.dat')": r"Path(r'C:\Users\Compumarts\OneDrive\Desktop\projects\engagement_project\models\landmarks\shape_predictor_68_face_landmarks.dat')",
    r"Path('D:/Project/models_of_project/yolov8n-face-lindevs.pt')": r"Path(r'C:\Users\Compumarts\OneDrive\Desktop\projects\engagement_project\models\yolo\yolov8n-face-lindevs.pt')",
    r"Path('D:/Project/models_of_project/hopenet_robust_alpha1.pkl')": r"Path(r'C:\Users\Compumarts\OneDrive\Desktop\projects\engagement_project\models\hopenet\hopenet_robust_alpha1.pkl')",
    r"Path('D:/Project/models_of_project/enet_b2_8.onnx')": r"Path(r'C:\Users\Compumarts\OneDrive\Desktop\projects\engagement_project\models\emotion\enet_b2_8.onnx')",
    r"Path(r'D:\Project\Notebooks\pipeline_blended_results.csv')": r"Path(r'C:\Users\Compumarts\OneDrive\Desktop\student_egagment_system\fastapi_backend\pipeline_blended_results.csv')"
}

for old, new in replacements.items():
    code = code.replace(old, new)

with open("run_notebook_eval.py", "w", encoding="utf-8") as f:
    f.write(code)

print("Created run_notebook_eval.py with correct paths.")
