"""Sign classifier — TFLite model inference for ISL character recognition.

Loads a TensorFlow Lite model and label map, then classifies
hand landmark feature vectors into ISL characters (A-Z, 1-9).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import numpy as np

from app.utils.logging import get_logger

logger = get_logger("sign_classifier")


class SignClassifier:
    """Classifies hand landmark features into ISL characters using TFLite.

    Uses TFLite runtime for lightweight inference — avoids the ~2 GB
    TensorFlow dependency in production.
    """

    def __init__(self, model_path: str, labels_path: str) -> None:
        """Load the TFLite model and label map.

        Args:
            model_path: Path to the .tflite model file.
            labels_path: Path to the labels JSON file.
        """
        self._interpreter: Optional[object] = None
        self._label_map: dict[int, str] = {}

        self._load_model(model_path)
        self._load_labels(labels_path)

    def _load_model(self, model_path: str) -> None:
        """Load the TFLite model interpreter."""
        path = Path(model_path)
        if not path.exists():
            raise FileNotFoundError(f"Model file not found: {path.absolute()}")

        try:
            # Try ai_edge_litert first (the modern replacement for tflite_runtime)
            from ai_edge_litert.interpreter import Interpreter
        except ImportError:
            try:
                # Try tflite_runtime (older lightweight)
                from tflite_runtime.interpreter import Interpreter
            except ImportError:
                # Fall back to full TensorFlow
                logger.warning("tflite_runtime not found, falling back to tensorflow.lite")
                from tensorflow.lite.python.interpreter import Interpreter

        self._interpreter = Interpreter(model_path=str(path))
        self._interpreter.allocate_tensors()

        self._input_details = self._interpreter.get_input_details()
        self._output_details = self._interpreter.get_output_details()

        logger.info(
            "Model loaded: %s (input shape: %s)",
            path.name,
            self._input_details[0]["shape"],
        )

    def _load_labels(self, labels_path: str) -> None:
        """Load the label map from JSON."""
        path = Path(labels_path)
        if not path.exists():
            raise FileNotFoundError(f"Labels file not found: {path.absolute()}")

        with open(path, "r") as f:
            raw = json.load(f)
            self._label_map = {int(k): v for k, v in raw.items()}

        logger.info("Labels loaded: %d classes", len(self._label_map))

    def predict(self, features: np.ndarray) -> tuple[str, float]:
        """Classify a hand landmark feature vector.

        Args:
            features: 1D numpy array of 84 normalised landmark features.

        Returns:
            Tuple of (predicted_character, confidence_percentage).
        """
        if self._interpreter is None:
            raise RuntimeError("Model not loaded")

        # Reshape and set correct dtype for TFLite input
        input_data = features.reshape(1, -1).astype(np.float32)
        self._interpreter.set_tensor(self._input_details[0]["index"], input_data)
        self._interpreter.invoke()

        output = self._interpreter.get_tensor(self._output_details[0]["index"])[0]

        class_index = int(np.argmax(output))
        confidence = float(np.max(output)) * 100.0

        predicted_char = self._label_map.get(class_index, "?")

        return predicted_char, confidence

    @property
    def num_classes(self) -> int:
        """Return the number of classes in the label map."""
        return len(self._label_map)
