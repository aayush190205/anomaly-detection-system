import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, StandardScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.utils import to_categorical
import joblib
import os

print("Loading synthetic dataset...")
data_path = "../data-generator/synthetic_access_logs.csv"
if not os.path.exists(data_path):
    print(f"Error: Data not found at {data_path}")
    exit()

df = pd.read_csv(data_path)

print("Encoding and profiling baseline features...")
features_to_encode = ['entity_type', 'source_ip', 'geo_location', 'resource_accessed', 'auth_method', 'command_sequence', 'device_fingerprint']
encoders = {}
X_raw = df.copy()

for col in features_to_encode:
    encoders[col] = LabelEncoder()
    X_raw[col] = encoders[col].fit_transform(X_raw[col].astype(str))

feature_cols = ['entity_type', 'source_ip', 'geo_location', 'resource_accessed', 'auth_method', 'session_duration', 'command_sequence', 'device_fingerprint']
X = X_raw[feature_cols].values

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

X_lstm = X_scaled.reshape((X_scaled.shape[0], 1, X_scaled.shape[1]))

label_encoder = LabelEncoder()
y_encoded = label_encoder.fit_transform(df['label'])
y_categorical = to_categorical(y_encoded)

print("Building Sequence-Aware LSTM Model...")
model = Sequential([
    LSTM(64, input_shape=(X_lstm.shape[1], X_lstm.shape[2]), return_sequences=True),
    Dropout(0.2),
    LSTM(32),
    Dropout(0.2),
    Dense(32, activation='relu'),
    Dense(y_categorical.shape[1], activation='softmax') 
])

model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])

print("Training LSTM Sequence Model (This may take a minute)...")
model.fit(X_lstm, y_categorical, epochs=5, batch_size=64, validation_split=0.2, verbose=1)

os.makedirs("models", exist_ok=True)
model.save("models/lstm_detector.h5")
joblib.dump(scaler, "models/scaler.pkl")
joblib.dump(encoders, "models/encoders.pkl")
joblib.dump(label_encoder, "models/label_encoder.pkl")
joblib.dump(feature_cols, "models/feature_cols.pkl")

print("\nSuccess! Baseline profilers and LSTM Model saved to models/ directory.")