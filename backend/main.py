from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import pickle
import pandas as pd
import os

app = FastAPI(title="Apex F1 Predictor API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load Model
MODEL_PATH = "model.pkl"
model_data = None
if os.path.exists(MODEL_PATH):
    with open(MODEL_PATH, "rb") as f:
        model_data = pickle.load(f)


class PredictRequest(BaseModel):
    grid: int
    team: str


@app.get("/")
def read_root():
    return {"message": "Welcome to the Apex F1 Predictor API"}


@app.get("/api/status")
def status():
    return {"status": "ok", "model_loaded": model_data is not None}


@app.post("/api/predict")
def predict(request: PredictRequest):
    if not model_data:
        raise HTTPException(status_code=500, detail="Model not loaded")

    model = model_data["model"]
    features = model_data["features"]

    # Create input dataframe
    input_data = pd.DataFrame([
        {"grid": request.grid, f"team_{request.team}": 1}
    ])

    # Fill missing team columns to match training features
    for col in features:
        if col not in input_data.columns:
            input_data[col] = 0

    # Ensure column order matches
    input_data = input_data[features]

    # Predict and probabilities
    prediction = model.predict(input_data)

    # Calculate probabilities
    proba = model.predict_proba(input_data)[0]
    classes = model.classes_
    prob_list = []
    for cls, prob in zip(classes, proba):
        prob_list.append({"position": int(cls), "probability": float(prob)})

    # Sort and take top 5
    prob_list.sort(key=lambda x: x["probability"], reverse=True)
    top_5 = prob_list[:5]

    return {"predicted_position": int(prediction[0]), "probabilities": top_5}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
