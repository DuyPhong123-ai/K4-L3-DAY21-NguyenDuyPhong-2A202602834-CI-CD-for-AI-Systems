import json
from pathlib import Path
from unittest.mock import Mock

import pytest
from src.publish_model import publish_model


def test_publishes_approved_artifacts(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "outputs").mkdir()
    (tmp_path / "models").mkdir()
    (tmp_path / "outputs/report.json").write_text(json.dumps({"f1_score": 0.7149}))
    (tmp_path / "models/model.joblib").write_bytes(b"test model")
    s3 = Mock()
    monkeypatch.setattr("src.publish_model.boto3.client", Mock(return_value=s3))
    publish_model("lab-bucket")
    assert s3.upload_file.call_count == 2
    s3.upload_file.assert_any_call(str(Path("models/model.joblib")), "lab-bucket", "artifacts/current/model.joblib")
    s3.upload_file.assert_any_call(str(Path("outputs/report.json")), "lab-bucket", "artifacts/current/report.json")


def test_rejects_model_before_s3_upload(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "outputs").mkdir()
    (tmp_path / "outputs/report.json").write_text(json.dumps({"f1_score": 0.60}))
    factory = Mock()
    monkeypatch.setattr("src.publish_model.boto3.client", factory)
    with pytest.raises(ValueError):
        publish_model("lab-bucket")
    factory.assert_not_called()
