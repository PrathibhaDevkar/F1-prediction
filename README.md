# Apex F1 Predictor 2026

Apex F1 Predictor is a modern web application designed to forecast Formula 1 race finishes for the 2026 season. It utilizes machine learning models trained on historical F1 data to estimate finishing positions based on starting grid order and constructor.

## Key Features

- **2026 Season Calendar**: Interactive dashboard showcasing the comprehensive 24-race 2026 F1 calendar.
- **Lap View Modal**: Click on completed races to view dynamic race statistics, points, and lap-by-lap information (powered by FastF1).
- **Prediction Engine**: Enter your starting grid position and constructor to get AI-powered outcomes.
- **Top 5 Probability Metrics**: Displays calculated likelihoods for the top five fastest and most accurate position forecasts.

## Technologies Used

### Frontend
- **React.js & Vite**: For lightning-fast UI compilation and a component-based architecture.
- **CSS3 with Glassmorphism**: Provides an aggressive and modern "Speed" aesthetic tailored for the pinnacle of motorsport.

### Backend
- **FastAPI**: Delivering high-performance async API endpoints.
- **uvicorn**: ASGI server for running the FastAPI backend.
- **FastF1**: The backbone for querying historical F1 data directly from official archives.
- **pandas**: Used for dataset manipulation and robust data cleaning.
- **scikit-learn (RandomForestClassifier)**: Serves as the core machine-learning predictive model.
- **pickle**: Serializes and deserializes the ML model to eliminate training overhead on startup.

## Future Enhancements

The next major phases of Apex F1 aim to broaden analytical capabilities and visual features:

- **Live Weather Integration**: Inject real-time weather forecasts (rain probabilities, track temperatures) directly into the prediction model to account for dynamic variables.
- **Real-Time Telemetry Streaming**: Visualizing live speed, gear, and throttle inputs during active race weekends via websockets.
- **Advanced Machine Learning Models**: Migrating to more complex algorithms such as XGBoost or neural networks, and increasing the training dataset depth by expanding parameters (e.g. driver-specific statistics, pit stop averages, and circuit-specific track limits). 
- **Head-to-Head Driver Comparisons**: In-depth analytics comparing teammates directly to understand the delta factor on specific circuits.

## How to run locally

### Backend Setup
1. Navigate into the `backend` folder.
2. Initialize virtual environment: `python -m venv venv` and activate it.
3. Install dependencies: `pip install -r requirements.txt`
4. Re-train the model if needed: `python model_trainer.py`
5. Run the FastAPI development server: `python main.py`

### Frontend Setup
1. Navigate to the `frontend` folder.
2. Install Node packages: `npm install`
3. Spin up the Vite server: `npm run dev`
