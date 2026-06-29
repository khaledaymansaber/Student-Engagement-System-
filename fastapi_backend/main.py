"""
FastAPI Backend for Student Engagement Monitoring System
Exposes the AI pipeline as a REST API for the ASP.NET MVC frontend.
"""

import os
import json
import shutil
import tempfile
import traceback
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

from pipeline import FastApiPipelineWrapper

# ── Load Config ────────────────────────────────────────────────────────────────
CONFIG_PATH = Path(__file__).parent / "config.json"
with open(CONFIG_PATH, "r") as f:
    config = json.load(f)

# ── Initialize FastAPI ─────────────────────────────────────────────────────────
app = FastAPI(
    title="Student Engagement AI API",
    description="Analyzes student engagement from video using a 4-model blended pipeline",
    version="1.0.0"
)

# ── Load Pipeline (once at startup) ───────────────────────────────────────────
pipeline: FastApiPipelineWrapper = None


@app.on_event("startup")
async def startup_event():
    """Load the AI pipeline models when the server starts."""
    global pipeline
    print("[Server] Loading AI pipeline models...")
    pipeline = FastApiPipelineWrapper(config)
    print("[Server] AI pipeline ready! Server is accepting requests.")


# ── Endpoints ──────────────────────────────────────────────────────────────────

@app.get("/health")
async def health_check():
    """Health check endpoint for the ASP.NET backend to verify the server is alive."""
    return {"status": "healthy", "pipeline_loaded": pipeline is not None}


@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    """
    Accepts a video file, runs the engagement analysis pipeline, and returns results.
    The response format matches the FastApiResponseDto expected by the ASP.NET app.
    """
    if pipeline is None:
        raise HTTPException(status_code=503, detail="AI pipeline not loaded yet")

    # Validate file type
    allowed_extensions = {".mp4", ".avi", ".mov"}
    file_ext = Path(file.filename).suffix.lower() if file.filename else ""
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: '{file_ext}'. Allowed: {allowed_extensions}"
        )

    # Save uploaded file to a temp directory
    temp_dir = tempfile.mkdtemp()
    temp_path = os.path.join(temp_dir, file.filename)

    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        print(f"[Server] Analyzing video: {file.filename} ({os.path.getsize(temp_path)} bytes)")

        # Run the pipeline
        result = pipeline.predict(temp_path)

        print(f"[Server] Analysis complete: engagement={result['engagementPercentage']}%")
        return JSONResponse(content=result)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
    finally:
        # Cleanup temp file
        try:
            shutil.rmtree(temp_dir)
        except:
            pass


# ── Run with Uvicorn ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    server_cfg = config.get("server", {})
    uvicorn.run(
        "main:app",
        host=server_cfg.get("host", "0.0.0.0"),
        port=server_cfg.get("port", 8000),
        reload=False
    )
