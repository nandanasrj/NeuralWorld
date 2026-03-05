import cv2
import numpy as np

print("Loading ONNX style model...")

model_path = "backend/models/mosaic.onnx"
image_path = "backend/test.jpg"

net = cv2.dnn.readNetFromONNX(model_path)

print("Model loaded.")

img = cv2.imread(image_path)

(h, w) = img.shape[:2]

# Resize for speed (optional)
img_resized = cv2.resize(img, (600, 600))

blob = cv2.dnn.blobFromImage(
    img_resized,
    1.0,
    (600, 600),
    (103.939, 116.779, 123.680),
    swapRB=True,
    crop=False
)

net.setInput(blob)
output = net.forward()

output = output.reshape((3, output.shape[2], output.shape[3]))
output = output.transpose(1, 2, 0)

# Add mean values back
output[:, :, 0] += 103.939
output[:, :, 1] += 116.779
output[:, :, 2] += 123.680

styled = np.clip(output, 0, 255).astype(np.uint8)

styled = cv2.resize(styled, (w, h))

cv2.imwrite("backend/styled_output.jpg", styled)

print("Style transfer complete.")