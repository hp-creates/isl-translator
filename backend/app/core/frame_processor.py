"""Frame processor — decodes base64 frames and extracts hand landmarks.

Uses MediaPipe Hands to detect hand landmarks in video frames and
normalises them into a feature vector suitable for the sign classifier.
"""

from __future__ import annotations

import base64
from typing import Optional

import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np

from app.utils.logging import get_logger

logger = get_logger("frame_processor")

# Constants matching the training configuration
NUM_HANDS = 2
FEATURES_PER_HAND = 42  # 21 landmarks × 2 coordinates (x, y)
TOTAL_FEATURES = NUM_HANDS * FEATURES_PER_HAND  # 84


class FrameProcessor:
    """Processes video frames to extract normalised hand landmark features.

    Initialises a MediaPipe Hands instance and provides methods to:
    1. Decode base64 JPEG frames
    2. Detect hands and extract landmarks
    3. Normalise landmarks into a fixed-size feature vector
    """

    def __init__(
        self,
        max_num_hands: int = NUM_HANDS,
        min_detection_confidence: float = 0.6,
        min_tracking_confidence: float = 0.5,
    ) -> None:
        # Create the base options pointing to the downloaded .task model file
        base_options = python.BaseOptions(model_asset_path='model/hand_landmarker.task')

        # Configure the vision task
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            num_hands=max_num_hands,
            min_hand_detection_confidence=min_detection_confidence,
            min_hand_presence_confidence=min_tracking_confidence,
        )

        # Initialize the landmarker
        self._landmarker = vision.HandLandmarker.create_from_options(options)
        logger.info(
            "FrameProcessor initialised (max_hands=%d, det_conf=%.2f)",
            max_num_hands,
            min_detection_confidence,
        )

    def process_frame(self, base64_data: str) -> Optional[tuple[np.ndarray, int]]:
        """Decode a base64 JPEG frame and extract hand landmark features.

        Args:
            base64_data: Base64-encoded JPEG image data.

        Returns:
            Tuple of (feature_vector, num_hands_detected) or None if decoding
            fails or no hands are detected with sufficient landmarks.
        """
        # Decode base64 → raw bytes → numpy array → BGR image
        try:
            img_bytes = base64.b64decode(base64_data)
            img_array = np.frombuffer(img_bytes, dtype=np.uint8)
            frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            if frame is None:
                logger.warning("Failed to decode frame from base64 data")
                return None
        except Exception:
            logger.exception("Error decoding base64 frame")
            return None

        # Convert BGR → RGB and wrap in an mp.Image object
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=img_rgb)

        # Run inference
        detection_result = self._landmarker.detect(mp_image)

        # Extract and normalise landmarks
        all_features: list[float] = []
        num_hands_detected = 0

        if detection_result.hand_landmarks:
            num_hands_detected = len(detection_result.hand_landmarks)

            for hand_landmarks in detection_result.hand_landmarks:
                # hand_landmarks is now a list of NormalizedLandmark objects directly
                landmarks_raw = [
                    (lm.x, lm.y) for lm in hand_landmarks
                ]
                normalised = self._normalise_landmarks(landmarks_raw)
                all_features.extend(normalised)

            # Pad if fewer than expected hands detected
            if num_hands_detected < NUM_HANDS:
                padding_size = FEATURES_PER_HAND * (NUM_HANDS - num_hands_detected)
                all_features.extend([0.0] * padding_size)
        else:
            # No hands detected — return zero vector
            all_features = [0.0] * TOTAL_FEATURES

        if len(all_features) != TOTAL_FEATURES:
            logger.warning(
                "Feature vector size mismatch: expected %d, got %d",
                TOTAL_FEATURES,
                len(all_features),
            )
            return None

        return np.array(all_features, dtype=np.float32), num_hands_detected

    @staticmethod
    def _normalise_landmarks(landmarks_raw: list[tuple[float, float]]) -> list[float]:
        """Normalise hand landmarks relative to the wrist.

        This MUST be identical to the normalisation used during training.

        Args:
            landmarks_raw: List of 21 (x, y) landmark coordinates.

        Returns:
            Flat list of 42 normalised coordinates.
        """
        wrist_x, wrist_y = landmarks_raw[0]

        # Make coordinates relative to wrist
        landmarks_rel = [
            (x - wrist_x, y - wrist_y) for x, y in landmarks_raw
        ]

        # Scale to [-1, 1] range
        max_val = max(
            abs(coord) for point in landmarks_rel for coord in point
        )
        if max_val == 0:
            return [0.0] * FEATURES_PER_HAND

        landmarks_norm = [
            (x / max_val, y / max_val) for x, y in landmarks_rel
        ]

        # Flatten to 1D list
        return [coord for point in landmarks_norm for coord in point]

    def close(self) -> None:
        """Release MediaPipe resources."""
        self._landmarker.close()
        logger.info("FrameProcessor closed")
