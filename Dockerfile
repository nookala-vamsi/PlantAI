# Use official lightweight Python 3.10 CPU-only image
FROM python:3.10-slim

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /code

# Install system dependencies (needed for rdkit / graph packages)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Pre-install PyTorch CPU-only wheels to bypass long compilation times
RUN pip install --no-cache-dir torch==2.2.1+cpu -f https://download.pytorch.org/whl/torch_stable.html

# Copy requirements file first to utilize Docker layer caching
COPY backend/requirements.txt /code/backend/requirements.txt

# Install remaining dependencies from requirements
RUN pip install --no-cache-dir -r /code/backend/requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu

# Copy the machine learning model assets
COPY ml /code/ml
COPY gate_1 /code/gate_1
COPY gate_2 /code/gate_2

# Copy backend application files
COPY backend /code/backend

# Set the working directory to backend folder so relative ML model paths map seamlessly (../ml/models/...)
WORKDIR /code/backend

# Expose standard Hugging Face Spaces port (7860)
EXPOSE 7860

# Run FastAPI using uvicorn under Hugging Face configurations
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
