from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from style_engine import StyleEngine

import cv2
import numpy as np
import tempfile
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

engines = {
    "mosaic":         StyleEngine(os.path.join(BASE_DIR, "models/mosaic.onnx")),
    "pointilism":     StyleEngine(os.path.join(BASE_DIR, "models/pointilism.onnx")),
    "udnie":          StyleEngine(os.path.join(BASE_DIR, "models/udnie.onnx")),
    "candy":          StyleEngine(os.path.join(BASE_DIR, "models/candy.onnx")),
    "rain_princess":  StyleEngine(os.path.join(BASE_DIR, "models/rain_princess.onnx")),
}


@app.get("/")
def root():
    return {"message": "NeuralWorld API running"}


# ================= IMAGE =================
@app.post("/stylize")
async def stylize(
    file: UploadFile = File(...),
    style: str = Form(...),
    strength: float = Form(1.0)
):
    if style not in engines:
        raise HTTPException(status_code=400, detail="Invalid style")

    strength = max(0.0, min(1.0, strength))

    image_bytes = await file.read()
    styled = engines[style].stylize(image_bytes, strength)

    return Response(content=styled, media_type="image/jpeg")


# ================= VIDEO =================
@app.post("/stylize_video")
async def stylize_video(
    file: UploadFile = File(...),
    style: str = Form(...),
    strength: float = Form(1.0)
):
    if style not in engines:
        raise HTTPException(status_code=400, detail="Invalid style")

    strength = max(0.0, min(1.0, strength))

    input_path = None
    output_path = None

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_input:
            temp_input.write(await file.read())
            input_path = temp_input.name

        temp_output = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
        output_path = temp_output.name
        temp_output.close()

        cap = cv2.VideoCapture(input_path)

        if not cap.isOpened():
            raise HTTPException(status_code=400, detail="Could not open video file")

        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps == 0:
            fps = 24

        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        fourcc = cv2.VideoWriter_fourcc(*"avc1")
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        engine = engines[style]

        frame_count = 0
        inference_interval = 5
        last_styled = None

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame_count += 1

            if frame_count % inference_interval == 0 or last_styled is None:
                frame_small = cv2.resize(frame, (320, 320))
                frame_bytes = cv2.imencode(".jpg", frame_small)[1].tobytes()

                styled_bytes = engine.stylize(frame_bytes, strength)

                styled_frame = cv2.imdecode(
                    np.frombuffer(styled_bytes, np.uint8),
                    cv2.IMREAD_COLOR
                )

                last_styled = cv2.resize(styled_frame, (width, height))

            out.write(last_styled)

        cap.release()
        out.release()

        with open(output_path, "rb") as f:
            video_bytes = f.read()

        return Response(content=video_bytes, media_type="video/mp4")

    finally:
        if input_path and os.path.exists(input_path):
            os.remove(input_path)
        if output_path and os.path.exists(output_path):
            os.remove(output_path)