import joblib
import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from sklearn.ensemble import GradientBoostingClassifier
from src.serve import FEATURE_NAMES, app, download_model, MODEL_KEY


@pytest.fixture
def client(tmp_path, monkeypatch):
    frame = pd.DataFrame(np.random.default_rng(42).random((40, 10)), columns=FEATURE_NAMES)
    model = GradientBoostingClassifier(n_estimators=5, random_state=42).fit(frame, [0, 1] * 20)
    model_path = tmp_path / "model.joblib"
    joblib.dump(model, model_path)
    monkeypatch.delenv("ARTIFACT_BUCKET", raising=False)
    monkeypatch.setenv("MODEL_PATH", str(model_path))
    with TestClient(app) as test_client:
        yield test_client, model


def test_healthz(client):
    response = client[0].get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_score_matches_model(client):
    features = [28, 2, 14, 2, 11, 0, 1, 0, 0, 45]
    response = client[0].post("/score", json={"features": features})
    expected = int(client[1].predict(pd.DataFrame([features], columns=FEATURE_NAMES))[0])
    assert response.status_code == 200
    assert response.json() == {"prediction": expected,
                               "label": "thu_nhap_cao" if expected else "thu_nhap_thap"}


def test_score_rejects_wrong_length(client):
    assert client[0].post("/score", json={"features": [1, 2]}).status_code == 400


def test_score_rejects_non_numeric_input(client):
    assert client[0].post("/score", json={"features": ["invalid"] * 10}).status_code == 422


def test_download_model_from_s3(tmp_path, monkeypatch):
    from unittest.mock import Mock
    s3 = Mock()
    factory = Mock(return_value=s3)
    monkeypatch.setattr("src.serve.boto3.client", factory)
    path = tmp_path / "models" / "model.joblib"
    monkeypatch.setenv("ARTIFACT_BUCKET", "lab-bucket")
    monkeypatch.setenv("MODEL_PATH", str(path))
    assert download_model() == path
    assert path.parent.is_dir()
    factory.assert_called_once_with("s3")
    s3.download_file.assert_called_once_with("lab-bucket", MODEL_KEY, str(path))
