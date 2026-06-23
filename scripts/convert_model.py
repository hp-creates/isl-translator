"""Convert Keras .h5 model to TensorFlow Lite format.

Usage:
    pip install tensorflow>=2.15.0
    python scripts/convert_model.py

This script converts the ISL hand sign classification model from
Keras H5 format to TFLite format, reducing the runtime dependency
from ~2 GB (TensorFlow) to ~5 MB (tflite-runtime).
"""

from __future__ import annotations

import sys
from pathlib import Path

# Paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
H5_MODEL_PATH = PROJECT_ROOT / "isl_model_2hand.h5"
TFLITE_OUTPUT_DIR = PROJECT_ROOT / "backend" / "model"
TFLITE_OUTPUT_PATH = TFLITE_OUTPUT_DIR / "isl_model_2hand.tflite"


def convert() -> None:
    """Convert .h5 model to .tflite format."""
    try:
        import tensorflow as tf
    except ImportError:
        print("Error: TensorFlow is required for conversion.")
        print("Install it with: pip install tensorflow>=2.15.0")
        sys.exit(1)

    if not H5_MODEL_PATH.exists():
        print(f"Error: Model not found at {H5_MODEL_PATH}")
        print("Make sure 'isl_model_2hand.h5' is in the project root.")
        sys.exit(1)

    print(f"Loading model from: {H5_MODEL_PATH}")
    model = tf.keras.models.load_model(str(H5_MODEL_PATH))
    model.summary()

    print("\nConverting to TFLite format...")
    converter = tf.lite.TFLiteConverter.from_keras_model(model)

    # Optimise for size and speed
    converter.optimizations = [tf.lite.Optimize.DEFAULT]

    tflite_model = converter.convert()

    # Ensure output directory exists
    TFLITE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Write .tflite file
    with open(TFLITE_OUTPUT_PATH, "wb") as f:
        f.write(tflite_model)

    h5_size = H5_MODEL_PATH.stat().st_size / 1024
    tflite_size = TFLITE_OUTPUT_PATH.stat().st_size / 1024

    print(f"\nConversion complete!")
    print(f"  H5 model:     {h5_size:.1f} KB")
    print(f"  TFLite model:  {tflite_size:.1f} KB")
    print(f"  Size reduction: {(1 - tflite_size / h5_size) * 100:.1f}%")
    print(f"  Output: {TFLITE_OUTPUT_PATH}")


if __name__ == "__main__":
    convert()
