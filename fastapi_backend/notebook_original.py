import os
import sys
import cv2
import dlib
import torch
import torch.nn as nn
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import onnxruntime as ort
from pathlib import Path
from typing import Optional, Tuple
from torchvision.models.resnet import Bottleneck
from ultralytics import YOLO
from tqdm import tqdm
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, ConfusionMatrixDisplay, roc_curve, auc
)

print('--- Configuring Environment ---')
os.environ['OPENCV_VIDEOIO_PRIORITY_MSMF'] = '0'
cv2.setNumThreads(cv2.getNumberOfCPUs())
torch.set_grad_enabled(False)
torch.backends.cudnn.benchmark = True
torch.backends.cuda.matmul.allow_tf32 = True
torch.backends.cudnn.allow_tf32 = True
DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'
print(f'Device: {DEVICE}')

# ----------------------------------------------------------------------------------
# PATHS
# ----------------------------------------------------------------------------------
VIDEO_ROOT_PATH = Path(r'D:\Huss\final\DAiSEE\DataSet\Test')
CSV_LABELS_PATH = Path(r'D:\Huss\final\DAiSEE\Labels\TestLabels.csv')

LANDMARK_PATH = Path(r'D:\Project\models_of_project\shape_predictor_68_face_landmarks.dat')
YOLO_PATH     = Path('D:/Project/models_of_project/yolov8n-face-lindevs.pt')
HOPENET_PATH  = Path('D:/Project/models_of_project/hopenet_robust_alpha1.pkl')
HSE_PATH      = Path('D:/Project/models_of_project/enet_b2_8.onnx')

OUTPUT_CSV = Path(r'D:\Project\Notebooks\pipeline_blended_results.csv')

missing = [(str(p), n) for p, n in [
    (VIDEO_ROOT_PATH, 'Video Folder'), (CSV_LABELS_PATH, 'Labels CSV'),
    (LANDMARK_PATH, 'Dlib Landmarks'), (YOLO_PATH, 'YOLO'),
    (HOPENET_PATH, 'Hopenet'), (HSE_PATH, 'HSE Emotion')
] if not p.exists()]

if missing:
    print(f'CRITICAL ERROR: Missing: {[n for _, n in missing]}')
    sys.exit(1)
else:
    print('All paths verified successfully!')

# ----------------------------------------------------------------------------------
# PROBABILITY BLENDING CONFIGURATION
# ----------------------------------------------------------------------------------
# Blend weights (must sum to 1.0)
PIPELINE_WEIGHT = 0.40   # GPU pipeline weight (frame-by-frame Emotion + Pose)
BEHAVIOR_WEIGHT = 0.60   # Behavior score weight (clip-level EAR, Gaze, MAR, Yaw)

FINAL_THRESHOLD = 0.60   # If Final Blended Score >= this -> Engaged

# ----------------------------------------------------------------------------------
# BEHAVIOR THRESHOLDS (Combo #3 from Grid Search)
# ----------------------------------------------------------------------------------
EAR_THRESHOLD          = 0.246   # avg eye openness < this -> drowsy
GAZE_H_THRESHOLD       = 0.247   # avg gaze off-center > this -> looking away
GAZE_VAR_THRESHOLD     = 0.0005  # gaze variance > this -> erratic eyes
MAR_MAX_THRESHOLD      = 0.406   # max mouth opening > this -> yawning
HEAD_YAW_THRESHOLD     = 4.62    # avg absolute yaw > this -> head turned
HEAD_YAW_VAR_THRESHOLD = 9.88    # yaw variance > this -> fidgeting

SKIP_FRAMES = 4

print(f'Blending: {PIPELINE_WEIGHT*100}% Pipeline + {BEHAVIOR_WEIGHT*100}% Behavior Vote')

# ----------------------------------------------------------------------------------
# MODEL DEFINITIONS
# ----------------------------------------------------------------------------------

class DlibLandmarkExtractor:
    LEFT_EYE  = list(range(36, 42))
    RIGHT_EYE = list(range(42, 48))

    def __init__(self, landmark_path: Path):
        self.predictor = dlib.shape_predictor(str(landmark_path))

    def extract(self, face_bgr: np.ndarray) -> Optional[Tuple[float, float, float]]:
        try:
            gray = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2GRAY)
            h, w = gray.shape
            rect = dlib.rectangle(0, 0, w - 1, h - 1)
            shape = self.predictor(gray, rect)
            lm = np.array([[shape.part(i).x, shape.part(i).y] for i in range(68)])

            left_ear  = self._ear(lm[self.LEFT_EYE])
            right_ear = self._ear(lm[self.RIGHT_EYE])
            ear = (left_ear + right_ear) / 2.0

            lc = np.mean(lm[self.LEFT_EYE],  axis=0)
            rc = np.mean(lm[self.RIGHT_EYE], axis=0)
            eyes_cx = (lc[0] + rc[0]) / 2
            gaze_h  = max(-1.0, min(1.0, (eyes_cx - w / 2) / (w / 4)))

            mar = self._mar(lm)
            return float(ear), float(gaze_h), float(mar)
        except:
            return None

    def _ear(self, pts: np.ndarray) -> float:
        v1 = np.linalg.norm(pts[1] - pts[5])
        v2 = np.linalg.norm(pts[2] - pts[4])
        h  = np.linalg.norm(pts[0] - pts[3])
        return (v1 + v2) / (2.0 * h) if h >= 1 else 0.3

    def _mar(self, lm: np.ndarray) -> float:
        v1 = np.linalg.norm(lm[50] - lm[58])
        v2 = np.linalg.norm(lm[51] - lm[57])
        v3 = np.linalg.norm(lm[52] - lm[56])
        h  = np.linalg.norm(lm[48] - lm[54])
        return (v1 + v2 + v3) / (3.0 * h) if h >= 1 else 0.0


class Hopenet(nn.Module):
    def __init__(self, block, layers, num_bins):
        super().__init__()
        self.inplanes = 64
        self.conv1    = nn.Conv2d(3, 64, kernel_size=7, stride=2, padding=3, bias=False)
        self.bn1      = nn.BatchNorm2d(64)
        self.relu     = nn.ReLU(inplace=True)
        self.maxpool  = nn.MaxPool2d(kernel_size=3, stride=2, padding=1)
        self.layer1   = self._make_layer(block, 64,  layers[0])
        self.layer2   = self._make_layer(block, 128, layers[1], stride=2)
        self.layer3   = self._make_layer(block, 256, layers[2], stride=2)
        self.layer4   = self._make_layer(block, 512, layers[3], stride=2)
        self.avgpool  = nn.AdaptiveAvgPool2d((1, 1))
        self.fc_yaw   = nn.Linear(512 * block.expansion, num_bins)
        self.fc_pitch = nn.Linear(512 * block.expansion, num_bins)
        self.fc_roll  = nn.Linear(512 * block.expansion, num_bins)

    def _make_layer(self, block, planes, blocks, stride=1):
        ds = None
        if stride != 1 or self.inplanes != planes * block.expansion:
            ds = nn.Sequential(
                nn.Conv2d(self.inplanes, planes * block.expansion,
                          kernel_size=1, stride=stride, bias=False),
                nn.BatchNorm2d(planes * block.expansion))
        layers = [block(self.inplanes, planes, stride, ds)]
        self.inplanes = planes * block.expansion
        for _ in range(1, blocks):
            layers.append(block(self.inplanes, planes))
        return nn.Sequential(*layers)

    def forward(self, x):
        x = self.maxpool(self.relu(self.bn1(self.conv1(x))))
        x = self.layer4(self.layer3(self.layer2(self.layer1(x))))
        x = self.avgpool(x).view(x.size(0), -1)
        return self.fc_yaw(x), self.fc_pitch(x), self.fc_roll(x)


class HeadPoseEstimator:
    def __init__(self, model_path: Path):
        self.model = Hopenet(Bottleneck, [3, 4, 6, 3], 66)
        ckpt = torch.load(str(model_path), map_location=DEVICE)
        state = ckpt['state_dict'] if 'state_dict' in ckpt else ckpt
        self.model.load_state_dict(state, strict=False)
        self.model.to(DEVICE).eval()
        self.idx = torch.arange(66).float().to(DEVICE)

    def estimate(self, face_bgr) -> Tuple[float, float]:
        rgb = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2RGB)
        t   = torch.from_numpy(cv2.resize(rgb, (224, 224))).permute(2,0,1).float().unsqueeze(0).to(DEVICE) / 255.0
        yaw_l, pitch_l, _ = self.model(t)
        yaw   = torch.sum(torch.softmax(yaw_l,   dim=1) * self.idx) * 3 - 99
        pitch = torch.sum(torch.softmax(pitch_l, dim=1) * self.idx) * 3 - 99
        return float(yaw.item()), float(pitch.item())


class EmotionRecognizer:
    EMOTION_MAP = ['Anger','Contempt','Disgust','Fear','Happiness','Neutral','Sadness','Surprise']
    REDUCED_MAP = {'Anger':'Negative','Disgust':'Negative','Fear':'Negative','Sadness':'Negative',
                   'Happiness':'Positive','Surprise':'Positive','Neutral':'Neutral'}

    def __init__(self, model_path: Path):
        providers = ['CUDAExecutionProvider','CPUExecutionProvider'] if DEVICE == 'cuda' else ['CPUExecutionProvider']
        self.session = ort.InferenceSession(str(model_path), providers=providers)

    def recognize(self, face_bgr) -> str:
        try:
            rgb  = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2RGB)
            inp  = np.expand_dims(np.transpose(
                cv2.resize(rgb, (260, 260)).astype(np.float32)/255.0, (2,0,1)), 0)
            idx  = int(np.argmax(self.session.run(
                None, {self.session.get_inputs()[0].name: inp})[0][0]))
            return self.REDUCED_MAP.get(self.EMOTION_MAP[idx], 'Neutral')
        except:
            return 'Neutral'


class FaceDetector:
    def __init__(self, model_path: Path, conf: float = 0.50):
        self.model = YOLO(str(model_path))
        self.conf  = conf

    def detect(self, frame) -> Optional[np.ndarray]:
        results = self.model(frame, conf=self.conf, verbose=False)
        boxes   = results[0].boxes
        if not len(boxes): return None
        x1, y1, x2, y2 = boxes[0].xyxy.cpu().numpy().astype(int)[0]
        h, w = frame.shape[:2]
        face = frame[max(0,y1):min(h-1,y2), max(0,x1):min(w-1,x2)]
        return face if face.size > 0 else None


class EngagementClassifier:
    def classify(self, emotion: str, yaw: float, pitch: float) -> bool:
        abs_yaw = abs(yaw)
        if emotion == 'Negative':
            return abs_yaw < 12 and -12 < pitch < 12
        if emotion == 'Positive':
            return abs_yaw < 45 and -45 < pitch < 30
        if emotion == 'Neutral':
            if abs_yaw < 40 and -35 < pitch < 28:  return True
            if abs_yaw < 25 and -55 < pitch < -30: return True
        return False

print('All model classes defined.')

# ----------------------------------------------------------------------------------
# BLENDED PIPELINE LOGIC
# ----------------------------------------------------------------------------------

class BlendedPipeline:
    def __init__(self):
        print('Loading models...')
        self.face_detector = FaceDetector(YOLO_PATH)
        self.emotion       = EmotionRecognizer(HSE_PATH)
        self.pose          = HeadPoseEstimator(HOPENET_PATH)
        self.classifier    = EngagementClassifier()
        self.dlib          = DlibLandmarkExtractor(LANDMARK_PATH)
        print('All models loaded.')

    def predict(self, video_path: Path) -> Tuple[int, float, float, float]:
        """Returns (prediction, final_score, pipeline_score, behavior_score)."""
        cap = cv2.VideoCapture(str(video_path), cv2.CAP_FFMPEG)
        if not cap.isOpened():
            return 0, 0.0, 0.0, 0.0

        frame_idx = 0
        ears, gazes, mars, yaws = [], [], [], []
        pipeline_votes = []

        while True:
            ret, frame = cap.read()
            if not ret: break
            frame_idx += 1
            if frame_idx % SKIP_FRAMES != 0: continue

            face = self.face_detector.detect(frame)
            if face is None: continue

            # Extract Dlib features
            dlib_result = self.dlib.extract(face)
            if dlib_result is not None:
                ear, gaze_h, mar = dlib_result
                ears.append(ear)
                gazes.append(gaze_h)
                mars.append(mar)

            # Extract Pipeline features (Emotion + Hopenet Pose)
            emotion    = self.emotion.recognize(face)
            yaw, pitch = self.pose.estimate(face)
            yaws.append(yaw)
            
            pipeline_votes.append(1 if self.classifier.classify(emotion, yaw, pitch) else 0)

        cap.release()

        if not pipeline_votes:
            return 0, 0.0, 0.0, 0.0

        # 1. Pipeline Score (mean of frame-by-frame binary votes)
        pipeline_score = float(np.mean(pipeline_votes))

        # 2. Behavior Score (clip-level voting on 6 fine-tuned features)
        behavior_votes = 0
        if ears:
            behavior_votes += sum([
                np.mean(ears)          < EAR_THRESHOLD,       # Drowsy
                np.mean(np.abs(gazes)) > GAZE_H_THRESHOLD,    # Looking away
                np.var(gazes)          > GAZE_VAR_THRESHOLD,  # Erratic gaze
                np.max(mars)           > MAR_MAX_THRESHOLD,   # Yawning
                np.mean(np.abs(yaws))  > HEAD_YAW_THRESHOLD,  # Head turned (Hopenet yaw)
                np.var(yaws)           > HEAD_YAW_VAR_THRESHOLD # Fidgeting (Hopenet yaw variance)
            ])
        
        # Convert 0-6 triggers into a 0.0-1.0 score (0 triggers = 1.0, 6 triggers = 0.0)
        behavior_score = 1.0 - (behavior_votes / 6.0)

        # 3. Final Blended Score
        final_score = (PIPELINE_WEIGHT * pipeline_score) + (BEHAVIOR_WEIGHT * behavior_score)
        
        pred = 1 if final_score >= FINAL_THRESHOLD else 0
        
        return pred, final_score, pipeline_score, behavior_score

model = BlendedPipeline()

# ----------------------------------------------------------------------------------
# EXECUTION
# ----------------------------------------------------------------------------------

def find_video(base: Path, clip_id: str) -> Optional[Path]:
    for ext in ['.avi', '.mp4']:
        p = base / f'{clip_id}{ext}'
        if p.exists(): return p
        try:
            p = base / clip_id[:6] / clip_id / f'{clip_id}{ext}'
            if p.exists(): return p
        except: pass
    return None

df = pd.read_csv(CSV_LABELS_PATH)
if 'Engagement' in df.columns:
    df['binary_engagement'] = (df['Engagement'] >= 2).astype(int)
elif 'Label' in df.columns:
    df['binary_engagement'] = df['Label'].astype(int)

results = []
print('\n--- Starting Processing ---')
for _, row in tqdm(df.iterrows(), total=len(df), desc='Processing Videos'):
    clip_id    = str(row['ClipID']).replace('.avi', '').replace('.mp4', '')
    video_path = find_video(VIDEO_ROOT_PATH, clip_id)
    gt         = row['binary_engagement']

    if video_path:
        try:
            pred, f_score, p_score, b_score = model.predict(video_path)
            results.append({'ClipID': clip_id, 'y_true': gt, 'y_pred': pred,
                            'final_score': f_score, 'pipeline_score': p_score, 
                            'behavior_score': b_score, 'status': 'success'})
        except Exception as e:
            results.append({'ClipID': clip_id, 'y_true': gt, 'y_pred': 0,
                            'final_score': 0.0, 'pipeline_score': 0.0, 
                            'behavior_score': 0.0, 'status': str(e)})
    else:
        results.append({'ClipID': clip_id, 'y_true': gt, 'y_pred': 0,
                        'final_score': 0.0, 'pipeline_score': 0.0, 
                        'behavior_score': 0.0, 'status': 'not_found'})

results_df = pd.DataFrame(results)
results_df.to_csv(OUTPUT_CSV, index=False)
print(f'\nDone. Results saved to {OUTPUT_CSV}')

# ----------------------------------------------------------------------------------
# METRICS & VISUALIZATIONS
# ----------------------------------------------------------------------------------

valid = results_df[results_df['status'] == 'success']
y_true = valid['y_true'].values
y_pred = valid['y_pred'].values
y_prob = valid['final_score'].values

cm = confusion_matrix(y_true, y_pred)
tn, fp, fn, tp = cm.ravel() if cm.size == 4 else (0, 0, 0, 0)
spec = tn / (tn + fp) if (tn + fp) > 0 else 0.0

print('=' * 55)
print(f'PERFORMANCE METRICS (N={len(valid)})')
print(f'  Accuracy:    {accuracy_score(y_true, y_pred):.4f}')
print(f'  Precision:   {precision_score(y_true, y_pred, zero_division=0):.4f}')
print(f'  Recall:      {recall_score(y_true, y_pred, zero_division=0):.4f}')
print(f'  F1 Score:    {f1_score(y_true, y_pred, zero_division=0):.4f}')
print(f'  Specificity: {spec:.4f}  <-- True Negative Rate')
print(f'  TN={tn}  FP={fp}  FN={fn}  TP={tp}')
print('=' * 55)

print('\nReference (Original 3-model pipeline):')
print('  TN=7   FP=80  FN=25  TP=1662  |  Specificity=0.080  Recall=0.985')

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
ConfusionMatrixDisplay(cm, display_labels=['Not Engaged', 'Engaged']).plot(
    cmap=plt.cm.Blues, ax=ax1)
ax1.set_title('Confusion Matrix — Blended Pipeline')

try:
    fpr, tpr, _ = roc_curve(y_true, y_prob)
    ax2.plot(fpr, tpr, color='darkorange', lw=2, label=f'AUC = {auc(fpr,tpr):.3f}')
    ax2.plot([0,1],[0,1], color='navy', lw=2, linestyle='--')
    ax2.set(xlim=[0,1], ylim=[0,1.05], xlabel='FPR', ylabel='TPR', title='ROC Curve (Final Score)')
    ax2.legend(loc='lower right')
except Exception as e:
    ax2.text(0.5, 0.5, f'ROC: {e}', ha='center')

plt.tight_layout()
plt.show()

