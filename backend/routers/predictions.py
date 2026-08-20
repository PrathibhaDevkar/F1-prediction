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
