"""Tests for the SignClassifier.

Note: These tests require the actual model and labels files to be present.
They are skipped if the files are not found (e.g., in CI without model artifacts).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from app.core.frame_processor import TOTAL_FEATURES

# Paths relative to backend directory
MODEL_PATH = Path("model/isl_model_2hand.tflite")
LABELS_PATH = Path("model/labels_2hand.json")

# Skip all tests if model files are not present
pytestmark = pytest.mark.skipif(
    not MODEL_PATH.exists() or not LABELS_PATH.exists(),
    reason="Model files not found — run scripts/convert_model.py first",
)


class TestSignClassifier:
    """Test suite for SignClassifier (requires model files)."""

    @pytest.fixture
    def classifier(self):
        """Load the classifier with actual model files."""
        from app.core.sign_classifier import SignClassifier

        return SignClassifier(
            model_path=str(MODEL_PATH),
            labels_path=str(LABELS_PATH),
        )

    def test_loads_successfully(self, classifier):
        """Classifier should load model and labels without errors."""
        assert classifier.num_classes == 35  # 9 digits + 26 letters

    def test_predict_returns_valid_output(self, classifier):
        """Predict should return a character and confidence score."""
        features = np.random.randn(TOTAL_FEATURES).astype(np.float32)
        char, confidence = classifier.predict(features)

        assert isinstance(char, str)
        assert len(char) == 1 or char.isdigit()
        assert 0.0 <= confidence <= 100.0

    def test_predict_zero_input(self, classifier):
        """Zero input should still return a valid prediction (no crash)."""
        features = np.zeros(TOTAL_FEATURES, dtype=np.float32)
        char, confidence = classifier.predict(features)

        assert isinstance(char, str)
        assert isinstance(confidence, float)

    def test_predict_consistent(self, classifier):
        """Same input should produce same output (deterministic)."""
        features = np.ones(TOTAL_FEATURES, dtype=np.float32) * 0.5
        char1, conf1 = classifier.predict(features)
        char2, conf2 = classifier.predict(features)

        assert char1 == char2
        assert conf1 == conf2
