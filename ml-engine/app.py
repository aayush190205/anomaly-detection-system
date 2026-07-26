# ============================================================
# Behaviour-Based Intrusion Detection System Backend
# Pure Machine Learning Architecture (LSTM + SHAP)
# ============================================================

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import logging
import traceback
import warnings
from collections import defaultdict, deque
from datetime import datetime
from typing import Dict, List, Any
import joblib
import numpy as np
import shap
from tensorflow.keras.models import load_model

warnings.filterwarnings("ignore")

# Logging Configuration
LOG_FORMAT = "%(asctime)s | %(levelname)s | %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger("BehaviourIDS")

# Flask Configuration
app = Flask(__name__)
CORS(app)
app.config["JSON_SORT_KEYS"] = False

# Paths
MODEL_DIR = "models"
MODEL_PATH = os.path.join(MODEL_DIR, "lstm_detector.keras")
SCALER_PATH = os.path.join(MODEL_DIR, "scaler.pkl")
ENCODER_PATH = os.path.join(MODEL_DIR, "encoders.pkl")
LABEL_ENCODER_PATH = os.path.join(MODEL_DIR, "label_encoder.pkl")
FEATURE_COLUMNS_PATH = os.path.join(MODEL_DIR, "feature_cols.pkl")
SEQUENCE_PATH = os.path.join(MODEL_DIR, "sequence_length.pkl")

# Load Model & Objects
logger.info("Loading trained model...")
try:
    model = load_model(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)
    encoders = joblib.load(ENCODER_PATH)
    label_encoder = joblib.load(LABEL_ENCODER_PATH)
    feature_cols = joblib.load(FEATURE_COLUMNS_PATH)
    SEQUENCE_LENGTH = joblib.load(SEQUENCE_PATH)
    logger.info("Model loaded successfully.")
except Exception as e:
    logger.exception("Model loading failed.")
    raise e

# Global Runtime Variables
entity_history = defaultdict(lambda: deque(maxlen=SEQUENCE_LENGTH))
last_prediction_cache = {}
REQUEST_COUNTER = 0
MODEL_VERSION = "3.1-PureML"
MAX_HISTORY_ENTITIES = 5000
SHAP_BACKGROUND_SIZE = 5
SHAP_NSAMPLES = 20

REQUIRED_FIELDS = [
    "entity_id", "entity_type", "source_ip", "geo_location",
    "resource_accessed", "auth_method", "session_duration",
    "command_sequence", "device_fingerprint", "login_status"
]

def encode_value(column: str, value: Any) -> int | float:
    value = str(value)
    if column not in encoders:
        try: return float(value)
        except: return 0.0
    encoder = encoders[column]
    if value in encoder.classes_:
        return encoder.transform([value])[0]
    return 0

def validate_event(event: Dict[str, Any]):
    missing = [f for f in REQUIRED_FIELDS if f not in event or event[f] is None or str(event[f]).strip() == ""]
    if missing: return False, "Missing required field(s): " + ", ".join(missing)
    try: float(event["session_duration"])
    except: return False, "session_duration must be numeric."
    return True, ""

def get_time_features(event):
    now = datetime.now()
    return int(event.get("hour", now.hour)), int(event.get("day_of_week", now.weekday())), int(event.get("is_weekend", int(now.weekday() >= 5)))

def preprocess_event(event):
    hour, day, weekend = get_time_features(event)
    processed = {
        "entity_type": encode_value("entity_type", event["entity_type"]),
        "source_ip": encode_value("source_ip", event["source_ip"]),
        "geo_location": encode_value("geo_location", event["geo_location"]),
        "resource_accessed": encode_value("resource_accessed", event["resource_accessed"]),
        "auth_method": encode_value("auth_method", event["auth_method"]),
        "session_duration": float(event["session_duration"]),
        "command_sequence": encode_value("command_sequence", event["command_sequence"]),
        "device_fingerprint": encode_value("device_fingerprint", event["device_fingerprint"]),
        "login_status": encode_value("login_status", event["login_status"]),
        "hour": hour, "day_of_week": day, "is_weekend": weekend
    }
    feature_vector = np.array([processed[col] for col in feature_cols]).reshape(1, -1)
    return scaler.transform(feature_vector)[0]

def add_event_to_history(entity_id, processed_event):
    if len(entity_history) > MAX_HISTORY_ENTITIES:
        oldest = next(iter(entity_history))
        entity_history.pop(oldest, None)
    entity_history[entity_id].append(processed_event)

def build_sequence(entity_id):
    history = list(entity_history[entity_id])
    while len(history) < SEQUENCE_LENGTH:
        history.insert(0, history[0])
    sequence = np.array(history)
    return sequence.reshape(1, SEQUENCE_LENGTH, len(feature_cols))

logger.info("Initializing SHAP Explainer...")
background = np.zeros((SHAP_BACKGROUND_SIZE, SEQUENCE_LENGTH * len(feature_cols)))

def predict_wrapper(x):
    x = np.asarray(x).reshape((x.shape[0], SEQUENCE_LENGTH, len(feature_cols)))
    return model.predict(x, verbose=0)

explainer = shap.KernelExplainer(predict_wrapper, background)

def predict_sequence(sequence):
    probabilities = model.predict(sequence, verbose=0)[0]
    class_index = int(np.argmax(probabilities))
    confidence = float(probabilities[class_index] * 100)
    prediction = label_encoder.inverse_transform([class_index])[0]
    return prediction, confidence, class_index, probabilities

def generate_shap_explanation(sequence, class_index, prediction):
    flattened = sequence.reshape(1, SEQUENCE_LENGTH * len(feature_cols))
    shap_values = explainer.shap_values(flattened, nsamples=SHAP_NSAMPLES)
    
    if isinstance(shap_values, list): scores = np.array(shap_values[class_index])[0]
    else:
        values = np.array(shap_values)
        scores = values[0, :, class_index] if values.ndim == 3 else values[0]
            
    scores = scores.reshape(SEQUENCE_LENGTH, len(feature_cols))
    importance = np.mean(np.abs(scores), axis=0)
    top_indices = np.argsort(importance)[::-1][:5]
    
    explanations = []
    for idx in top_indices:
        explanations.append({
            "feature": feature_cols[idx].replace("_", " ").title(),
            "impact": round(float(importance[idx]), 4),
            "direction": ("pushed toward anomaly" if prediction != "normal" else "supported normal behaviour")
        })
    return explanations

def build_response(prediction, confidence, explanations, probabilities):
    return {
        "status": "success",
        "classification_type": ("Normal" if prediction == "normal" else "Anomaly"),
        "prediction": prediction.replace("_", " ").title(),
        "confidence": round(confidence, 2),
        "top_features": explanations,
        "class_probabilities": {
            label_encoder.inverse_transform([i])[0].replace("_", " ").title(): round(float(probabilities[i] * 100), 2)
            for i in range(len(probabilities))
        },
        "timestamp": datetime.now().isoformat(),
        "model_version": MODEL_VERSION
    }

@app.route("/api/analyze", methods=["POST"])
def analyze():
    global REQUEST_COUNTER
    REQUEST_COUNTER += 1
    try:
        event = request.get_json(silent=True)
        if event is None: return jsonify({"status": "error", "message": "Invalid JSON request."}), 400

        valid, message = validate_event(event)
        if not valid: return jsonify({"status": "error", "message": message}), 400

        entity_id = str(event["entity_id"])
        processed_event = preprocess_event(event)
        add_event_to_history(entity_id, processed_event)
        collected = len(entity_history[entity_id])

        sequence = build_sequence(entity_id)
        prediction, confidence, class_index, probabilities = predict_sequence(sequence)

        explanations = generate_shap_explanation(sequence, class_index, prediction)
        response = build_response(prediction, confidence, explanations, probabilities)
        
        response["entity_id"] = entity_id
        response["history_size"] = collected
        last_prediction_cache[entity_id] = response

        return jsonify(response)
    except Exception as e:
        logger.error(traceback.format_exc())
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/prediction/<entity_id>", methods=["GET"])
def last_prediction(entity_id):
    return jsonify(last_prediction_cache.get(entity_id)) if entity_id in last_prediction_cache else (jsonify({"status": "error"}), 404)

@app.route("/api/reset", methods=["POST"])
def reset():
    entity_history.clear()
    last_prediction_cache.clear()
    return jsonify({"status": "success", "message": "All runtime history has been cleared."})

@app.route("/health", methods=["GET"])
def health(): return jsonify({"status": "healthy"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True, threaded=True)