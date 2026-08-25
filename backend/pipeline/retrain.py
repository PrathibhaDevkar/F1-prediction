"""The autonomous ('agentic') pipeline: detects newly completed races and
retrains + refreshes the next-race forecast on its own — no manual script
running required. Runs as a plain sync function so APScheduler's
AsyncIOExecutor offloads it to a thread instead of blocking the event loop
(retraining can take minutes on a cold FastF1 cache).
"""
from datetime import datetime, timezone

import db
import model_trainer
from services import fastf1_service


def check_and_process_new_results():
    db.set_state("last_run_at", datetime.now(timezone.utc).isoformat())

    completed = fastf1_service.get_completed_events()
    if not completed:
        db.set_state("last_run_status", "no_data")
        print("[pipeline] No completed races found.")
        return {"status": "no_data"}

    latest_round = int(completed[-1]["RoundNumber"])
    last_processed_raw = db.get_state("last_processed_round")
    last_processed_round = int(last_processed_raw) if last_processed_raw else 0

    if latest_round <= last_processed_round:
        db.set_state("last_run_status", "no_new_race")
        print(f"[pipeline] No new race since round {last_processed_round}.")
        return {"status": "no_new_race", "latest_round": latest_round}

    print(f"[pipeline] New race detected: round {latest_round} "
          f"(previously processed: {last_processed_round}). Retraining...")

    model_data, next_race = model_trainer.train_and_save()
    if model_data is None:
        db.set_state("last_run_status", "retrain_failed")
        print("[pipeline] Retrain failed: no data fetched.")
        return {"status": "retrain_failed"}

    db.set_state("last_processed_round", latest_round)
    db.set_state("last_run_status", "ok")
    db.set_state("model_trained_at", datetime.now(timezone.utc).isoformat())
    model_trainer.write_seed_state(next_race)
    print(f"[pipeline] Retrain complete. last_processed_round={latest_round}.")
    return {"status": "ok", "latest_round": latest_round}
