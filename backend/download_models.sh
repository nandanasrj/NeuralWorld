#!/bin/bash
mkdir -p /app/backend/models
BASE="https://github.com/nandanasrj/NeuralWorld/releases/download/v1.0"

for model in candy mosaic pointilism rain_princess udnie; do
  if [ ! -f "/app/backend/models/${model}.onnx" ]; then
    echo "Downloading ${model}.onnx..."
    curl -L -o "/app/backend/models/${model}.onnx" "${BASE}/${model}.onnx"
  fi
done
