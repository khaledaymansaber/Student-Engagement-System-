FROM python:3.9-slim

# Install system dependencies needed for OpenCV, Dlib, and Video processing (needs root)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    build-essential \
    cmake \
    && rm -rf /var/lib/apt/lists/*

# Hugging Face Spaces requires a non-root user for security
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

WORKDIR /app

# Copy requirements and install
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files (including models)
COPY --chown=user . /app

# Hugging Face Spaces expects the app to run on port 7860
EXPOSE 7860

# Start the FastAPI server (our entrypoint is pipeline.py)
CMD ["uvicorn", "pipeline:app", "--host", "0.0.0.0", "--port", "7860"]
