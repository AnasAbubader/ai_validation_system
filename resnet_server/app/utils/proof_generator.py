# resnet_server/app/utils/proof_generator.py
import ezkl
from pathlib import Path
import json
import numpy as np
import torch
import logging
from ..config import ONNX_DIR

logger = logging.getLogger(__name__)

class ProofGenerator:
    def __init__(self):
        self.base_dir = Path(".")
        self.models_dir = self.base_dir / "models"
        self.proof_dir = self.base_dir / "proof_data"
        self.verify_dir = self.base_dir / "verify_data"
        
        # Create necessary directories
        for dir_path in [self.models_dir, self.proof_dir, self.verify_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

    async def verify_step(self, step_name: str, condition: bool, error_msg: str) -> None:
        """Verify each step with detailed error messages."""
        if not condition:
            logger.error(f"{step_name} failed: {error_msg}")
            raise AssertionError(f"{step_name} failed: {error_msg}")
        logger.info(f"{step_name} completed successfully")

    async def generate_proof(self, model_type: str, input_data: np.ndarray):
        """Generate EZKL proof for model inference using optimized approach"""
        try:
            # Define file paths
            onnx_path = self.models_dir / f"{model_type}.onnx"
            settings_path = self.proof_dir / f"{model_type}_settings.json"
            circuit_path = self.proof_dir / f"{model_type}_circuit.ezkl"
            vk_path = self.verify_dir / f"{model_type}_vk.key"
            pk_path = self.proof_dir / f"{model_type}_pk.key"
            witness_path = self.proof_dir / "witness.json"
            proof_path = self.proof_dir / "proof.json"
            input_path = self.proof_dir / "input.json"

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

            # Generate keys if needed
            if not (vk_path.exists() and pk_path.exists()):
                logger.info("Generating keys...")
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

            # Local verification before sending
            res = ezkl.verify(
                str(proof_path),
                str(settings_path),
                str(vk_path)
            )
            await self.verify_step("Local proof verification", res, "Failed to verify proof")

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