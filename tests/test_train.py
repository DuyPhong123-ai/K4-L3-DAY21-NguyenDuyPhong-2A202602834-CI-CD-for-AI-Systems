import json
import joblib
import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import accuracy_score, f1_score
from src.train import FEATURE_NAMES, train


def _make_temp_data(tmp_path):
    rng = np.random.default_rng(0)
    df = pd.DataFrame(rng.random((200, len(FEATURE_NAMES))), columns=FEATURE_NAMES)
    df["target"] = rng.integers(0, 2, size=200)
    train_path, eval_path = tmp_path / "train.csv", tmp_path / "holdout.csv"
    df.iloc[:160].to_csv(train_path, index=False)
    df.iloc[160:].to_csv(eval_path, index=False)
    return str(train_path), str(eval_path)


@pytest.fixture
def trained(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MLFLOW_TRACKING_URI", "sqlite:///mlflow.db")
    monkeypatch.setenv("MLFLOW_EXPERIMENT_NAME", "unit-tests")
    monkeypatch.setenv("MLFLOW_ARTIFACT_ROOT", str(tmp_path / "mlartifacts"))
    train_path, eval_path = _make_temp_data(tmp_path)
    f1 = train({"n_estimators": 10, "learning_rate": 0.1, "max_depth": 2}, train_path, eval_path)
    return f1, pd.read_csv(eval_path)


def test_train_returns_float(trained):
    f1, _ = trained
    assert isinstance(f1, float)
    assert 0 <= f1 <= 1


def test_report_file_created(trained):
    f1, holdout = trained
    with open("outputs/report.json", encoding="utf-8") as f:
        report = json.load(f)
    model = joblib.load("models/model.joblib")
    preds = model.predict(holdout[FEATURE_NAMES])
    assert report["f1_score"] == f1 == f1_score(holdout.target, preds)
    assert report["accuracy"] == accuracy_score(holdout.target, preds)
    assert report["train_rows"] == 160
    assert report["eval_rows"] == 40


def test_model_file_created(trained):
    _, holdout = trained
    model = joblib.load("models/model.joblib")
    assert list(model.feature_names_in_) == FEATURE_NAMES
    assert set(model.predict(holdout[FEATURE_NAMES])) <= {0, 1}
