import pandas as pd

# Path to the dataset
csv_path = r'C:\Users\Compumarts\OneDrive\Desktop\projects\engagement_project\data\extracted_data\test_labels_binary.csv'

# Read dataset
df = pd.read_csv(csv_path)

# Filter cases where binary_engagement is 0
zero_eng_ids = df[df['binary_engagement'] == 0]['ClipID'].tolist()

# Print the count
print(f"Total Zero Engagement Cases: {len(zero_eng_ids)}\n")

# Print all IDs
print("List of IDs:")
for clip_id in zero_eng_ids:
    print(clip_id)
