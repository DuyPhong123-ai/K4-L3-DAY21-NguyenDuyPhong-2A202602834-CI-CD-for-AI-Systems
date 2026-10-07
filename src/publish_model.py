"""Publish the approved model and its report to Amazon S3."""
import json
import os
from pathlib import Path
import sys

import boto3
from botocore.exceptions import ClientError

from src.quality_gate import check_quality


def publish_model(bucket: str) -> None:
    report_path = Path("outputs/report.json")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    check_quality(float(report["f1_score"]))
    model_path = Path("models/model.joblib")
    if not model_path.is_file():
        raise FileNotFoundError(model_path)
    s3 = boto3.client("s3")
    s3.upload_file(str(model_path), bucket, "artifacts/current/model.joblib")
    s3.upload_file(str(report_path), bucket, "artifacts/current/report.json")
    print(f"Published approved model to s3://{bucket}/artifacts/current/")


def main() -> int:
    try:
        publish_model(os.environ["ARTIFACT_BUCKET"])
        return 0
    except (ClientError, ValueError, OSError, KeyError) as exc:
        print(f"Publish failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
