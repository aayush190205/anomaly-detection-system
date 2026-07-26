import os
import joblib
import numpy as np
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.utils.class_weight import compute_class_weight
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.utils import to_categorical
from tensorflow.keras.callbacks import EarlyStopping

print("Loading dataset...")

DATA_PATH = "../data-generator/synthetic_access_logs.csv"

if not os.path.exists(DATA_PATH):
    raise FileNotFoundError(DATA_PATH)

df = pd.read_csv(DATA_PATH)

df["timestamp"] = pd.to_datetime(df["timestamp"])
df = df.sort_values(["entity_id", "timestamp"]).reset_index(drop=True)

df["hour"] = df["timestamp"].dt.hour
df["day_of_week"] = df["timestamp"].dt.dayofweek
df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)
df["login_status"] = df["login_status"].fillna("success")

categorical_cols = [
    "entity_type", "source_ip", "geo_location", "resource_accessed",
    "auth_method", "command_sequence", "device_fingerprint", "login_status"
]

encoders = {}
for col in categorical_cols:
    le = LabelEncoder()
    df[col] = le.fit_transform(df[col].astype(str))
    encoders[col] = le

feature_cols = [
    "entity_type", "source_ip", "geo_location", "resource_accessed",
    "auth_method", "session_duration", "command_sequence", "device_fingerprint",
    "login_status", "hour", "day_of_week", "is_weekend"
]

scaler = StandardScaler()
df[feature_cols] = scaler.fit_transform(df[feature_cols])

label_encoder = LabelEncoder()
df["target"] = label_encoder.fit_transform(df["label"])
NUM_CLASSES = len(label_encoder.classes_)
SEQUENCE_LENGTH = 5

def create_sequences(dataframe):
    X, y = [], []
    for entity_id, group in dataframe.groupby("entity_id"):
        group = group.sort_values("timestamp")
        values = group[feature_cols].values
        labels = group["target"].values

        if len(group) < SEQUENCE_LENGTH:
            continue

        for i in range(len(group) - SEQUENCE_LENGTH + 1):
            X.append(values[i:i + SEQUENCE_LENGTH])
            y.append(labels[i + SEQUENCE_LENGTH - 1])
    return np.array(X), np.array(y)

print("Splitting dataset by entities to prevent data leakage...")
unique_entities = df["entity_id"].unique()

# 1. SPLIT BY ENTITY FIRST
train_entities, test_entities = train_test_split(
    unique_entities, test_size=0.2, random_state=42
)

train_df = df[df["entity_id"].isin(train_entities)]
test_df = df[df["entity_id"].isin(test_entities)]

print("Creating sequences...")
X_train, y_train = create_sequences(train_df)
X_test, y_test = create_sequences(test_df)

y_train_cat = to_categorical(y_train, num_classes=NUM_CLASSES)
y_test_cat = to_categorical(y_test, num_classes=NUM_CLASSES)

class_weights = compute_class_weight(
    class_weight="balanced",
    classes=np.unique(y_train),
    y=y_train
)
class_weights = dict(enumerate(class_weights))

print("Training Samples :", X_train.shape)
print("Testing Samples  :", X_test.shape)
print("Classes :", label_encoder.classes_)

print("Building LSTM model...")
model = Sequential([
    LSTM(128, input_shape=(X_train.shape[1], X_train.shape[2]), return_sequences=True),
    Dropout(0.3),
    LSTM(64, return_sequences=False),
    Dropout(0.3),
    Dense(64, activation="relu"),
    Dropout(0.2),
    Dense(32, activation="relu"),
    Dense(NUM_CLASSES, activation="softmax")
])

model.compile(
    optimizer="adam",
    loss="categorical_crossentropy",
    metrics=["accuracy"]
)

early_stop = EarlyStopping(
    monitor="val_loss",
    patience=8,
    restore_best_weights=True
)

print("Training model...")
history = model.fit(
    X_train, y_train_cat,
    epochs=30,
    batch_size=64,
    validation_split=0.2,
    callbacks=[early_stop],
    class_weight=class_weights,
    verbose=1
)

print("\nEvaluating model...")
loss, accuracy = model.evaluate(X_test, y_test_cat, verbose=0)
print(f"\nTest Accuracy : {accuracy:.4f}")
print(f"Test Loss     : {loss:.4f}")

print("\nSaving model and preprocessing artifacts...")
os.makedirs("models", exist_ok=True)
model.save("models/lstm_detector.keras")
joblib.dump(scaler, "models/scaler.pkl")
joblib.dump(encoders, "models/encoders.pkl")
joblib.dump(label_encoder, "models/label_encoder.pkl")
joblib.dump(feature_cols, "models/feature_cols.pkl")
joblib.dump(SEQUENCE_LENGTH, "models/sequence_length.pkl")
joblib.dump(class_weights, "models/class_weights.pkl")

print("Training Complete. Model is ready for real-time inference.")