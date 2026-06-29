import json
import os

nb_path = r"C:\Users\Compumarts\Downloads\pipeline_probability_blending (1).ipynb"
out_path = r"C:\Users\Compumarts\OneDrive\Desktop\student_egagment_system\fastapi_backend\notebook_original.py"

with open(nb_path, "r", encoding="utf-8") as f:
    nb = json.load(f)

with open(out_path, "w", encoding="utf-8") as f:
    for cell in nb["cells"]:
        if cell["cell_type"] == "code":
            source = "".join(cell["source"])
            f.write(source + "\n\n")

print("Done extracting notebook.")
