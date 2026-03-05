import cv2
import numpy as np
import time
import os

cv2.setUseOptimized(True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

models = {
    "mosaic":        cv2.dnn.readNetFromONNX(os.path.join(BASE_DIR, "models/mosaic.onnx")),
    "pointilism":    cv2.dnn.readNetFromONNX(os.path.join(BASE_DIR, "models/pointilism.onnx")),
    "udnie":         cv2.dnn.readNetFromONNX(os.path.join(BASE_DIR, "models/udnie.onnx")),
    "candy":         cv2.dnn.readNetFromONNX(os.path.join(BASE_DIR, "models/candy.onnx")),
    "rain_princess": cv2.dnn.readNetFromONNX(os.path.join(BASE_DIR, "models/rain_princess.onnx")),
}

for net in models.values():
    net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
    net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)

style_names = list(models.keys())
current_style_index = 0
strength = 1.0

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: Cannot open webcam.")
    exit()

frame_count = 0
inference_interval = 3
last_styled = None
prev_time = 0

print("Controls:")
print("n / p  → next / previous style")
print("= / -  → increase / decrease strength")
print("q      → quit")

while True:
    ret, frame = cap.read()
    if not ret:
        print("Error: Failed to read frame from webcam.")
        break

    original = frame.copy()
    h, w = original.shape[:2]

    frame_count += 1

    if frame_count % inference_interval == 0 or last_styled is None:
        size = 320
        small = cv2.resize(frame, (size, size))

        blob = cv2.dnn.blobFromImage(
            small,
            1.0,
            (size, size),
            (103.939, 116.779, 123.680),
            swapRB=True,
            crop=False
        )

        net = models[style_names[current_style_index]]
        net.setInput(blob)
        output = net.forward()

        output = output.reshape((3, output.shape[2], output.shape[3]))
        output = output.transpose(1, 2, 0)

        output[:, :, 0] += 103.939
        output[:, :, 1] += 116.779
        output[:, :, 2] += 123.680

        styled = np.clip(output, 0, 255).astype(np.uint8)
        styled = cv2.resize(styled, (w, h))

        last_styled = cv2.addWeighted(styled, strength, original, 1 - strength, 0)

    combined = last_styled.copy()

    curr_time = time.time()
    fps = 1 / (curr_time - prev_time) if prev_time != 0 else 0
    prev_time = curr_time

    cv2.putText(combined, f"{style_names[current_style_index]}",
                (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
    cv2.putText(combined, f"Strength: {round(strength, 2)}",
                (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    cv2.putText(combined, f"FPS: {int(fps)}",
                (20, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    cv2.imshow("NeuralWorld Webcam", combined)

    key = cv2.waitKey(1) & 0xFF

    if key == ord('n'):
        current_style_index = (current_style_index + 1) % len(style_names)
        last_styled = None
    elif key == ord('p'):
        current_style_index = (current_style_index - 1) % len(style_names)
        last_styled = None
    elif key == ord('='):        # increase strength
        strength = min(1.0, round(strength + 0.1, 1))
        last_styled = None
    elif key == ord('-'):        # decrease strength
        strength = max(0.0, round(strength - 0.1, 1))
        last_styled = None
    elif key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()