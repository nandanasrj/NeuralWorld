import torch
import torchvision.transforms as transforms
import torchvision.models as models
from PIL import Image
import cv2
import numpy as np

device = torch.device("cpu")

print("Loading pretrained model...")

# Using a lightweight pretrained model just to verify pipeline
model = models.mobilenet_v2(weights="DEFAULT")
model.eval()

print("Model loaded successfully.")

# Load image
image_path = "backend/test.jpg"

image = Image.open(image_path).convert("RGB")

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor()
])

img_tensor = transform(image).unsqueeze(0)

with torch.no_grad():
    output = model(img_tensor)

print("Inference successful.")
print("Output shape:", output.shape)