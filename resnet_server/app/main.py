from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
import shutil
from pathlib import Path
import logging
from PIL import Image
import numpy as np
import uuid
from typing import Dict, Any

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

from .models.model_manager import ModelManager
from .utils.proof_generator import ProofGenerator
from .config import UPLOAD_DIR, MODELS_DIR

# Initialize managers
model_manager = ModelManager()
proof_generator = ProofGenerator()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI application.
    Handles startup and shutdown events.
    """
    # Startup: Load models and create necessary directories
    logger.info("Starting up ResNet server...")
    logger.info(f"Using upload directory: {UPLOAD_DIR}")
    logger.info(f"Using models directory: {MODELS_DIR}")
    
    # Ensure directories exist
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    
    try:
        await model_manager.load_models()
        logger.info("Models loaded successfully")
    except Exception as e:
        logger.error(f"Error loading models: {str(e)}")
        raise
    
    yield  # Server is running
    
    # Cleanup: Add any cleanup code here
    logger.info("Shutting down ResNet server...")

# Initialize FastAPI app with lifespan manager
app = FastAPI(
    title="ResNet Inference Server",
    description="API for ResNet model inference and EZKL proof generation",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint"""
    return {"status": "healthy"}

@app.post("/process")
async def process_image(
    image: UploadFile = File(...),
    model_type: str = "resnet18"
) -> Dict[str, Any]:
    """
    Process uploaded image with specified ResNet model
    
    Args:
        image: Uploaded image file
        model_type: Type of ResNet model to use (resnet18 or resnet34)
    
    Returns:
        Dict containing class_id and probability
    """
    # Validate model type
    if model_type not in ["resnet18", "resnet34"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid model type. Must be either 'resnet18' or 'resnet34'"
        )
    
    # Validate file type
    if not image.content_type.startswith('image/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must be an image"
        )
    
    # Create unique filename
    unique_filename = f"{uuid.uuid4()}_{image.filename}"
    image_path = UPLOAD_DIR / unique_filename
    
    logger.debug(f"Processing image: {image.filename}, model_type: {model_type}")
    logger.debug(f"Saving to: {image_path}")
    
    try:
        # Save uploaded image
        with image_path.open("wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        
        logger.debug(f"File saved successfully at {image_path}")
        
        # Verify file exists and is readable
        if not image_path.exists():
            raise FileNotFoundError(f"File not found after saving: {image_path}")
        
        # Verify it's a valid image
        try:
            with Image.open(image_path) as img:
                logger.debug(f"Image validated: format={img.format}, size={img.size}")
        except Exception as e:
            raise ValueError(f"Invalid image file: {str(e)}")
        
        # Process image
        result = await model_manager.process_image(str(image_path), model_type)
        logger.debug(f"Processing result: {result}")
        return result
        
    except Exception as e:
        logger.exception(f"Error processing image: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing image: {str(e)}"
        )
    finally:
        # Cleanup uploaded image
        if image_path.exists():
            try:
                image_path.unlink()
                logger.debug(f"Cleaned up file: {image_path}")
            except Exception as e:
                logger.error(f"Error cleaning up file {image_path}: {str(e)}")

@app.post("/generate-proof")
async def generate_proof(
    image: UploadFile = File(...),
    model_type: str = "resnet18"
) -> Dict[str, Any]:
    """
    Generate EZKL proof for model inference
    
    Args:
        image: Uploaded image file
        model_type: Type of ResNet model to use (resnet18 or resnet34)
    
    Returns:
        Dict containing proof generation results
    """
    # Validate model type
    if model_type not in ["resnet18", "resnet34"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid model type. Must be either 'resnet18' or 'resnet34'"
        )
    
    # Validate file type
    if not image.content_type.startswith('image/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must be an image"
        )
    
    # Create unique filename
    unique_filename = f"{uuid.uuid4()}_{image.filename}"
    image_path = UPLOAD_DIR / unique_filename
    
    logger.debug(f"Generating proof for image: {image.filename}, model_type: {model_type}")
    
    try:
        # Save uploaded image
        with image_path.open("wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        
        logger.debug(f"File saved successfully at {image_path}")
        
        # Process image to get input tensor
        try:
            with Image.open(image_path) as img:
                image_data = img.convert('RGB')
                input_tensor = model_manager.transform(image_data)
                input_numpy = input_tensor.numpy()
        except Exception as e:
            raise ValueError(f"Error processing image: {str(e)}")
        
        # Generate proof
        try:
            proof_result = await proof_generator.generate_proof(
                model_type,
                input_numpy
            )
            logger.debug(f"Proof generation result: {proof_result}")
            return proof_result
        except Exception as e:
            raise ValueError(f"Error generating proof: {str(e)}")
            
    except Exception as e:
        logger.exception(f"Error in proof generation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating proof: {str(e)}"
        )
    finally:
        # Cleanup uploaded image
        if image_path.exists():
            try:
                image_path.unlink()
                logger.debug(f"Cleaned up file: {image_path}")
            except Exception as e:
                logger.error(f"Error cleaning up file {image_path}: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8001,
        log_level="debug"
    )