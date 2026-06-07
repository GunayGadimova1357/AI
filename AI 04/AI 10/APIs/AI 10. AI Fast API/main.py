import traceback

import joblib
import pandas as pd
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, r2_score, root_mean_squared_error
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from xgboost import XGBRegressor

app = FastAPI(title="Price Prediction AI Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parents[2]
MODEL_PATH = BASE_DIR / "models" / "model_az.pkl"
DATA_PATH = BASE_DIR / "data" / "housing_az_sqm_azn.csv"
FEATURES = ["Bedrooms", "Bathrooms", "Sqm", "City"]
BUNDLE = None
PIPELINE = None


def load_model():
    global BUNDLE, PIPELINE, FEATURES
    loaded = joblib.load(MODEL_PATH)
    if not isinstance(loaded, dict) or "pipeline" not in loaded:
        raise ValueError("Model file has unexpected format")
    BUNDLE = loaded
    PIPELINE = BUNDLE["pipeline"]
    FEATURES = BUNDLE.get("featured_order", FEATURES)
    print(f"Model loaded successfully {MODEL_PATH}")


def train_model():
    df = pd.read_csv(DATA_PATH)
    y = df["PriceAZN"].astype(float)
    x = df[FEATURES]

    numeric_transformer = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler())
    ])

    categorical_transformer = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False))
    ])

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, ["Bedrooms", "Bathrooms", "Sqm"]),
            ("cat", categorical_transformer, ["City"])
        ]
    )

    pipe = Pipeline(steps=[
        ("prep", preprocessor),
        ("model", XGBRegressor(
            n_estimators=300,
            learning_rate=0.05,
            max_depth=4,
            random_state=42,
            n_jobs=-1
        ))
    ])

    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=0.2, random_state=42
    )
    pipe.fit(x_train, y_train)
    predictions = pipe.predict(x_test)

    bundle = {
        "pipeline": pipe,
        "featured_order": FEATURES,
    }
    joblib.dump(bundle, MODEL_PATH)
    load_model()

    return {
        "rows": int(len(df)),
        "mae": float(mean_absolute_error(y_test, predictions)),
        "rmse": float(root_mean_squared_error(y_test, predictions)),
        "r2": float(r2_score(y_test, predictions)),
    }


try:
    load_model()
except Exception as e:
    print(f"Error loading model: {e}")
    traceback.print_exc()

class PredictIn(BaseModel):
    bedrooms: float
    bathrooms: float
    sqm: float
    city: str


class ApartmentIn(PredictIn):
    priceAZN: float


@app.post("/predict")
async def predict(request: PredictIn):
    print(PIPELINE)
    if PIPELINE is None:
        raise HTTPException(status_code=503, detail="No model loaded")
    try:
        features = {
            "Bedrooms": [request.bedrooms],
            "Bathrooms": [request.bathrooms],
            "City": [request.city]
        }
        if "Sqm" in FEATURES:
            features["Sqm"] = [request.sqm]
        features_df = pd.DataFrame(features, columns=FEATURES)
        prediction = PIPELINE.predict(features_df)[0]
        return {"priceAZN": float(prediction)}
    except Exception as e:
        print(f"Error predicting price: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error predicting price: {e}")


@app.post("/apartments")
async def add_apartment(request: ApartmentIn):
    try:
        new_row = pd.DataFrame([{
            "PriceAZN": request.priceAZN,
            "Bedrooms": request.bedrooms,
            "Bathrooms": request.bathrooms,
            "Sqm": request.sqm,
            "City": request.city,
        }])
        new_row.to_csv(DATA_PATH, mode="a", header=False, index=False)
        metrics = train_model()
        return {
            "message": "Apartment added and model retrained",
            "metrics": metrics,
        }
    except Exception as e:
        print(f"Error adding apartment: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error adding apartment: {e}")


@app.post("/retrain")
async def retrain():
    try:
        metrics = train_model()
        return {
            "message": "Model retrained",
            "metrics": metrics,
        }
    except Exception as e:
        print(f"Error retraining model: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error retraining model: {e}")
