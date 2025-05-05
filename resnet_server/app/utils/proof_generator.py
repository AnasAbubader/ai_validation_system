# resnet_server/app/utils/proof_generator.py
import ezkl
from pathlib import Path
import json
import numpy as np
import torch
import logging
import torchvision.transforms as transforms
from PIL import Image
import os
import io

logger = logging.getLogger(__name__)

class ProofGenerator:
    def __init__(self):
        # Use relative paths from the current directory
        self.resnet_server_dir = Path("/app")  # Base directory in Docker
        if not self.resnet_server_dir.exists():
            # Fallback for local development
            current_file = Path(__file__)
            self.resnet_server_dir = current_file.parent.parent.parent
        
        # Define paths based on setup.py structure
        self.onnx_dir = self.resnet_server_dir / "app" / "models" / "onnx"
        self.proof_dir = self.resnet_server_dir / "proof_data"
        
        # Define image transformation pipeline
        self.transform = transforms.Compose([
            transforms.Resize((32, 32)),
            transforms.ToTensor(),
        ])
        
        logger.info(f"Initialized ProofGenerator with ONNX dir: {self.onnx_dir}")
        logger.info(f"Proof data directory: {self.proof_dir}")

    async def verify_step(self, step_name: str, condition: bool, error_msg: str) -> None:
        """Verify each step with detailed error messages."""
        if not condition:
            logger.error(f"{step_name} failed: {error_msg}")
            raise AssertionError(f"{step_name} failed: {error_msg}")
        logger.info(f"{step_name} completed successfully")

    async def load_config(self, model_type: str) -> dict:
        """Load model configuration from setup"""
        config_path = self.proof_dir / model_type / "config.json"
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration not found at {config_path}")
        
        with open(config_path, 'r') as f:
            config = json.load(f)
            
        # Replace absolute paths with relative paths based on our current directory
        for key in ["circuit_path", "settings_path", "pk_path"]:
            if key in config:
                path_str = config[key]
                # Convert to a Path object and get just the filename
                filename = os.path.basename(path_str)
                # Create a relative path in the proof directory
                relative_path = str(self.proof_dir / model_type / filename)
                config[key] = relative_path
                
        return config

    def preprocess_input(self, input_data: np.ndarray) -> torch.Tensor:
        """Preprocess input data to match model requirements"""
        try:
            # Log input shape and size for debugging
            logger.info(f"Original input shape: {input_data.shape}, size: {input_data.size}")
            
            # Determine input format and reshape accordingly
            if input_data.size == 150528:  # 224x224x3 flattened
                # Reshape to image dimensions
                height = width = int(np.sqrt(input_data.size // 3))
                input_data = input_data.reshape(height, width, 3)
            
            # Convert numpy array to PIL Image
            input_image = Image.fromarray(input_data.astype('uint8'))
            
            # Apply transformation pipeline
            transformed_input = self.transform(input_image)
            
            # Ensure correct shape [1, 3, 32, 32]
            if transformed_input.shape != (3, 32, 32):
                raise ValueError(f"Unexpected shape after transform: {transformed_input.shape}")
            
            # Add batch dimension
            transformed_input = transformed_input.unsqueeze(0)
            
            logger.info(f"Preprocessed input shape: {transformed_input.shape}")
            return transformed_input
            
        except Exception as e:
            logger.error(f"Error in preprocessing: {e}")
            raise

    async def generate_proof(self, model_type: str, input_data: np.ndarray):
        """Generate EZKL proof using the optimized setup"""
        try:
            # Load configuration created by setup.py
            config = await self.load_config(model_type)
            
            # Get paths from config
            model_proof_dir = self.proof_dir / model_type
            witness_path = model_proof_dir / "witness.json"
            proof_path = model_proof_dir / "proof.json"
            input_path = model_proof_dir / "input.json"

            # Create paths using the model_proof_dir as base
            # The config now contains relative paths
            circuit_path = Path(config["circuit_path"])
            settings_path = Path(config["settings_path"])
            pk_path = Path(config["pk_path"])

            # Log paths for debugging
            logger.debug(f"Circuit path: {circuit_path}")
            logger.debug(f"Settings path: {settings_path}")
            logger.debug(f"PK path: {pk_path}")

            # Verify required files exist
            required_files = {
                "Circuit": circuit_path,
                "Settings": settings_path,
                "Proving key": pk_path
            }
            
            for name, path in required_files.items():
                if not path.exists():
                    logger.error(f"{name} file not found at {path}")
                    # Check if file exists with different casing
                    parent_dir = path.parent
                    if parent_dir.exists():
                        all_files = list(parent_dir.glob("*"))
                        logger.error(f"Files in {parent_dir}: {all_files}")
                    raise FileNotFoundError(f"{name} file not found at {path}")

            # Preprocess input data
            processed_input = self.preprocess_input(input_data)
            
            # Prepare input for EZKL
            input_json = {
                "input_data": [processed_input.numpy().reshape([-1]).tolist()]
            }
            with open(input_path, "w") as f:
                json.dump(input_json, f)
            await self.verify_step("Input creation", input_path.exists(), "Failed to create input file")

            # Generate witness
            logger.info("Generating witness...")
            res = await ezkl.gen_witness(
                str(input_path),
                str(circuit_path),
                str(witness_path)
            )
            await self.verify_step("Witness generation", res, "Failed to generate witness")

            # Generate proof using optimized settings
            logger.info("Generating proof...")
            res = ezkl.prove(
                str(witness_path),
                str(circuit_path),
                str(pk_path),
                str(proof_path),
                "single"
            )
            await self.verify_step("Proof generation", res, "Failed to generate proof")

            # Load proof and settings data
            with open(proof_path, 'r') as f:
                proof_data = json.load(f)
            with open(settings_path, 'r') as f:
                settings_data = json.load(f)

            return {
                "status": "success",
                "proof_data": {
                    "proof": proof_data,
                    "settings": settings_data,
                    "model_type": model_type
                },
                "is_valid": True
            }

        except Exception as e:
            logger.error(f"Error generating proof: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                "status": "error",
                "error": str(e),
                "is_valid": False,
                "model_type": model_type
            }