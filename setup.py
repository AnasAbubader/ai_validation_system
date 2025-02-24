import os
from pathlib import Path
import ezkl
import json
import logging
import torch
import torchvision.models as models
import asyncio
import numpy as np

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SetupManager:
    def __init__(self):
        # Get the current file's directory (assumed to be in project root)
        self.project_root = Path(__file__).parent
        
        # Define directories
        self.resnet_server_dir = self.project_root / "resnet_server"
        self.middleware_dir = self.project_root / "middleware"
        
        # Define specific paths
        self.onnx_dir = self.resnet_server_dir / "app" / "models" / "onnx"
        self.proof_dir = self.resnet_server_dir / "proof_data"
        self.verify_dir = self.middleware_dir / "verify_data"
        
        # Model types
        self.model_types = ["resnet18", "resnet34"]

    def create_directories(self):
        """Create all necessary directories"""
        directories = [
            self.onnx_dir,
            self.proof_dir,
            self.verify_dir
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {directory}")

    def create_optimized_resnet34(self):
        """Create a memory-optimized version of ResNet34."""
        model = models.resnet34(weights=None)
        
        # Define minimal channel dimensions
        channels = [8, 8, 16, 16, 32]  # Reduced channel growth
        
        # Reduce first layer
        model.conv1 = torch.nn.Conv2d(3, channels[0], kernel_size=3, stride=2, padding=1, bias=False)
        model.bn1 = torch.nn.BatchNorm2d(channels[0])
        model.maxpool = torch.nn.Identity()

        def update_basic_block(block, in_channels, out_channels, stride=1):
            block.conv1 = torch.nn.Conv2d(in_channels, out_channels, 
                                        kernel_size=3, stride=stride, padding=1, bias=False)
            block.bn1 = torch.nn.BatchNorm2d(out_channels)
            block.conv2 = torch.nn.Conv2d(out_channels, out_channels, 
                                        kernel_size=3, stride=1, padding=1, bias=False)
            block.bn2 = torch.nn.BatchNorm2d(out_channels)
            
            if stride != 1 or in_channels != out_channels:
                block.downsample = torch.nn.Sequential(
                    torch.nn.Conv2d(in_channels, out_channels, 
                                  kernel_size=1, stride=stride, bias=False),
                    torch.nn.BatchNorm2d(out_channels)
                )
            else:
                block.downsample = None

        # Update layer1 (8 -> 8)
        update_basic_block(model.layer1[0], channels[0], channels[1])
        model.layer1 = torch.nn.Sequential(model.layer1[0])
        
        # Update layer2 (8 -> 16)
        update_basic_block(model.layer2[0], channels[1], channels[2], stride=2)
        model.layer2 = torch.nn.Sequential(model.layer2[0])
        
        # Update layer3 (16 -> 16)
        update_basic_block(model.layer3[0], channels[2], channels[3], stride=2)
        model.layer3 = torch.nn.Sequential(model.layer3[0])
        
        # Update layer4 (16 -> 32)
        update_basic_block(model.layer4[0], channels[3], channels[4], stride=2)
        model.layer4 = torch.nn.Sequential(model.layer4[0])
        
        # Update final layer
        model.fc = torch.nn.Linear(channels[4], 2)
        
        return model

    def create_optimized_resnet18(self):
        """Create a memory-optimized version of ResNet18"""
        model = models.resnet18(weights=None)
        
        # Use the same channel configuration as ResNet34 for consistency
        channels = [8, 8, 16, 16, 32]
        
        # Reduce first layer
        model.conv1 = torch.nn.Conv2d(3, channels[0], kernel_size=3, stride=2, padding=1, bias=False)
        model.bn1 = torch.nn.BatchNorm2d(channels[0])
        model.maxpool = torch.nn.Identity()
        
        def update_basic_block(block, in_channels, out_channels, stride=1):
            block.conv1 = torch.nn.Conv2d(in_channels, out_channels, 
                                        kernel_size=3, stride=stride, padding=1, bias=False)
            block.bn1 = torch.nn.BatchNorm2d(out_channels)
            block.conv2 = torch.nn.Conv2d(out_channels, out_channels, 
                                        kernel_size=3, stride=1, padding=1, bias=False)
            block.bn2 = torch.nn.BatchNorm2d(out_channels)
            
            if stride != 1 or in_channels != out_channels:
                block.downsample = torch.nn.Sequential(
                    torch.nn.Conv2d(in_channels, out_channels, 
                                  kernel_size=1, stride=stride, bias=False),
                    torch.nn.BatchNorm2d(out_channels)
                )
            else:
                block.downsample = None

        # Apply the same layer modifications as ResNet34
        update_basic_block(model.layer1[0], channels[0], channels[1])
        model.layer1 = torch.nn.Sequential(model.layer1[0])
        
        update_basic_block(model.layer2[0], channels[1], channels[2], stride=2)
        model.layer2 = torch.nn.Sequential(model.layer2[0])
        
        update_basic_block(model.layer3[0], channels[2], channels[3], stride=2)
        model.layer3 = torch.nn.Sequential(model.layer3[0])
        
        update_basic_block(model.layer4[0], channels[3], channels[4], stride=2)
        model.layer4 = torch.nn.Sequential(model.layer4[0])
        
        model.fc = torch.nn.Linear(channels[4], 2)
        
        return model

    async def setup_model(self, model_type: str):
        """Setup initial files for a specific model"""
        try:
            logger.info(f"Setting up {model_type}...")
            
            # Create model-specific proof directory
            model_proof_dir = self.proof_dir / model_type
            model_proof_dir.mkdir(exist_ok=True)

            # Define paths
            onnx_path = self.onnx_dir / f"{model_type}.onnx"
            settings_path = model_proof_dir / "settings.json"
            circuit_path = model_proof_dir / "circuit.ezkl"
            pk_path = model_proof_dir / "pk.key"
            vk_path = self.verify_dir / f"{model_type}_vk.key"

            # Create and export optimized model
            logger.info(f"Creating and exporting optimized {model_type} to ONNX...")
            if model_type == "resnet34":
                model = self.create_optimized_resnet34()
            else:  # resnet18
                model = self.create_optimized_resnet18()
            
            model.eval()
            dummy_input = torch.randn(1, 3, 32, 32)  # Smaller input size
            
            torch.onnx.export(
                model, 
                dummy_input,
                onnx_path,
                input_names=['input'],
                output_names=['output'],
                export_params=True,
                opset_version=10,
                do_constant_folding=True
            )

            # Generate settings with memory optimizations
            logger.info("Generating settings...")
            run_args = ezkl.PyRunArgs()
            run_args.input_visibility = "private"
            run_args.param_visibility = "fixed"
            run_args.output_visibility = "public"
            run_args.num_inner_cols = 8
            
            res = ezkl.gen_settings(str(onnx_path), str(settings_path), py_run_args=run_args)
            if not res:
                raise Exception("Failed to generate settings")
            
            # Update settings with memory optimizations
            with open(settings_path, 'r') as f:
                settings = json.load(f)
            settings['curve'] = 'bn254'
            settings['strategy'] = 'lookup'
            settings['lookup_bits'] = 4
            with open(settings_path, 'w') as f:
                json.dump(settings, f)

            # Compile circuit
            logger.info("Compiling circuit...")
            res = ezkl.compile_circuit(str(onnx_path), str(circuit_path), str(settings_path))
            if not res:
                raise Exception("Failed to compile circuit")

            # Generate keys
            logger.info("Generating keys...")
            res = ezkl.setup(str(circuit_path), str(vk_path), str(pk_path))
            if not res:
                raise Exception("Failed to generate keys")

            # Save configuration
            config = {
                "onnx_path": str(onnx_path),
                "settings_path": str(settings_path),
                "circuit_path": str(circuit_path),
                "vk_path": str(vk_path),
                "pk_path": str(pk_path)
            }
            
            config_path = model_proof_dir / "config.json"
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=4)
            
            logger.info(f"Successfully completed setup for {model_type}")
            return True

        except Exception as e:
            logger.error(f"Error during setup of {model_type}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False

async def main():
    """Main setup function"""
    logger.info("Starting setup process...")
    
    setup_manager = SetupManager()
    
    # Create necessary directories
    setup_manager.create_directories()
    
    # Setup each model type
    for model_type in setup_manager.model_types:
        success = await setup_manager.setup_model(model_type)
        if success:
            logger.info(f"Successfully set up {model_type}")
        else:
            logger.error(f"Failed to set up {model_type}")
    
    logger.info("Setup process completed")

if __name__ == "__main__":
    asyncio.run(main())