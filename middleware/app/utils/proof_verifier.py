# middleware/app/utils/proof_verifier.py
import ezkl
from pathlib import Path
import json
import logging
import shutil

logger = logging.getLogger(__name__)

class ProofVerifier:
    def __init__(self):
        # Get the current file's directory and navigate up to middleware
        current_file = Path(__file__)
        self.middleware_dir = current_file.parent.parent.parent
        
        # Define verify_data directory path based on setup.py structure
        self.verify_dir = self.middleware_dir / "verify_data"
        
        logger.info(f"Initialized ProofVerifier with verify dir: {self.verify_dir}")

    async def verify_step(self, step_name: str, condition: bool, error_msg: str) -> None:
        """Verify each step with detailed error messages."""
        if not condition:
            logger.error(f"{step_name} failed: {error_msg}")
            raise AssertionError(f"{step_name} failed: {error_msg}")
        logger.info(f"{step_name} completed successfully")

    def validate_proof_data(self, data: dict) -> dict:
        """Validate the structure of incoming proof data and extract the proof_data"""
        # Check if the data is nested under proof_data
        if "proof_data" in data:
            proof_data = data["proof_data"]
        else:
            proof_data = data  # Use the data directly if not nested
            
        # Validate required fields
        required_fields = ["proof", "settings", "model_type"]
        for field in required_fields:
            if field not in proof_data:
                raise ValueError(f"Missing required field: {field}")
        
        # Validate proof structure
        if not isinstance(proof_data["proof"], dict):
            raise ValueError("Proof data must be a dictionary")
        
        # Validate settings structure
        settings = proof_data["settings"]
        required_settings = ["curve", "strategy", "lookup_bits"]
        for setting in required_settings:
            if setting not in settings:
                raise ValueError(f"Missing required setting: {setting}")
                
        return proof_data  # Return the validated proof_data

    async def prepare_verification_files(self, proof_data: dict, temp_dir: Path) -> tuple:
        """Prepare files needed for verification"""
        try:
            # Create paths for verification files
            proof_path = temp_dir / "proof.json"
            settings_path = temp_dir / "settings.json"
            
            # Save proof and settings
            with open(proof_path, "w") as f:
                json.dump(proof_data["proof"], f, indent=4)
            with open(settings_path, "w") as f:
                json.dump(proof_data["settings"], f, indent=4)
            
            return proof_path, settings_path
        
        except Exception as e:
            logger.error(f"Error preparing verification files: {e}")
            raise

    async def verify_proof(self, data: dict) -> dict:
        """
        Verify EZKL proof using the verification key from setup
        
        Args:
            data: Dictionary containing proof data (either directly or nested under 'proof_data')
            
        Returns:
            Dict containing verification result
        """
        temp_verify_dir = None
        try:
            # Validate incoming proof data and get the correct structure
            proof_data = self.validate_proof_data(data)
            
            model_type = proof_data["model_type"]
            temp_verify_dir = self.verify_dir / f"temp_{model_type}"
            
            # Create temporary directory with clean state
            if temp_verify_dir.exists():
                shutil.rmtree(temp_verify_dir)
            temp_verify_dir.mkdir(exist_ok=True)

            # Get verification key path
            vk_path = self.verify_dir / f"{model_type}_vk.key"
            if not vk_path.exists():
                raise FileNotFoundError(
                    f"Verification key not found at {vk_path}. "
                    "Please ensure setup.py has been run to generate keys."
                )

            # Prepare verification files
            proof_path, settings_path = await self.prepare_verification_files(
                proof_data, temp_verify_dir
            )

            # Log verification attempt
            logger.info(f"Attempting to verify proof for {model_type}")
            logger.debug(f"Using verification key: {vk_path}")
            logger.debug(f"Using proof file: {proof_path}")
            logger.debug(f"Using settings file: {settings_path}")

            # Verify the proof
            logger.info("Verifying proof...")
            is_valid = ezkl.verify(
                str(proof_path),
                str(settings_path),
                str(vk_path)
            )
            
            # Check verification result
            await self.verify_step(
                "Proof verification",
                is_valid,
                "Proof verification failed - proof is invalid"
            )

            return {
                "status": "success",
                "is_valid": is_valid,
                "model_type": model_type,
                "message": "Proof verified successfully" if is_valid else "Proof verification failed"
            }

        except FileNotFoundError as e:
            logger.error(f"File not found error: {e}")
            return {
                "status": "error",
                "error": str(e),
                "is_valid": False,
                "model_type": proof_data.get("model_type", "unknown")
            }
        except ValueError as e:
            logger.error(f"Validation error: {e}")
            return {
                "status": "error",
                "error": str(e),
                "is_valid": False,
                "model_type": proof_data.get("model_type", "unknown")
            }
        except Exception as e:
            logger.error(f"Error verifying proof: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                "status": "error",
                "error": str(e),
                "is_valid": False,
                "model_type": proof_data.get("model_type", "unknown")
            }
        finally:
            # Cleanup temporary verification files
            try:
                if temp_verify_dir and temp_verify_dir.exists():
                    shutil.rmtree(temp_verify_dir)
                    logger.debug(f"Cleaned up temporary directory: {temp_verify_dir}")
            except Exception as e:
                logger.error(f"Cleanup error: {e}")

    def get_verification_key_path(self, model_type: str) -> Path:
        """Get the path to the verification key generated by setup.py"""
        return self.verify_dir / f"{model_type}_vk.key"