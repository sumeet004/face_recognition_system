FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install required system libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    ffmpeg \
    wget \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install PyTorch CPU
RUN pip install --upgrade pip setuptools wheel
RUN pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

# Copy requirements early to leverage Docker caching
COPY requirements.txt /app/requirements.txt

# Install Python dependencies WITH normal deps  
# (this installs click, starlette, uvicorn deps correctly)
RUN pip install -r /app/requirements.txt

# Remove TensorFlow if DeepFace tries to pull it
RUN pip uninstall -y tensorflow tensorboard tensorflow-estimator tf-keras || true

# Copy application code
COPY . /app

# Expose API port
EXPOSE 8000

# Run API
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]