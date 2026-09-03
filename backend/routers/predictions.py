import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import db
from services import fastf1_service, model_service, prediction_service

router = APIRouter(prefix="/api", tags=["predictions"])


class PredictRequest(BaseModel):
    grid: int
    team: str
    driver: str | None = None
    circuit: str | None = None


@router.post("/predict")
def predict(request: PredictRequest):
    model_data = model_service.get_model()
    if not model_data:
        raise HTTPException(status_code=500, detail="Model not loaded")

    return prediction_service.build_prediction(
        model_data,
        request.grid,
        request.team,
        request.driver,
        request.circuit,
        driver_form=model_data.get("driver_form"),
        team_form=model_data.get("team_form"),
    )


@router.get("/next-race")
def next_race():
    event = fastf1_service.get_next_event()
    if event is None:
        return {"event": None, "forecast": None, "lastUpdated": None}

    race_time = fastf1_service.race_session_time(pd.Series(event))
    event_payload = {
        "round": int(event["RoundNumber"]),
        "name": event["EventName"],
        "country": event["Country"],
        "location": event["Location"],
        "date": race_time.isoformat() if race_time else None,
    }

    round_key = str(event_payload["round"])
    cached = db.get_cached_prediction(round_key)
    forecast = cached["forecast"] if cached else None
    last_updated = cached["generatedAt"] if cached else None

    return {"event": event_payload, "forecast": forecast, "lastUpdated": last_updated}


@router.get("/accuracy")
def accuracy():
    """Held-out test-set performance: the model never saw these races
    during training, so this is a real (if retrospective) measure of how
    good the predictions actually are — not just an AUC number, but the
    real per-race predicted-vs-actual rows behind it."""
    metrics = db.get_model_metrics()
    if metrics is None:
        return {"metrics": None, "testPredictions": []}
    return {"metrics": metrics, "testPredictions": db.get_model_test_predictions()}


@router.get("/track-record")
def track_record():
    """Real forecasts made before each race happened, reconciled against
    what actually happened once it did — builds up over time as new races
    complete, unlike /api/accuracy which is a fixed historical sample."""
    return {"records": db.get_track_record()}
