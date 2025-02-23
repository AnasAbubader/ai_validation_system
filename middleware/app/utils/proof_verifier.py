# middleware/app/utils/proof_verifier.py
import ezkl
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)

class ProofVerifier:
    def __init__(self):
        # Define base paths
        self.base_dir = Path("ai-validation-system")
        self.verify_dir = self.base_dir / "middleware" / "verify_data"
        
        # Create necessary directories
        self.verify_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Initialized ProofVerifier with verify dir: {self.verify_dir}")

    async def verify_step(self, step_name: str, condition: bool, error_msg: str) -> None:
        """Verify each step with detailed error messages."""
        if not condition:
            logger.error(f"{step_name} failed: {error_msg}")
            raise AssertionError(f"{step_name} failed: {error_msg}")
        logger.info(f"{step_name} completed successfully")

    async def verify_proof(self, proof_data: dict) -> dict:
        """
        Verify EZKL proof using optimized approach
        
        Args:
            proof_data: Dictionary containing proof data
            
        Returns:
            Dict containing verification result
        """
        try:
            model_type = proof_data.get("model_type", "unknown")
            temp_verify_dir = self.verify_dir / f"temp_{model_type}"
            temp_verify_dir.mkdir(exist_ok=True)

            # Define verification paths
            proof_path = temp_verify_dir / "received_proof.json"
            settings_path = temp_verify_dir / "verify_settings.json"
            vk_path = self.verify_dir / f"{model_type}_vk.key"

            # Verify verification key exists
            if not vk_path.exists():
                raise FileNotFoundError(f"Verification key not found at {vk_path}")

            # Save received proof and settings
            with open(proof_path, "w") as f:
                json.dump(proof_data["proof"], f)
            with open(settings_path, "w") as f:
                json.dump(proof_data["settings"], f)

            # Verify the received proof
            logger.info("Verifying proof...")
            is_valid = ezkl.verify(
                str(proof_path),
                str(settings_path),
                str(vk_path)
            )
            await self.verify_step("Proof verification", is_valid, "Failed to verify proof")

            return {
                "status": "success",
                "is_valid": is_valid,
                "model_type": model_type
            }

        except Exception as e:
            logger.error(f"Error verifying proof: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                "status": "error",
                "error": str(e),
                "is_valid": False,
                "model_type": model_type
            }
        finally:
            # Cleanup temporary verification files
            try:
                for file in temp_verify_dir.glob('*'):
                    file.unlink()
                temp_verify_dir.rmdir()
            except Exception as e:
                logger.error(f"Cleanup error: {e}")

    def get_verification_key_path(self, model_type: str) -> Path:
        """Get the path to the verification key for a specific model"""
        return self.verify_dir / f"{model_type}_vk.key"