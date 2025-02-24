import torch
import torchvision.models as models
from torchvision import transforms
import onnx
from PIL import Image
import os
from ..config import MODEL_URLS, MODELS_DIR, ONNX_DIR
import logging

logger = logging.getLogger(__name__)

class ModelManager:
    def __init__(self):
        self.models = {}
        self.transform = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])

    async def load_models(self):
        """Load ResNet models and convert to ONNX format"""
        for model_name in MODEL_URLS:
            # Load PyTorch model with the new weights parameter
            if model_name == "resnet18":
                model = models.resnet18(weights=None)  # Changed from pretrained=False
            else:  # resnet34
                model = models.resnet34(weights=None)  # Changed from pretrained=False
            
            # Download weights if not exists
            weights_path = MODELS_DIR / f"{model_name}.pth"
            if not weights_path.exists():
                logger.info(f"Downloading weights for {model_name}")
                torch.hub.download_url_to_file(
                    MODEL_URLS[model_name],
                    weights_path
                )
            
            # Load weights
            model.load_state_dict(torch.load(weights_path))
            model.eval()
            self.models[model_name] = model
            
            # Convert to ONNX if not exists
            onnx_path = ONNX_DIR / f"{model_name}.onnx"
            if not onnx_path.exists():
                logger.info(f"Converting {model_name} to ONNX format")
                self._convert_to_onnx(model, model_name)

    def _convert_to_onnx(self, model, model_name):
        """Convert PyTorch model to ONNX format"""
        dummy_input = torch.randn(1, 3, 224, 224)
        onnx_path = ONNX_DIR / f"{model_name}.onnx"
        
        torch.onnx.export(
            model,
            dummy_input,
            onnx_path,
            export_params=True,
            opset_version=11,
            do_constant_folding=True,
            input_names=['input'],
            output_names=['output']
        )
        logger.info(f"Successfully converted {model_name} to ONNX format")

    async def process_image(self, image_path: str, model_type: str):
        """Process image with specified ResNet model"""
        if model_type not in self.models:
            raise ValueError(f"Unknown model type: {model_type}")
        
        # Load and preprocess image
        image = Image.open(image_path).convert('RGB')
        input_tensor = self.transform(image)
        input_batch = input_tensor.unsqueeze(0)
        
        # Run inference
        with torch.no_grad():
            output = self.models[model_type](input_batch)
        
        # Get top prediction
        probabilities = torch.nn.functional.softmax(output[0], dim=0)
        top_prob, top_class = torch.topk(probabilities, 1)
        
        return {
            "class_id": top_class.item(),
            "probability": top_prob.item()
        }