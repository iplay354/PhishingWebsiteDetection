import os
from pathlib import Path
from src.inference.feature_pipeline import build_feature_vector
from src.utils import load_model

ROOT = Path(__file__).resolve().parents[2]
MODEL = os.path.join(ROOT, "models", "xgboost_best.pkl")


class PhishingPredictor:
    def __init__(self):
        self.model = load_model(MODEL)

    def predict(self, url):
        X = build_feature_vector(url)

        prob = self.model.predict_proba(X)[0, 1]
        label = int(prob >= 0.5)

        return {
            "url": url,
            "label": label,
            "probability": float(prob),
            "result": "Phishing" if label == 1 else "Legitimate"
        }