import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Get paths from environment variables with fallbacks
MODELS_DIR = Path(os.getenv('MODEL_DIR', 'app/models'))
UPLOAD_DIR = Path(os.getenv('UPLOAD_DIR', 'app/uploads'))
PORT = int(os.getenv('PORT', 8001))

# Ensure paths are absolute
if not MODELS_DIR.is_absolute():
    MODELS_DIR = BASE_DIR / MODELS_DIR
if not UPLOAD_DIR.is_absolute():
    UPLOAD_DIR = BASE_DIR / UPLOAD_DIR

# Model paths
ONNX_DIR = MODELS_DIR / "onnx"

# Create directories if they don't exist
MODELS_DIR.mkdir(parents=True, exist_ok=True)
ONNX_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Model URLs
MODEL_URLS = {
    "resnet18": "https://download.pytorch.org/models/resnet18-5c106cde.pth",
    "resnet34": "https://download.pytorch.org/models/resnet34-333f7ec4.pth"
}

# EZKL settings
EZKL_SETTINGS = {
    "input_shape": [1, 3, 224, 224],
    "scale": 7,
    "bits": 16,
}