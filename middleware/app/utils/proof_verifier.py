# middleware/app/utils/proof_verifier.py
import ezkl
from pathlib import Path
import json
import logging
import shutil
import time
import os

logger = logging.getLogger(__name__)

class ProofVerifier:
    def __init__(self):
        # Check multiple possible paths for verification keys
        possible_paths = [
            Path("/app/verify_data"),                  # Direct path
            Path("/app/middleware/verify_data"),       # Nested path
            Path("/app").parent / "verify_data",       # Parent directory
            Path("./verify_data"),                     # Relative to current directory
            Path("/tmp/verify_data"),                  # Use /tmp directory (usually writable)
            Path.home() / "verify_data",               # User's home directory
            Path.cwd() / "verify_data",                # Current working directory
        ]
        
        # Find the first path that exists and contains verification keys
        self.verify_dir = None
        for path in possible_paths:
            if path.exists():
                # Check if this directory contains .key files
                key_files = list(path.glob("*.key"))
                if key_files:
                    self.verify_dir = path
                    logger.info(f"Found verification keys in: {self.verify_dir}")
                    break
                else:
                    logger.debug(f"Directory exists but contains no .key files: {path}")
            else:
                logger.debug(f"Directory does not exist: {path}")
        
        # If no verification directory was found, try to create one in a writable location
        if self.verify_dir is None:
            # Try several locations in order of preference
            writable_locations = [
                Path.cwd() / "verify_data",    # Current working directory
                Path("/tmp/verify_data"),      # /tmp is usually writable
                Path.home() / "verify_data",   # User's home directory
            ]
            
            for location in writable_locations:
                try:
                    # Try to create a test file to verify we can write here
                    test_path = location.parent / f"test_write_{time.time()}"
                    try:
                        if not location.parent.exists():
                            location.parent.mkdir(parents=True, exist_ok=True)
                        with open(test_path, 'w') as f:
                            f.write('test')
                        # If we can write, this is our verify_dir
                        test_path.unlink()  # Clean up test file
                        self.verify_dir = location
                        logger.info(f"Selected writable location for verification directory: {self.verify_dir}")
                        break
                    except Exception as e:
                        logger.debug(f"Cannot write to {location.parent}: {e}")
                        continue
                except Exception as e:
                    logger.debug(f"Error testing writability for {location}: {e}")
                    continue
            
            if self.verify_dir is None:
                # Last resort - try current directory
                self.verify_dir = Path("./verify_data")
                logger.warning(f"No writable location found. Using fallback location: {self.verify_dir}")
        
        # Create verification directory if it doesn't exist
        if not self.verify_dir.exists():
            try:
                self.verify_dir.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created verification directory: {self.verify_dir}")
            except Exception as e:
                logger.error(f"Failed to create verification directory: {e}")
                # If we still can't create the directory, use a temporary directory
                import tempfile
                self.verify_dir = Path(tempfile.mkdtemp(prefix="verify_data_"))
                logger.warning(f"Using temporary directory as fallback: {self.verify_dir}")
        
        # Log all available verification keys
        if self.verify_dir.exists():
            key_files = list(self.verify_dir.glob("*.key"))
            logger.info(f"Available verification keys: {[k.name for k in key_files]}")

    async def verify_step(self, step_name: str, condition: bool, error_msg: str) -> None:
        """Verify each step with detailed error messages."""
        if not condition:
            logger.error(f"{step_name} failed: {error_msg}")
            raise AssertionError(f"{step_name} failed: {error_msg}")
        logger.info(f"{step_name} completed successfully")

    def validate_proof_data(self, data: dict) -> dict:
        """Validate the structure of incoming proof data and extract the proof_data"""
        # Initialize proof_data to None
        proof_data = None
        
        try:
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
        except Exception as e:
            logger.error(f"Error validating proof data: {e}")
            if proof_data and isinstance(proof_data, dict):
                logger.error(f"Proof data keys: {proof_data.keys()}")
            else:
                logger.error(f"Invalid proof_data type: {type(proof_data)}")
                logger.error(f"Original data keys: {data.keys() if isinstance(data, dict) else type(data)}")
            raise

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

    def find_verification_key(self, model_type: str) -> Path:
        """Find verification key for the model, checking multiple locations"""
        # Check standard name format
        vk_path = self.verify_dir / f"{model_type}_vk.key"
        if vk_path.exists():
            return vk_path
            
        # Check alternative naming convention
        alt_vk_path = self.verify_dir / f"{model_type}.key"
        if alt_vk_path.exists():
            return alt_vk_path
            
        # Check all key files for a partial match
        if self.verify_dir.exists():
            for key_file in self.verify_dir.glob("*.key"):
                if model_type in key_file.name:
                    logger.info(f"Found verification key with partial match: {key_file}")
                    return key_file
        
        # If we reach here, no key was found
        # Log available keys to help debugging
        if self.verify_dir.exists():
            available_keys = list(self.verify_dir.glob("*.key"))
            logger.error(f"Available keys: {[k.name for k in available_keys]}")
            
        # Return the standard path (which doesn't exist) for consistent error handling
        return vk_path

    async def verify_proof(self, data: dict) -> dict:
        """
        Verify EZKL proof using the verification key from setup
        
        Args:
            data: Dictionary containing proof data (either directly or nested under 'proof_data')
            
        Returns:
            Dict containing verification result
        """
        temp_verify_dir = None
        proof_data = None  # Initialize proof_data to None
        model_type = "unknown"  # Initialize model_type with a default value
        
        try:
            # Log received data for debugging
            logger.debug(f"Received data type: {type(data)}")
            if isinstance(data, dict):
                logger.debug(f"Received data keys: {data.keys()}")
                if "status" in data:
                    logger.debug(f"Status: {data['status']}")
                if "error" in data:
                    logger.debug(f"Error in received data: {data['error']}")
                    # If we received an error from the resnet_server, return it directly
                    if data.get("status") == "error":
                        return data
            
            # Validate incoming proof data and get the correct structure
            proof_data = self.validate_proof_data(data)
            
            model_type = proof_data["model_type"]
            
            # Make sure the base verification directory exists
            if not self.verify_dir.exists():
                try:
                    self.verify_dir.mkdir(parents=True, exist_ok=True)
                    logger.info(f"Created main verification directory: {self.verify_dir}")
                except Exception as e:
                    logger.error(f"Failed to create main verification directory: {e}")
                    # Fall back to using a temporary directory
                    import tempfile
                    temp_base_dir = Path(tempfile.mkdtemp(prefix="verify_"))
                    logger.warning(f"Using temporary directory as fallback: {temp_base_dir}")
                    self.verify_dir = temp_base_dir

            # Create the temporary directory path
            try:
                temp_verify_dir = self.verify_dir / f"temp_{model_type}"
            except Exception as e:
                # If we can't create in the original directory, use a system temp directory
                import tempfile
                temp_verify_dir = Path(tempfile.mkdtemp(prefix=f"verify_{model_type}_"))
                logger.warning(f"Using system temporary directory as fallback: {temp_verify_dir}")
            
            # Log the temporary directory path
            logger.debug(f"Using temporary directory: {temp_verify_dir}")
            
            # Create temporary directory with clean state
            if temp_verify_dir.exists():
                shutil.rmtree(temp_verify_dir)
                logger.debug(f"Removed existing temporary directory: {temp_verify_dir}")
                
            # Create the temporary directory
            temp_verify_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created new temporary directory: {temp_verify_dir}")
            
            # Double-check that the directory was created
            if not temp_verify_dir.exists():
                logger.error(f"Failed to create temporary directory: {temp_verify_dir}")
                raise FileNotFoundError(f"Could not create temporary directory: {temp_verify_dir}")

            # Find verification key using the flexible finder
            vk_path = self.find_verification_key(model_type)
            logger.debug(f"Looking for verification key at: {vk_path}")
            
            # List all files in verify_dir for debugging
            if self.verify_dir.exists():
                logger.debug(f"Files in {self.verify_dir}: {list(self.verify_dir.glob('*'))}")
            
            if not vk_path.exists():
                raise FileNotFoundError(
                    f"Verification key not found at {vk_path}. "
                    "Please ensure setup.py has been run to generate keys."
                )

            # Prepare verification files
            proof_path, settings_path = await self.prepare_verification_files(
                proof_data, temp_verify_dir
            )
            
            # Verify the files were created successfully
            if not proof_path.exists() or not settings_path.exists():
                logger.error(f"Verification files not created. Proof path exists: {proof_path.exists()}, Settings path exists: {settings_path.exists()}")
                raise FileNotFoundError(f"Failed to create verification files in {temp_verify_dir}")

            # Log verification attempt
            logger.info(f"Attempting to verify proof for {model_type}")
            logger.debug(f"Using verification key: {vk_path}")
            logger.debug(f"Using proof file: {proof_path}")
            logger.debug(f"Using settings file: {settings_path}")

            # Start timing the verification
            start_time = time.time()
            
            # Verify the proof
            logger.info("Verifying proof...")
            is_valid = ezkl.verify(
                str(proof_path),
                str(settings_path),
                str(vk_path)
            )
            
            # Calculate and print verification time in milliseconds
            verification_time_ms = (time.time() - start_time) * 1000
            logger.info(f"Verification time: {verification_time_ms:.2f} ms")
            
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
                "model_type": model_type if proof_data else "unknown"
            }
        except ValueError as e:
            logger.error(f"Validation error: {e}")
            return {
                "status": "error",
                "error": str(e),
                "is_valid": False,
                "model_type": model_type if proof_data else "unknown"
            }
        except Exception as e:
            logger.error(f"Error verifying proof: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                "status": "error",
                "error": str(e),
                "is_valid": False,
                "model_type": model_type if proof_data else "unknown"
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
        return self.find_verification_key(model_type)