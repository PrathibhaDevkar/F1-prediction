from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import db
from pipeline.scheduler import start_scheduler, stop_scheduler
from routers import drivers, predictions, schedule
from services import model_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    model_service.load_model()
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(title="Apex F1 Predictor API", lifespan=lifespan)

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


@app.get("/")
def read_root():
    return {"message": "Welcome to the Apex F1 Predictor API"}


@app.get("/api/status")
def status():
    return {
        "status": "ok",
        "model_loaded": model_service.get_model() is not None,
        "last_pipeline_run": db.get_state("last_run_at"),
        "last_run_status": db.get_state("last_run_status"),
        "last_processed_round": db.get_state("last_processed_round"),
        "model_trained_at": db.get_state("model_trained_at"),
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
