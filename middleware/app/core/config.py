# middleware/app/core/config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME = "AIaaS Middleware"
    VERSION = "1.0.0"

    # JWT Settings
    JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key")
    JWT_ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30

    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://anas:A1n9a8s9@localhost/aiaas")

    # ResNet Server
    RESNET_SERVER_URL = os.getenv("RESNET_SERVER_URL", "http://localhost:8001")

    # EZKL Settings
    EZKL_SETTINGS = {
        "bits": 16,
        "scale": 7,
        "input_shape": [1, 3, 224, 224]
    }

settings = Settings()