"""Train Adult income classification and record MLflow runs."""
import json
import os
from pathlib import Path

import joblib
import mlflow
import mlflow.sklearn
import pandas as pd
import yaml
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import accuracy_score, f1_score

F1_THRESHOLD = 0.65
FEATURE_NAMES = [
    "age", "workclass", "education_num", "marital_status", "occupation",
    "relationship", "sex", "capital_gain", "capital_loss", "hours_per_week",
]


def train(params: dict, data_path: str = "data/train_batch1.csv",
          eval_path: str = "data/holdout.csv") -> float:
    """Return positive-class F1 on holdout; save metrics and fitted model."""
    df_train = pd.read_csv(data_path)
    df_eval = pd.read_csv(eval_path)
    X_train, y_train = df_train[FEATURE_NAMES], df_train["target"]
    X_eval, y_eval = df_eval[FEATURE_NAMES], df_eval["target"]
    mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "sqlite:///mlflow.db"))
    experiment_name = os.getenv("MLFLOW_EXPERIMENT_NAME", "adult-income")
    if mlflow.get_experiment_by_name(experiment_name) is None:
        artifact_root = Path(os.getenv("MLFLOW_ARTIFACT_ROOT", "mlartifacts")).resolve()
        mlflow.create_experiment(experiment_name, artifact_location=artifact_root.as_uri())
    mlflow.set_experiment(experiment_name)
    with mlflow.start_run() as run:
        mlflow.log_params(params)
        mlflow.log_param("random_state", 42)
        mlflow.set_tags({"train_rows": len(df_train), "eval_rows": len(df_eval)})
        model = GradientBoostingClassifier(**params, random_state=42)
        model.fit(X_train, y_train)
        preds = model.predict(X_eval)
        f1 = float(f1_score(y_eval, preds, zero_division=0))
        acc = float(accuracy_score(y_eval, preds))
        mlflow.log_metrics({"f1_score": f1, "accuracy": acc})
        mlflow.sklearn.log_model(model, "model")
        Path("outputs").mkdir(exist_ok=True)
        Path("models").mkdir(exist_ok=True)
        report = {"f1_score": f1, "accuracy": acc, "params": params,
                  "train_rows": len(df_train), "eval_rows": len(df_eval),
                  "run_id": run.info.run_id}
        Path("outputs/report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        joblib.dump(model, "models/model.joblib")
        mlflow.log_artifact("outputs/report.json")
        print(f"F1: {f1:.4f} | Accuracy: {acc:.4f}")
    return f1


if __name__ == "__main__":
    with open("params.yaml", encoding="utf-8") as f:
        train(yaml.safe_load(f))
