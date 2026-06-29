import os
import sys
import cv2
import dlib
import torch
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
import torch.nn as nn
import onnxruntime as ort
from ultralytics import YOLO

print("--- Configuring Environment ---")
DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'
print(f"Device: {DEVICE}")

# ==================================================================================
# 1. PATHS CONFIGURATION (تم التعديل لمسارات الداتا الجديدة)
# ==================================================================================
VIDEO_ROOT_PATH = Path(r"C:\Users\Compumarts\OneDrive\Desktop\projects\DAiSEE\DataSet\Test")
CSV_LABELS_PATH = Path(r"C:\Users\Compumarts\OneDrive\Desktop\projects\DAiSEE\test_labels_binary.csv")
OUTPUT_CSV      = Path(r"C:\Users\Compumarts\OneDrive\Desktop\projects\DAiSEE\engagement_results.csv")

YOLO_PATH       = Path(r"C:\Users\Compumarts\OneDrive\Desktop\projects\final_notebooks\models_of_project\yolov8n-face-lindevs.pt")
HSE_PATH        = Path(r"C:\Users\Compumarts\OneDrive\Desktop\projects\final_notebooks\models_of_project\enet_b2_8.onnx")
HOPENET_PATH    = Path(r"C:\Users\Compumarts\OneDrive\Desktop\projects\final_notebooks\models_of_project\hopenet_robust_alpha1.pkl")
LANDMARK_PATH   = Path(r"C:\Users\Compumarts\OneDrive\Desktop\projects\final_notebooks\models_of_project\shape_predictor_68_face_landmarks.dat")

PIPELINE_WEIGHT = 0.40   
BEHAVIOR_WEIGHT = 0.60   
FINAL_THRESHOLD = 0.60   

EAR_THRESHOLD          = 0.246   
GAZE_H_THRESHOLD       = 0.247   
GAZE_VAR_THRESHOLD     = 0.0005  
MAR_MAX_THRESHOLD      = 0.406   
HEAD_YAW_THRESHOLD     = 4.62    
HEAD_YAW_VAR_THRESHOLD = 9.88    

SKIP_FRAMES = 4
print(f'Blending: {PIPELINE_WEIGHT*100}% Pipeline + {BEHAVIOR_WEIGHT*100}% Behavior Vote')

# ==================================================================================
# 2. MODEL DEFINITIONS
# ==================================================================================
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

class Bottleneck(nn.Module):
    expansion = 4
    def __init__(self, inplanes, planes, stride=1, downsample=None):
        super(Bottleneck, self).__init__()
        self.conv1 = nn.Conv2d(inplanes, planes, kernel_size=1, bias=False)
        self.bn1 = nn.BatchNorm2d(planes)
        self.conv2 = nn.Conv2d(planes, planes, kernel_size=3, stride=stride, padding=1, bias=False)
        self.bn2 = nn.BatchNorm2d(planes)
        self.conv3 = nn.Conv2d(planes, planes * 4, kernel_size=1, bias=False)
        self.bn3 = nn.BatchNorm2d(planes * 4)
        self.relu = nn.ReLU(inplace=True)
        self.downsample = downsample
        self.stride = stride

    def forward(self, x):
        residual = x
        out = self.conv1(x)
        out = self.bn1(out)
        out = self.relu(out)
        out = self.conv2(out)
        out = self.bn2(out)
        out = self.relu(out)
        out = self.conv3(out)
        out = self.bn3(out)
        if self.downsample is not None:
            residual = self.downsample(x)
        out += residual
        out = self.relu(out)
        return out

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
                nn.Conv2d(self.inplanes, planes * block.expansion, kernel_size=1, stride=stride, bias=False),
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
            inp  = np.expand_dims(np.transpose(cv2.resize(rgb, (260, 260)).astype(np.float32)/255.0, (2,0,1)), 0)
            idx  = int(np.argmax(self.session.run(None, {self.session.get_inputs()[0].name: inp})[0][0]))
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

# ==================================================================================
# 3. BLENDED PIPELINE LOGIC
# ==================================================================================
class BlendedPipeline:
    def __init__(self):
        print('Loading models...')
        self.face_detector = FaceDetector(YOLO_PATH)
        self.emotion       = EmotionRecognizer(HSE_PATH)
        self.pose          = HeadPoseEstimator(HOPENET_PATH)
        self.classifier    = EngagementClassifier()
        self.dlib          = DlibLandmarkExtractor(LANDMARK_PATH)
        print('All models loaded successfully.')

    def predict(self, video_path: Path) -> Tuple[int, float, float, float]:
        # تم إزالة كود الـ FFMPEG القسري ليعمل على نظام ويندوز بشكل طبيعي مثل الكود القديم
        cap = cv2.VideoCapture(str(video_path))
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

            dlib_result = self.dlib.extract(face)
            if dlib_result is not None:
                ear, gaze_h, mar = dlib_result
                ears.append(ear)
                gazes.append(gaze_h)
                mars.append(mar)

            emotion    = self.emotion.recognize(face)
            yaw, pitch = self.pose.estimate(face)
            yaws.append(yaw)
            
            pipeline_votes.append(1 if self.classifier.classify(emotion, yaw, pitch) else 0)

        cap.release()

        if not pipeline_votes:
            return 0, 0.0, 0.0, 0.0

        pipeline_score = float(np.mean(pipeline_votes))

        behavior_votes = 0
        if ears:
            behavior_votes += sum([
                np.mean(ears)          < EAR_THRESHOLD,       
                np.mean(np.abs(gazes)) > GAZE_H_THRESHOLD,    
                np.var(gazes)          > GAZE_VAR_THRESHOLD,  
                np.max(mars)           > MAR_MAX_THRESHOLD,   
                np.mean(np.abs(yaws))  > HEAD_YAW_THRESHOLD,  
                np.var(yaws)           > HEAD_YAW_VAR_THRESHOLD 
            ])
        
        behavior_score = 1.0 - (behavior_votes / 6.0)
        final_score = (PIPELINE_WEIGHT * pipeline_score) + (BEHAVIOR_WEIGHT * behavior_score)
        pred = 1 if final_score >= FINAL_THRESHOLD else 0
        
        return pred, final_score, pipeline_score, behavior_score

# ==================================================================================
# FASTAPI WRAPPER (To prevent the web UI from breaking)
# ==================================================================================

class FastApiPipelineWrapper:
    """Wraps the EXACT BlendedPipeline from the Notebook to return UI-compatible JSON."""
    def __init__(self, config: Dict[str, Any]):
        self.pipeline = BlendedPipeline()
    
    def predict(self, video_path: str) -> Dict[str, Any]:
        # We need to capture frame-level emotions and engagement.
        # Since BlendedPipeline.predict only returns 4 values, we will run the same logic here
        # to capture the timelines, or we can just run BlendedPipeline.predict and generate dummy timelines that match the final score.
        # Wait, the user wants the REAL emotion timeline!
        # Let's extract the loop logic to get the timelines.
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            return self._empty_result()

        frame_idx = 0
        ears, gazes, mars, yaws = [], [], [], []
        pipeline_votes = []
        emotion_timeline = []
        engagement_timeline = []
        emotion_counts = {
            "neutral": 0, "happy": 0, "sad": 0, "angry": 0,
            "fearful": 0, "disgusted": 0, "surprised": 0
        }

        while True:
            ret, frame = cap.read()
            if not ret: break
            frame_idx += 1
            if frame_idx % SKIP_FRAMES != 0: continue

            face = self.pipeline.face_detector.detect(frame)
            if face is None: continue

            dlib_result = self.pipeline.dlib.extract(face)
            if dlib_result is not None:
                ear, gaze_h, mar = dlib_result
                ears.append(ear)
                gazes.append(gaze_h)
                mars.append(mar)

            emotion = self.pipeline.emotion.recognize(face)
            yaw, pitch = self.pipeline.pose.estimate(face)
            yaws.append(yaw)
            
            is_engaged = self.pipeline.classifier.classify(emotion, yaw, pitch)
            pipeline_votes.append(1 if is_engaged else 0)
            
            # Record timelines
            timestamp = (frame_idx / cap.get(cv2.CAP_PROP_FPS)) if cap.get(cv2.CAP_PROP_FPS) > 0 else (frame_idx / 30.0)
            
            emotion_mapped = emotion.lower()
            if emotion_mapped == "positive": emotion_mapped = "happy"
            elif emotion_mapped == "negative": emotion_mapped = "sad"
            
            if emotion_mapped in emotion_counts:
                emotion_counts[emotion_mapped] += 1
            else:
                emotion_counts["neutral"] += 1
                
            emotion_timeline.append({
                "timestamp": round(timestamp, 2),
                "emotion": emotion_mapped.capitalize()
            })
            
            engagement_timeline.append({
                "timestamp": round(timestamp, 2),
                "isEngaged": bool(is_engaged)
            })

        cap.release()

        if not pipeline_votes:
            return self._empty_result()

        pipeline_score = float(np.mean(pipeline_votes))

        behavior_votes = 0
        if ears:
            behavior_votes += sum([
                np.mean(ears)          < EAR_THRESHOLD,       
                np.mean(np.abs(gazes)) > GAZE_H_THRESHOLD,    
                np.var(gazes)          > GAZE_VAR_THRESHOLD,  
                np.max(mars)           > MAR_MAX_THRESHOLD,   
                np.mean(np.abs(yaws))  > HEAD_YAW_THRESHOLD,  
                np.var(yaws)           > HEAD_YAW_VAR_THRESHOLD 
            ])
        
        behavior_score = 1.0 - (behavior_votes / 6.0)
        final_score = (PIPELINE_WEIGHT * pipeline_score) + (BEHAVIOR_WEIGHT * behavior_score)
        
        # Calculate dominant emotion
        total_emotions = sum(emotion_counts.values())
        if total_emotions > 0:
            for k in emotion_counts:
                emotion_counts[k] = round((emotion_counts[k] / total_emotions) * 100, 1)
            dominant_emotion = max(emotion_counts, key=emotion_counts.get).capitalize()
        else:
            dominant_emotion = "Neutral"

        return {
            "engagementPercentage": round(final_score * 100, 1),
            "focusedPercentage": round(behavior_score * 100, 1),
            "distractedPercentage": round((1.0 - behavior_score) * 100, 1),
            "dominantEmotion": dominant_emotion,
            "emotionDistribution": emotion_counts,
            "engagementTimeline": engagement_timeline,
            "emotionTimeline": emotion_timeline,
            "disengagementIntervals": []
        }

    def _empty_result(self) -> Dict[str, Any]:
        return {
            "engagementPercentage": 0.0,
            "focusedPercentage": 0.0,
            "distractedPercentage": 100.0,
            "dominantEmotion": "Neutral",
            "emotionDistribution": {
                "neutral": 100.0, "happy": 0.0, "sad": 0.0, "angry": 0.0,
                "fearful": 0.0, "disgusted": 0.0, "surprised": 0.0
            },
            "engagementTimeline": [],
            "emotionTimeline": [],
            "disengagementIntervals": []
        }
