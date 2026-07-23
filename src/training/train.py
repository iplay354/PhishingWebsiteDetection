import os
from pathlib import Path
import pandas as pd
from sklearn.model_selection import train_test_split, GridSearchCV, StratifiedKFold
from xgboost import XGBClassifier
from src.utils import ensure_dir, save_model, logging

ROOT = Path(__file__).resolve().parents[2]

def data_in(hybrid_features_csv=None, path_save_train_test=None, test_size=0.2):
    hybrid_features_csv = hybrid_features_csv or os.path.join(ROOT, "data", "features_full", "hybrid_features_full.csv")

    data = pd.read_csv(hybrid_features_csv)

    X = data.drop(columns=["label"])
    y = data["label"]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=test_size,                          #train 80, test 20
        stratify=y,
        random_state=99                   # 80 train ban đâu, sau vẫn phải là 80 train đó
    )

    path_save_train_test = path_save_train_test or os.path.join(ROOT, "data", "features_train_test")
    ensure_dir(path_save_train_test)

    pd.concat([X_train, y_train], axis=1).to_csv(os.path.join(path_save_train_test, "train.csv"), index=False)
    pd.concat([X_test, y_test], axis=1).to_csv(os.path.join(path_save_train_test, "test.csv"), index=False)

    logging.info("Train/Test datasets saved successfully.")

    return X_train, X_test, y_train, y_test

def train_xgboost(X_train, y_train):
    param_grid = {
        "n_estimators": [100, 200],
        "max_depth": [3, 5, 7],
        "learning_rate": [0.05, 0.1],
        "subsample": [0.8, 1.0],
        "colsample_bytree": [0.8, 1.0],
    }

    xgb = XGBClassifier(
        objective="binary:logistic",
        eval_metric="logloss",
        random_state=99,
        n_jobs=8,                                              # 8 core laptop
        use_label_encoder=False,
    )

    cv = StratifiedKFold(
        n_splits=5,
        shuffle=True,
        random_state=99
    )

    grid = GridSearchCV(
        estimator=xgb,
        param_grid=param_grid,
        cv=cv,
        n_jobs=8,
        verbose=1
    )

    grid.fit(X_train, y_train)

    logging.info(f"Best parameters: {grid.best_params_}")

    return grid.best_estimator_, grid

def main():
    # data
    X_train, X_test, y_train, y_test = data_in()

    # Train model
    model, grid = train_xgboost(X_train, y_train)

    # Save model
    ensure_dir(os.path.join(ROOT, "models"))
    save_model(model, os.path.join(ROOT, "models", "xgboost_best.pkl"))

    # Save results
    ensure_dir(os.path.join(ROOT, "results"))

    pd.DataFrame(grid.cv_results_).to_csv(os.path.join(ROOT, "results", "grid_results.csv"),index=False)

    logging.info("Training finished successfully.")

if __name__ == "__main__":
    main()


