from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
import joblib
import shap
from tensorflow.keras.models import load_model

app = Flask(__name__)
CORS(app) # Allows your React frontend to connect

print("Loading LSTM Model and Profilers into memory...")
model = load_model("models/lstm_detector.h5")
scaler = joblib.load("models/scaler.pkl")
encoders = joblib.load("models/encoders.pkl")
label_encoder = joblib.load("models/label_encoder.pkl")
feature_cols = joblib.load("models/feature_cols.pkl")

# Initialize SHAP Explainer (Deliverable 5)
# We use a zero-array as the baseline representing "normal" scaled values
background = np.zeros((1, len(feature_cols)))

def lstm_predict_wrapper(x):
    # Reshape input back to [samples, timesteps, features] for the LSTM
    return model.predict(x.reshape(-1, 1, len(feature_cols)), verbose=0)

explainer = shap.KernelExplainer(lstm_predict_wrapper, background)

@app.route('/api/analyze', methods=['POST'])
def analyze_log():
    try:
        log_data = request.json
        
        # 1. Preprocess the incoming JSON log precisely like the training data
        processed_log = []
        for col in feature_cols:
            val = log_data.get(col, '')
            if col in encoders:
                # Handle unknown attributes gracefully (e.g., a brand new device ID)
                if val in encoders[col].classes_:
                    val = encoders[col].transform([str(val)])[0]
                else:
                    val = 0 
            processed_log.append(float(val))
            
        X_array = np.array([processed_log])
        X_scaled = scaler.transform(X_array)
        X_lstm = X_scaled.reshape((1, 1, len(feature_cols)))
        
        # 2. Make Sequence-Aware Prediction
        predictions = model.predict(X_lstm, verbose=0)
        class_idx = np.argmax(predictions[0])
        confidence = float(np.max(predictions[0])) * 100
        predicted_label = label_encoder.inverse_transform([class_idx])[0]
        
        # 3. Generate SHAP Explainability on the fly
        shap_values = explainer.shap_values(X_scaled)
        
        # Extract top 2 features driving this specific prediction
        class_shap = shap_values[class_idx][0]
        top_indices = np.argsort(np.abs(class_shap))[-2:]
        top_features = [feature_cols[i].replace('_', ' ').title() for i in top_indices]
        
        explanation = f"SHAP Analysis: Alert triggered due to deviations in {top_features[1]} and {top_features[0]}."
        if predicted_label == 'normal':
            explanation = "Access behavior perfectly matches the established baseline profile."
            
        return jsonify({
            "status": "success",
            "prediction": predicted_label.replace('_', ' ').title(),
            "confidence": round(confidence, 2),
            "explanation": explanation
        })
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    print("AI Chatbot Backend running on http://localhost:5000")
    app.run(port=5000, debug=True)