import pandas as pd
import numpy as np
import joblib
import shap
import os

print("Initializing Real-Time Inference Pipeline...")

# 1. Load the pre-trained model and encoders
try:
    model = joblib.load("models/anomaly_detector.pkl")
    encoders = joblib.load("models/encoders.pkl")
except FileNotFoundError:
    print("Error: Models not found. Run train.py first.")
    exit()

# 2. Simulate Real-Time Test Data (Extreme Class Imbalance)
data_path = "../data-generator/synthetic_access_logs.csv"
df_full = pd.read_csv(data_path)

df_normal = df_full[df_full['label'] == 'normal'].sample(n=2000, replace=True)
df_anomalies = df_full[df_full['label'] != 'normal'].sample(n=15, replace=True)
live_stream = pd.concat([df_normal, df_anomalies]).sample(frac=1).reset_index(drop=True)

# STRIP THE LABELS - The AI must predict these blindly
live_stream = live_stream.drop(columns=['label'])

# 3. Preprocess incoming live data
X_live = live_stream.copy()
features_to_encode = ['entity_type', 'source_ip', 'geo_location', 'resource_accessed', 'auth_method', 'command_sequence', 'device_fingerprint']

for col in features_to_encode:
    # Safely handle unseen data categories
    X_live[col] = X_live[col].map(lambda s: s if s in encoders[col].classes_ else '<unknown>')
    if '<unknown>' not in encoders[col].classes_:
        encoders[col].classes_ = np.append(encoders[col].classes_, '<unknown>')
    X_live[col] = encoders[col].transform(X_live[col].astype(str))

feature_cols = ['entity_type', 'source_ip', 'geo_location', 'resource_accessed', 'auth_method', 'session_duration', 'command_sequence', 'device_fingerprint']
X_model = X_live[feature_cols]

# 4. Make Real-Time Predictions
print("Scanning live traffic for anomalies...")
live_stream['predicted_anomaly'] = model.predict(X_model)
probabilities = model.predict_proba(X_model)
live_stream['risk_score'] = (np.max(probabilities, axis=1) * 100).astype(int)

# 5. Filter for the Analyst Queue
alerts = live_stream[live_stream['predicted_anomaly'] != 'normal'].copy()
print(f"Scan complete. Found {len(alerts)} suspicious events in {len(live_stream)} total logs.")

if not alerts.empty:
    # 6. Generate SHAP/LIME Explainability
    print("Generating Feature Attribution (Explainability) for alerts...")
    explainer = shap.TreeExplainer(model)
    X_alerts = X_model.loc[alerts.index]
    shap_values = explainer.shap_values(X_alerts)
    class_names = model.classes_
    
    explanations = []
    for i, (_, row) in enumerate(alerts.iterrows()):
        pred_class_idx = np.where(class_names == row['predicted_anomaly'])[0][0]
        
        # THE FIX: Safely extract SHAP values regardless of library version (List vs 3D Array)
        if isinstance(shap_values, list):
            row_shap = shap_values[pred_class_idx][i]
        else:
            row_shap = shap_values[i, :, pred_class_idx]
            
        # Get the top 2 features driving the anomaly (using absolute impact)
        top_indices = np.argsort(np.abs(row_shap))[-2:]
        top_features = [feature_cols[idx] for idx in top_indices]
        formatted_features = [f.replace('_', ' ').title() for f in top_features]
        
        explanations.append(f"SHAP/LIME Insight: Anomaly driven by {formatted_features[1]} and {formatted_features[0]}.")
        
    alerts['feature_attribution'] = explanations
else:
    alerts['feature_attribution'] = []

# 7. Forward to Frontend
output_path = "live_alerts.csv"
alerts.to_csv(output_path, index=False)
print(f"Alerts forwarded to {output_path} for the SOC Dashboard.")