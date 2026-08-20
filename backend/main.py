import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import drivers, predictions, schedule
from services import model_service

app = FastAPI(title="Apex F1 Predictor API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(schedule.router)
app.include_router(drivers.router)
app.include_router(predictions.router)

model_service.load_model()


@app.get("/")
def read_root():
    return {"message": "Welcome to the Apex F1 Predictor API"}


@app.get("/api/status")
def status():
    return {"status": "ok", "model_loaded": model_service.get_model() is not None}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
