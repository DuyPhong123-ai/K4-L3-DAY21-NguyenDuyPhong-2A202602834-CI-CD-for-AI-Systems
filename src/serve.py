"""Serve an S3 model, or MODEL_PATH for local verification."""
from contextlib import asynccontextmanager
import math
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
import boto3
import joblib
import pandas as pd
from pydantic import BaseModel

FEATURE_NAMES = [
    "age", "workclass", "education_num", "marital_status", "occupation",
    "relationship", "sex", "capital_gain", "capital_loss", "hours_per_week",
]
MODEL_KEY = "artifacts/current/model.joblib"


def download_model() -> Path:
    model_path = Path(os.getenv("MODEL_PATH", "~/models/model.joblib")).expanduser()
    bucket_name = os.getenv("ARTIFACT_BUCKET")
    if bucket_name:
        model_path.parent.mkdir(parents=True, exist_ok=True)
        boto3.client("s3").download_file(bucket_name, MODEL_KEY, str(model_path))
        print("Model downloaded from Amazon S3.")
    elif not os.getenv("MODEL_PATH"):
        raise RuntimeError("Set ARTIFACT_BUCKET for cloud or MODEL_PATH for local serving.")
    return model_path


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.model = joblib.load(download_model())
    yield
    del app.state.model


app = FastAPI(lifespan=lifespan)


class ScoreRequest(BaseModel):
    features: list[float]


@app.get("/healthz")
def healthz():
    if not hasattr(app.state, "model"):
        raise HTTPException(status_code=503, detail="Model is not loaded")
    return {"status": "ok"}


@app.post("/score")
def score(req: ScoreRequest):
    if len(req.features) != 10:
        raise HTTPException(status_code=400, detail="Expected 10 features (adult income)")
    if not all(math.isfinite(value) for value in req.features):
        raise HTTPException(status_code=400, detail="Features must be finite numbers")
    frame = pd.DataFrame([req.features], columns=FEATURE_NAMES)
    pred = int(app.state.model.predict(frame)[0])
    return {"prediction": pred, "label": "thu_nhap_cao" if pred == 1 else "thu_nhap_thap"}


def main():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)


if __name__ == "__main__":
    main()
