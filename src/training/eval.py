import os
from pathlib import Path
import pandas as pd
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
)
from src.utils import ensure_dir, load_model, logging

ROOT = Path(__file__).resolve().parents[2]

model_path = os.path.join(ROOT, "models", "xgboost_best.pkl")
features_test_path = os.path.join(ROOT, "data", "features_train_test", "test.csv")
result_path = os.path.join(ROOT, "results")

def compute_fpr(cm):
    tn, fp, fn, tp = cm.ravel()
    fpr = fp / (fp + tn) if (fp + tn) != 0 else 0.0
    return fpr

def evaluate():
    ensure_dir(result_path)

    model = load_model(model_path)
    logging.info("Model loaded successfully.")

    data = pd.read_csv(features_test_path)
    X_test = data.drop(columns=["label"])
    y_test = data["label"]

    y_pred = model.predict(X_test)      # X_test: đặc trưng → mô hình → y_pred: nhãn dự đoán

    # Confusion Matrix
    cm = confusion_matrix(y_test, y_pred)
    fpr= compute_fpr(cm)

    pd.DataFrame(
        cm,
        index=["Actual_0", "Actual_1"],
        columns=["Pred_0", "Pred_1"]
    ).to_csv(os.path.join(result_path, "confusion_matrix.csv"))

    # raw results
    raw_results = classification_report(y_test, y_pred, output_dict=True)
    pd.DataFrame(raw_results).transpose().to_csv(os.path.join(result_path, "raw_results.csv"), index=False)

    summary_results = {
        "Accuracy": raw_results["accuracy"],
        "Precision": raw_results["1"]["precision"],
        "Recall (TPR)": raw_results["1"]["recall"],
        "F1-score": raw_results["1"]["f1-score"],
        "FPR": fpr
    }

    pd.DataFrame([summary_results]).to_csv(os.path.join(result_path, "summary_results.csv"), index=False)

    print("----- Summary Results -----")
    for key, value in summary_results.items():
        print(f"{key}: {value:.4f}")

    logging.info("Evaluation finished successfully.")

if __name__ == "__main__":
    evaluate()
