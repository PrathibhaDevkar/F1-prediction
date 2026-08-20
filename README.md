# Apex F1 Predictor

Apex F1 Predictor forecasts Formula 1 race finishes using a model trained on real historical race data, kept up to date automatically as new races complete — plus a live telemetry view for whenever a session is actually running.

## Key Features

- **Real season calendar & results**: The calendar, driver/team lineup, and race results (winner, podium, laps) all come from [FastF1](https://github.com/theOehrly/Fast-F1), not hardcoded data.
- **Next Race Prediction**: A full-grid forecast for the next upcoming race, generated automatically by the training pipeline — separate from the manual what-if form below.
- **Prediction Engine**: Enter a grid position, team, and optionally a driver/circuit, to get a model-predicted finishing position with top-5 probabilities.
- **Live Telemetry**: Real-time speed/gear/throttle/brake/DRS per driver via [OpenF1](https://openf1.org) while an F1 session is actually in progress — shows a clear "no session live" state the rest of the time (which is most of the time; sessions run a few hours every couple of weeks).
- **Autonomous retrain pipeline**: A scheduler checks for newly completed races and retrains the model + refreshes the next-race forecast on its own — no manual script running required.

## Architecture

### Backend (`backend/`)
- **FastAPI** app (`main.py`), split into `routers/` (schedule, drivers, predictions, live) and `services/` (FastF1 access, model loading, prediction logic, live telemetry polling).
- **`model_trainer.py`**: trains a `RandomForestClassifier` on grid position, team, driver, and circuit, using every completed race from 2023 through the current point in the season. Callable directly or via the pipeline.
- **`pipeline/`**: an APScheduler job embedded in the app's lifespan, checking every 45 minutes (+ once on startup) for a newly completed race. When found, it retrains and refreshes the next-race forecast in-process — the running server picks up the new model without a restart.
- **`db.py`**: SQLite (no ORM) for pipeline state (last processed round, run status/timestamps) and the cached next-race forecast — survives restarts.
- **`services/live_timing.py`**: polls OpenF1's REST API for real-time car telemetry while a session is live, fanned out over a WebSocket (`/ws/live-timing`). Chosen over FastF1's own live-timing feature because that requires an F1TV subscription plus an interactive browser login; OpenF1 is a plain REST API with a simpler API-key model.

### Frontend (`frontend/`)
- **React + Vite**, fetching all of the above from the backend instead of hardcoded/random data.
- **recharts** for the live telemetry speed trace.

## How to run locally

### Backend Setup
1. `cd backend`, create/activate a virtualenv, `pip install -r requirements.txt`.
2. Optionally create `.env` with `OPENF1_API_KEY=` (get one from [openf1.org](https://openf1.org) — historical data works fine without it; a key is only needed for the real-time telemetry tier).
3. Train the model once: `python model_trainer.py` (fetches real historical data — can take a while on a cold cache).
4. Run the server: `python main.py` (or `uvicorn main:app --reload`). The scheduler and live-telemetry poller start automatically.

### Frontend Setup
1. `cd frontend`, `npm install`, `npm run dev`.

## Known limitations

- **Model accuracy is modest** (~12% exact match, but within 3 positions ~59% of the time, MAE ~4 positions on held-out data). Features now include rolling driver/team form and DNF rate on top of grid/team/driver/circuit, but there's still no weather or qualifying-pace signal. See "Future Enhancements" below.
- **Next-race grid is assumed**, not real — actual grid positions aren't known until qualifying finishes, so the forecast uses each driver's most recent race grid as a stand-in.
- **Live telemetry only works during an actual session window**, and OpenF1's real-time tier requires a paid API key; outside that, the UI correctly shows a "no session live" state rather than anything live.

## Future Enhancements

- **Live Weather Integration**: feed real-time weather (rain probability, track temp) into the model.
- **More features**: qualifying pace, pit-stop averages.
- **Try other algorithms**: XGBoost, gradient boosting variants.
- **Head-to-Head Driver Comparisons**: teammate-vs-teammate analytics per circuit.
- **Qualifying-triggered forecast refresh**: re-run the next-race forecast once qualifying completes, so "assumed grid" becomes real.
