# resnet_server/app/utils/proof_generator.py
import ezkl
from pathlib import Path
import json
import numpy as np
import torch
import logging

logger = logging.getLogger(__name__)

class ProofGenerator:
    def __init__(self):
        # Define base paths
        self.base_dir = Path("ai-validation-system")
        self.resnet_server_dir = self.base_dir / "resnet_server"
        
        # Define specific paths
        self.onnx_dir = self.resnet_server_dir / "app" / "models" / "onnx"
        self.proof_dir = self.resnet_server_dir / "proof_data"
        
        # Create necessary directories
        self.proof_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Initialized ProofGenerator with ONNX dir: {self.onnx_dir}")
        logger.info(f"Proof data will be saved to: {self.proof_dir}")

    async def verify_step(self, step_name: str, condition: bool, error_msg: str) -> None:
        """Verify each step with detailed error messages."""
        if not condition:
            logger.error(f"{step_name} failed: {error_msg}")
            raise AssertionError(f"{step_name} failed: {error_msg}")
        logger.info(f"{step_name} completed successfully")

    async def generate_proof(self, model_type: str, input_data: np.ndarray):
        """Generate EZKL proof for model inference using optimized approach"""
        try:
            # Create model-specific proof directory
            model_proof_dir = self.proof_dir / model_type
            model_proof_dir.mkdir(exist_ok=True)
            
            # Define file paths
            onnx_path = self.onnx_dir / f"{model_type}.onnx"
            settings_path = model_proof_dir / "settings.json"
            circuit_path = model_proof_dir / "circuit.ezkl"
            pk_path = model_proof_dir / "pk.key"
            witness_path = model_proof_dir / "witness.json"
            proof_path = model_proof_dir / "proof.json"
            input_path = model_proof_dir / "input.json"

            # Verify ONNX file exists
            if not onnx_path.exists():
                raise FileNotFoundError(f"ONNX model not found at {onnx_path}")

            # Prepare input data
            input_tensor = torch.tensor(input_data).reshape(1, 3, 32, 32)
            input_json = {
                "input_data": [input_tensor.numpy().reshape([-1]).tolist()]
            }
            with open(input_path, "w") as f:
                json.dump(input_json, f)
            await self.verify_step("Input creation", input_path.exists(), "Failed to create input file")

            # Generate settings if needed
            if not settings_path.exists():
                logger.info("Generating settings...")
                run_args = ezkl.PyRunArgs()
                run_args.input_visibility = "private"
                run_args.param_visibility = "fixed"
                run_args.output_visibility = "public"
                run_args.num_inner_cols = 8
                
                res = ezkl.gen_settings(str(onnx_path), str(settings_path), py_run_args=run_args)
                await self.verify_step("Settings generation", res, "Failed to generate settings")
                
                # Update settings with optimized parameters
                with open(settings_path, 'r') as f:
                    settings = json.load(f)
                settings['curve'] = 'bn254'
                settings['strategy'] = 'lookup'
                settings['lookup_bits'] = 4
                with open(settings_path, 'w') as f:
                    json.dump(settings, f)

            # Compile circuit if needed
            if not circuit_path.exists():
                logger.info("Compiling circuit...")
                res = ezkl.compile_circuit(str(onnx_path), str(circuit_path), str(settings_path))
                await self.verify_step("Circuit compilation", res, "Failed to compile circuit")

            # Generate proving key if needed
            if not pk_path.exists():
                logger.info("Generating proving key...")
                vk_path = self.base_dir / "middleware" / "verify_data" / f"{model_type}_vk.key"
                res = ezkl.setup(str(circuit_path), str(vk_path), str(pk_path))
                await self.verify_step("Key generation", res, "Failed to generate keys")

            # Generate witness
            logger.info("Generating witness...")
            res = await ezkl.gen_witness(
                str(input_path),
                str(circuit_path),
                str(witness_path)
            )
            await self.verify_step("Witness generation", res, "Failed to generate witness")

            # Generate proof
            logger.info("Generating proof...")
            res = ezkl.prove(
                str(witness_path),
                str(circuit_path),
                str(pk_path),
                str(proof_path),
                "single"
            )
            await self.verify_step("Proof generation", res, "Failed to generate proof")

            # Prepare return data
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