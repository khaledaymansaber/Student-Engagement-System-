<h1 align="center">Student Engagement System (SEM) 🎓</h1>

<p align="center">
  <strong>An AI-powered Learning Management System (LMS) to monitor, analyze, and enhance student engagement using Deep Learning.</strong>
</p>

---

## 📖 Overview
The **Student Engagement System** helps educators track the attention and emotional state of their students during video sessions. By uploading a recorded video of a student, the system's AI engine analyzes facial expressions, head posture, and eye movements to generate an **Engagement Timeline** and an overall **Engagement Score**.

## 🛠️ Technology Stack
- **Frontend & UI:** ASP.NET Core MVC 8, Tailwind CSS, Alpine.js, Chart.js
- **Backend (Web App):** C#, Entity Framework Core, SQL Server
- **AI Processing (API):** Python, FastAPI, PyTorch, ONNX
- **Machine Learning Models:**
  - **YOLOv8** (Face Detection)
  - **HopeNet** (Head Pose Estimation - Yaw, Pitch, Roll)
  - **HSE Emotion** (Facial Expression Recognition)
  - **Dlib** (Facial Landmarks, Eye Aspect Ratio, Mouth Aspect Ratio)

## ✨ Key Features
- **Dashboard:** At-a-glance overview of total videos, recent uploads, and overall system activity.
- **Student Profiles:** Manage students and track their individual performance over time.
- **AI Video Analysis:** Deep learning pipeline that classifies frames as *Focused* or *Distracted*.
- **Emotion Timeline:** Visual graphs displaying the dominant emotion throughout the video.
- **Real-time Notifications:** In-app alerts when video analysis is complete or if a student shows critically low engagement.

---

## 🚀 Getting Started (Local Setup)

To run this project locally, you need to run both the **ASP.NET Server** and the **FastAPI AI Server**.

### 1. Start the FastAPI AI Server
Make sure you have Python 3.9+ installed.
```bash
cd fastapi_backend
pip install -r requirements.txt
uvicorn pipeline:app --host 0.0.0.0 --port 8000
```
*Note: Ensure you have the required pre-trained weights (.onnx, .pt) in the `fastapi_backend` directory before running.*

### 2. Start the ASP.NET Web App
Make sure you have the .NET 8 SDK installed.
```bash
# Apply database migrations
dotnet ef database update

# Run the project
dotnet run
```
The application will be available at `http://localhost:5168`.

---

## 🗄️ Database Schema
The SQL Server database uses Entity Framework Core (Code-First) and consists of the following entities:
- `Teacher` (AspNetUsers)
- `Student`
- `Video`
- `AnalysisResult`
- `Notification`

## 🔮 Future Enhancements
- Live real-time stream analysis (WebRTC).
- Support for multiple faces in a single classroom video.

---

<p align="center">Made with ❤️ for modern education.</p>
