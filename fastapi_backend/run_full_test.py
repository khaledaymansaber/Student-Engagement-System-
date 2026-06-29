"""
Full DAiSEE Test Set Evaluation
Processes all 1720 test videos through the BlendedPipeline and compares with ground truth labels.
Outputs: CSV results file + summary statistics.
"""
import os
import sys
import json
import csv
import time
from pathlib import Path

# Add parent dir
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pipeline import BlendedPipeline

# ── Configuration ──────────────────────────────────────────────────────────────
TEST_DIR = r"C:\Users\Compumarts\OneDrive\Desktop\projects\DAiSEE\DataSet\Test"
LABELS_CSV = r"C:\Users\Compumarts\OneDrive\Desktop\projects\engagement_project\data\extracted_data\test_labels_binary.csv"
OUTPUT_CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_results.csv")
SUMMARY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_summary.txt")

# ── Load Ground Truth Labels ──────────────────────────────────────────────────
def load_labels(csv_path):
    """Load DAiSEE labels: filename -> {boredom, engagement, confusion, frustration, binary_label}"""
    labels = {}
    with open(csv_path, 'r') as f:
        reader = csv.reader(f)
        header = next(reader, None)  # skip header if exists
        for row in reader:
            if len(row) >= 6:
                filename = row[0].strip()
                labels[filename] = {
                    'boredom': int(row[1]),
                    'engagement': int(row[2]),
                    'confusion': int(row[3]),
                    'frustration': int(row[4]),
                    'binary_label': int(row[5])  # 1=engaged, 0=not engaged
                }
    return labels

# ── Main Evaluation ───────────────────────────────────────────────────────────
def main():
    print("=" * 70)
    print("  DAiSEE Full Test Set Evaluation")
    print("=" * 70)
    
    # Load pipeline
    with open("config.json", "r") as f:
        config = json.load(f)
    pipeline = BlendedPipeline(config)
    print("[OK] Pipeline loaded successfully.\n")
    
    # Load labels
    labels = load_labels(LABELS_CSV)
    print(f"[OK] Loaded {len(labels)} ground truth labels.\n")
    
    # Find all test videos
    video_files = []
    for root, dirs, files in os.walk(TEST_DIR):
        for file in files:
            if file.endswith(".avi") or file.endswith(".mp4"):
                video_files.append(os.path.join(root, file))
    
    video_files.sort()
    total = len(video_files)
    print(f"[OK] Found {total} test videos.\n")
    print("Starting evaluation...\n")
    
    # Process all videos
    results = []
    correct = 0
    total_processed = 0
    errors = 0
    start_time = time.time()
    
    # Stats tracking
    tp = fp = tn = fn = 0  # True/False Positive/Negative
    engagement_scores = []
    
    with open(OUTPUT_CSV, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([
            'Video', 'GT_Engagement', 'GT_Binary', 
            'Pred_EngagementPct', 'Pred_Binary', 'Correct',
            'DominantEmotion', 'FocusedPct', 'DistractedPct',
            'Pipeline_Detail'
        ])
        
        for i, video_path in enumerate(video_files):
            filename = os.path.basename(video_path)
            
            # Progress
            elapsed = time.time() - start_time
            avg_time = elapsed / (i + 1) if i > 0 else 0
            remaining = avg_time * (total - i - 1)
            
            print(f"[{i+1}/{total}] Processing: {filename}  "
                  f"(Elapsed: {elapsed:.0f}s, ETA: {remaining:.0f}s)", end="")
            
            try:
                result = pipeline.predict(video_path)
                eng_pct = result['engagementPercentage']
                pred_binary = 1 if eng_pct >= 60.0 else 0
                
                # Get ground truth
                gt = labels.get(filename, None)
                if gt is None:
                    print(f"  -> WARNING: No ground truth for {filename}")
                    continue
                
                gt_engagement = gt['engagement']
                gt_binary = gt['binary_label']
                is_correct = (pred_binary == gt_binary)
                
                if is_correct:
                    correct += 1
                
                # Confusion matrix
                if pred_binary == 1 and gt_binary == 1:
                    tp += 1
                elif pred_binary == 1 and gt_binary == 0:
                    fp += 1
                elif pred_binary == 0 and gt_binary == 1:
                    fn += 1
                else:
                    tn += 1
                
                engagement_scores.append(eng_pct)
                total_processed += 1
                
                writer.writerow([
                    filename, gt_engagement, gt_binary,
                    eng_pct, pred_binary, 1 if is_correct else 0,
                    result['dominantEmotion'],
                    result['focusedPercentage'],
                    result['distractedPercentage'],
                    f"focused={result['focusedPercentage']}% distracted={result['distractedPercentage']}%"
                ])
                
                status = "✓" if is_correct else "✗"
                print(f"  -> Eng={eng_pct}% Pred={pred_binary} GT={gt_binary} [{status}]")
                
            except Exception as e:
                errors += 1
                print(f"  -> ERROR: {str(e)[:80]}")
                writer.writerow([filename, '', '', '', '', '', '', '', '', f'ERROR: {e}'])
    
    # ── Summary Statistics ─────────────────────────────────────────────────────
    total_time = time.time() - start_time
    accuracy = (correct / total_processed * 100) if total_processed > 0 else 0
    precision = (tp / (tp + fp) * 100) if (tp + fp) > 0 else 0
    recall = (tp / (tp + fn) * 100) if (tp + fn) > 0 else 0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0
    
    avg_engagement = sum(engagement_scores) / len(engagement_scores) if engagement_scores else 0
    min_engagement = min(engagement_scores) if engagement_scores else 0
    max_engagement = max(engagement_scores) if engagement_scores else 0
    
    summary = f"""
{'='*70}
  DAiSEE Test Set Evaluation - FINAL RESULTS
{'='*70}

Total Videos Found:      {total}
Successfully Processed:  {total_processed}
Errors:                  {errors}
Total Time:              {total_time:.1f}s ({total_time/60:.1f} min)
Avg Time per Video:      {total_time/total_processed:.2f}s

{'─'*70}
  ACCURACY METRICS
{'─'*70}

Overall Accuracy:        {accuracy:.1f}% ({correct}/{total_processed})

Confusion Matrix:
                    Predicted Engaged    Predicted Not-Engaged
  GT Engaged            {tp:>6} (TP)           {fn:>6} (FN)
  GT Not-Engaged        {fp:>6} (FP)           {tn:>6} (TN)

Precision:               {precision:.1f}%
Recall (Sensitivity):    {recall:.1f}%
F1 Score:                {f1:.1f}%

{'─'*70}
  ENGAGEMENT SCORE DISTRIBUTION
{'─'*70}

Average Engagement:      {avg_engagement:.1f}%
Min Engagement:          {min_engagement:.1f}%
Max Engagement:          {max_engagement:.1f}%

{'='*70}
Results saved to: {OUTPUT_CSV}
{'='*70}
"""
    
    print(summary)
    
    with open(SUMMARY_FILE, 'w') as f:
        f.write(summary)
    
    print(f"\n[OK] Detailed results saved to: {OUTPUT_CSV}")
    print(f"[OK] Summary saved to: {SUMMARY_FILE}")


if __name__ == "__main__":
    main()
