"""Loads/reloads the pickled prediction model. Kept separate from main.py so
the Phase 2 retrain pipeline can call reload_model() after writing a new
model.pkl without restarting the server process.
"""
import os
import pickle
import threading

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BACKEND_DIR, "model.pkl")

_lock = threading.Lock()
_model_data = None
_loaded_once = False


def load_model():
    global _model_data, _loaded_once
    with _lock:
        if os.path.exists(MODEL_PATH):
            with open(MODEL_PATH, "rb") as f:
                _model_data = pickle.load(f)
        else:
            _model_data = None
        _loaded_once = True
    return _model_data


def get_model():
    if not _loaded_once:
        load_model()
    return _model_data


def reload_model():
    return load_model()
