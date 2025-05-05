# middleware/app/api/resnet.py
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
import requests
import shutil
import os
from pathlib import Path
import logging
import uuid
from ..core.security import get_current_user
from database.base import get_db
from database.crud import (
    create_request,
    get_user_requests,
    get_random_unverified_request,
    update_proof_status,
    update_proof_stats,
    count_user_requests,
    get_failed_verifications
)
from ..core.config import settings
from sqlalchemy.orm import Session
from ..utils.proof_verifier import ProofVerifier

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

router = APIRouter()

# Create upload directory for temporary files
TEMP_UPLOAD_DIR = Path("temp_uploads")
TEMP_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Initialize proof verifier
proof_verifier = ProofVerifier()

def count_temp_files(user_id: int) -> int:
    """Count the number of files in user's temporary directory"""
    user_dir = TEMP_UPLOAD_DIR / str(user_id)
    if not user_dir.exists():
        return 0
    return len(list(user_dir.glob("*")))

def compare_results(result1: dict, result2: dict, tolerance: float = 0.001) -> bool:
    """
    Compare two ResNet results to check if they're the same within tolerance
    """
    try:
        if set(result1.keys()) != set(result2.keys()):
            return False
            
        for key in result1:
            if abs(result1[key] - result2[key]) > tolerance:
                return False
        return True
    except Exception as e:
        logger.error(f"Error comparing results: {str(e)}")
        return False

def cleanup_temp_images(user_id: int):
    """Clean up only temporary images for a specific user"""
    user_dir = TEMP_UPLOAD_DIR / str(user_id)
    if user_dir.exists():
        for file in user_dir.glob("*"):
            try:
                file.unlink()
                logger.debug(f"Cleaned up temporary image: {file}")
            except Exception as e:
                logger.error(f"Error cleaning up file {file}: {str(e)}")
        try:
            user_dir.rmdir()
            logger.debug(f"Removed empty temporary directory: {user_dir}")
        except Exception as e:
            logger.error(f"Error removing directory {user_dir}: {str(e)}")

async def process_single_image(image_path: Path, filename: str, model_type: str) -> dict:
    """Process a single image and return the result"""
    try:
        with open(image_path, "rb") as f:
            files = {"image": (filename, f, "image/jpeg")}
            logger.debug(f"Sending request to ResNet server with model_type: {model_type}")
            response = requests.post(
                f"{settings.RESNET_SERVER_URL}/process",
                files=files,
                data={"model_type": model_type}
            )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"ResNet server error: {response.text}"
            )
        
        return response.json()
    except Exception as e:
        logger.error(f"Error processing image {filename}: {str(e)}")
        raise

@router.post("/process")
async def process_image(
    image: UploadFile = File(...),
    model_type: str = Form("resnet18"),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Process uploaded image with specified ResNet model and manage proof generation"""
    if model_type not in ["resnet18", "resnet34"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid model type"
        )

    # Create user-specific directory
    user_dir = TEMP_UPLOAD_DIR / str(current_user.id)
    user_dir.mkdir(parents=True, exist_ok=True)

    # Create unique filename
    unique_filename = f"{uuid.uuid4()}_{image.filename}"
    temp_path = user_dir / unique_filename

    logger.debug(f"Processing image: {image.filename}, model_type: {model_type}")
    
    try:
        # Save uploaded image temporarily
        with open(temp_path, "wb") as buffer:
            await image.seek(0)
            content = await image.read()
            buffer.write(content)
        
        logger.debug(f"File saved temporarily at {temp_path}")
        
        # Process initial image
        result = await process_single_image(temp_path, image.filename, model_type)
        logger.debug(f"Received result from ResNet server: {result}")
        
        # Record request in database
        request = create_request(
            db,
            user_id=current_user.id,
            model_type=model_type,
            image_path=str(temp_path),
            result=result
        )
        
        # Check if we should generate proof based on number of files
        file_count = count_temp_files(current_user.id)
        logger.debug(f"Current file count: {file_count}, threshold: {current_user.proof_threshold}")
        
        if file_count >= current_user.proof_threshold:
            # Choose random request for verification
            random_request = get_random_unverified_request(db, current_user.id)
            if random_request:
                logger.debug(f"Verifying request: {random_request.id}")
                
                random_image_path = Path(random_request.image_path)
                if random_image_path.exists():
                    try:
                        # First verification step
                        new_result = await process_single_image(
                            random_image_path,
                            os.path.basename(random_image_path),
                            random_request.model_type
                        )
                        logger.debug(f"Verification result: {new_result}")
                        
                        # Compare original and new results
                        results_match = compare_results(random_request.result, new_result)
                        logger.debug(f"Results match: {results_match}")
                        
                        if results_match:
                            # Generate proof
                            logger.debug("Results match, generating proof")
                            with open(random_image_path, "rb") as f:
                                files = {"image": (os.path.basename(random_image_path), f, "image/jpeg")}
                                proof_response = requests.post(
                                    f"{settings.RESNET_SERVER_URL}/generate-proof",
                                    files=files,
                                    data={"model_type": random_request.model_type}
                                )
                            
                            if proof_response.status_code == 200:
                                proof_result = proof_response.json()
                                logger.debug(f"Received proof from ResNet server: {proof_result}")
                                
                                verification_result = await proof_verifier.verify_proof(proof_result)
                                logger.debug(f"Proof verification result: {verification_result}")
                                
                                update_proof_status(
                                    db,
                                    random_request.id,
                                    proof_generated=True,
                                    proof_verified=verification_result["is_valid"]
                                )
                                
                                update_proof_stats(
                                    db,
                                    current_user.id,
                                    verification_result["is_valid"]
                                )
                                
                                # Clean up all temporary files after successful proof generation
                                cleanup_temp_images(current_user.id)
                            else:
                                logger.error(f"Error generating proof: {proof_response.text}")
                                update_proof_status(
                                    db,
                                    random_request.id,
                                    proof_generated=True,
                                    proof_verified=False,
                                    verification_failed=True
                                )
                        else:
                            logger.warning("Results don't match, marking proof as failed")
                            update_proof_status(
                                db,
                                random_request.id,
                                proof_generated=True,
                                proof_verified=False,
                                verification_failed=True
                            )
                            update_proof_stats(db, current_user.id, False)
                    except Exception as e:
                        logger.error(f"Error during verification/proof generation: {str(e)}")
                        raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Error during verification/proof generation: {str(e)}"
                        )
                else:
                    logger.error(f"Random request image not found: {random_image_path}")
        
        return result
    
    except Exception as e:
        logger.exception(f"Error processing image: {str(e)}")
        if temp_path.exists():
            temp_path.unlink()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing image: {str(e)}"
        )

@router.get("/stats")
async def get_stats(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's proof generation statistics"""
    failed_verifications = get_failed_verifications(db, current_user.id)
    failed_proofs = current_user.total_proofs - current_user.successful_proofs
    
    return {
        "total_proofs": current_user.total_proofs,
        "successful_proofs": current_user.successful_proofs,
        "failed_proofs": failed_proofs,
        "success_percentage": (current_user.successful_proofs / current_user.total_proofs * 100) if current_user.total_proofs > 0 else 0,
        "failed_verifications": len(failed_verifications),
        "threshold": current_user.proof_threshold
    }

@router.post("/settings")
async def update_settings(
    proof_threshold: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user's proof threshold setting"""
    if proof_threshold < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Proof threshold must be positive"
        )
    
    current_user.proof_threshold = proof_threshold
    db.commit()
    return {"message": "Settings updated successfully"}