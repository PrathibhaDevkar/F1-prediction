import fastf1
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import pickle
import os

# Enable fastf1 cache
os.makedirs("cache", exist_ok=True)
fastf1.Cache.enable_cache("cache")


def fetch_and_prepare_data():
    dataset = []
    # Fetch data for a few races to build a quick model
    # Doing 2023 races 1 to 5 for speed
    print("Fetching historical F1 data...")
    for round_number in range(1, 6):
        try:
            print(f"Loading 2023 Round {round_number}...")
            session = fastf1.get_session(2023, round_number, "R")
            session.load(telemetry=False, weather=False, messages=False)
            results = session.results
            for idx, driver in results.iterrows():
                grid = driver["GridPosition"]
                finish = driver["Position"]
                team = driver["TeamName"]
                dataset.append({"grid": grid, "finish": finish, "team": team})
        except Exception as e:
            print(f"Skipping round {round_number} due to error: {e}")

    df = pd.DataFrame(dataset)
    df["finish"] = pd.to_numeric(df["finish"], errors="coerce")
    df.dropna(subset=["finish", "grid"], inplace=True)
    return df


def train_model():
    df = fetch_and_prepare_data()
    if df.empty:
        print("Error: No data fetched.")
        return

    print(f"Dataset compiled with {len(df)} records.")

    # Advanced: One-hot encode the teams
    df = pd.get_dummies(df, columns=["team"])

    # Prepare features and target
    y = df["finish"]
    X = df.drop("finish", axis=1)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    print("Training Random Forest...")
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    acc = accuracy_score(y_test, preds)
    print(f"Model accuracy: {acc * 100:.2f}%")

    # Save model and the feature columns for later inference
    model_data = {"model": model, "features": X.columns.tolist()}

    with open("model.pkl", "wb") as f:
        pickle.dump(model_data, f)
    print("Model and feature references saved to model.pkl")


if __name__ == "__main__":
    train_model()
