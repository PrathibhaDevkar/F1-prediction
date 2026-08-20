import json
import os

import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services import fastf1_service, model_service, prediction_service

router = APIRouter(prefix="/api", tags=["predictions"])

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NEXT_RACE_CACHE_PATH = os.path.join(BACKEND_DIR, "cache", "next_race_prediction.json")


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
        model_data["model"],
        model_data["features"],
        request.grid,
        request.team,
        request.driver,
        request.circuit,
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

    forecast = None
    last_updated = None
    if os.path.exists(NEXT_RACE_CACHE_PATH):
        try:
            with open(NEXT_RACE_CACHE_PATH) as f:
                cache = json.load(f)
            if cache.get("round") == event_payload["round"]:
                forecast = cache.get("forecast")
                last_updated = cache.get("generatedAt")
        except Exception:
            pass

    return {"event": event_payload, "forecast": forecast, "lastUpdated": last_updated}
