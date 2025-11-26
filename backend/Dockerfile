FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

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

# PREVENT TENSORFLOW FROM INSTALLING
RUN pip uninstall -y tensorflow tensorboard tf-keras tensorflow-estimator || true

# Install app requirements
COPY requirements.txt /app/requirements.txt
RUN pip install --no-deps -r /app/requirements.txt

# Copy the app
COPY . /app

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
