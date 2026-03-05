import cv2
import numpy as np
import os


class StyleEngine:
    def __init__(self, model_path):
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found: {model_path}")
        self.net = cv2.dnn.readNetFromONNX(model_path)
        self.net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
        self.net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)

    def stylize(self, image_bytes: bytes, strength: float = 1.0) -> bytes:
        strength = max(0.0, min(1.0, strength))

        image_array = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

        if image is None:
            raise ValueError("Could not decode image bytes")

        original = image.copy()
        h, w = image.shape[:2]

        size = 320
        image_small = cv2.resize(image, (size, size))

        blob = cv2.dnn.blobFromImage(
            image_small,
            1.0,
            (size, size),
            (103.939, 116.779, 123.680),
            swapRB=True,
            crop=False
        )

        self.net.setInput(blob)
        output = self.net.forward()

        output = output.reshape((3, output.shape[2], output.shape[3]))
        output = output.transpose(1, 2, 0)

        output[:, :, 0] += 103.939
        output[:, :, 1] += 116.779
        output[:, :, 2] += 123.680

        styled = np.clip(output, 0, 255).astype(np.uint8)
        styled = cv2.resize(styled, (w, h))

        final = cv2.addWeighted(styled, strength, original, 1 - strength, 0)

        _, buffer = cv2.imencode(".jpg", final)
        return buffer.tobytes()