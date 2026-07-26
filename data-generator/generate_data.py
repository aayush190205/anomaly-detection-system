from datetime import datetime, timedelta
from faker import Faker
import random
import numpy as np
import pandas as pd

fake = Faker()

def create_entity_profiles(num_entities=200):
    entities = {}

    normal_resources = [
        "/dashboard",
        "/user/profile",
        "/api/v1/data",
        "/documents",
        "/notifications"
    ]

    normal_commands = [
        "LOGIN",
        "READ",
        "SEARCH",
        "UPDATE_PROFILE",
        "DOWNLOAD",
        "LOGOUT"
    ]

    auth_methods = [
        "password",
        "token",
        "certificate"
    ]

    entity_types = [
        "user",
        "user",
        "user",
        "service_account",
        "edge_device"
    ]

    for _ in range(num_entities):
        entity_id = fake.uuid4()

        entities[entity_id] = {
            "entity_type": random.choice(entity_types),
            "typical_ip": fake.ipv4_private(),
            "typical_geo": fake.city(),
            "device_fingerprint": fake.mac_address(),
            "preferred_auth": random.choice(auth_methods),
            "normal_resources": random.sample(normal_resources, k=3),
            "normal_commands": random.sample(normal_commands, k=4),
            "avg_session": random.randint(20, 90)
        }

    return entities

def generate_normal_baseline(entities, start_time, num_records=10000):
    data = []
    current_time = start_time

    for _ in range(num_records):
        entity_id = random.choice(list(entities.keys()))
        profile = entities[entity_id]

        current_time += timedelta(minutes=random.randint(1, 45))

        session = max(
            2,
            np.random.normal(profile["avg_session"], 8)
        )

        cmd_count = random.randint(2, 4)

        commands = random.sample(
            profile["normal_commands"],
            k=cmd_count
        )

        data.append({
            "entity_id": entity_id,
            "entity_type": profile["entity_type"],
            "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S"),
            "source_ip": profile["typical_ip"],
            "geo_location": profile["typical_geo"],
            "resource_accessed": random.choice(profile["normal_resources"]),
            "auth_method": profile["preferred_auth"],
            "session_duration": round(session, 2),
            "command_sequence": ",".join(commands),
            "device_fingerprint": profile["device_fingerprint"],
            "login_status": "success",
            "label": "normal"
        })

    return data

def inject_brute_force(entities, current_time, num_attacks=50):
    attack_data = []

    for _ in range(num_attacks):
        entity_id = random.choice(list(entities.keys()))
        profile = entities[entity_id]

        attacker_ip = fake.ipv4()
        attack_time = current_time + timedelta(days=random.randint(1, 10))

        for _ in range(random.randint(15, 30)):
            attack_time += timedelta(seconds=random.randint(1, 3))

            attack_data.append({
                "entity_id": entity_id,
                "entity_type": profile["entity_type"],
                "timestamp": attack_time.strftime("%Y-%m-%d %H:%M:%S"),
                "source_ip": attacker_ip,
                "geo_location": fake.city(),
                "resource_accessed": "/login",
                "auth_method": "password",
                "session_duration": 0.0,
                "command_sequence": "LOGIN",
                "device_fingerprint": fake.mac_address(),
                "login_status": "failure",
                "label": "brute_force"
            })

        attack_time += timedelta(seconds=5)

        attack_data.append({
            "entity_id": entity_id,
            "entity_type": profile["entity_type"],
            "timestamp": attack_time.strftime("%Y-%m-%d %H:%M:%S"),
            "source_ip": attacker_ip,
            "geo_location": fake.city(),
            "resource_accessed": "/login",
            "auth_method": "password",
            "session_duration": round(random.uniform(5, 20), 2),
            "command_sequence": "LOGIN,READ",
            "device_fingerprint": fake.mac_address(),
            "login_status": "success",
            "label": "brute_force"
        })

    return attack_data

def inject_credential_stuffing(entities, current_time, num_campaigns=20):
    attack_data = []

    for _ in range(num_campaigns):
        attacker_ip = fake.ipv4()

        attack_time = current_time + timedelta(
            days=random.randint(1, 15)
        )

        victims = random.sample(
            list(entities.keys()),
            min(40, len(entities))
        )

        for entity_id in victims:
            profile = entities[entity_id]

            attack_time += timedelta(
                seconds=random.randint(2, 6)
            )

            attack_data.append({
                "entity_id": entity_id,
                "entity_type": profile["entity_type"],
                "timestamp": attack_time.strftime("%Y-%m-%d %H:%M:%S"),
                "source_ip": attacker_ip,
                "geo_location": fake.city(),
                "resource_accessed": "/login",
                "auth_method": "password",
                "session_duration": 0.0,
                "command_sequence": "LOGIN",
                "device_fingerprint": fake.mac_address(),
                "login_status": random.choice(
                    ["failure"] * 9 + ["success"]
                ),
                "label": "credential_stuffing"
            })

    return attack_data

def inject_impossible_travel(entities, current_time, num_attacks=50):
    attack_data = []

    for _ in range(num_attacks):
        entity_id = random.choice(list(entities.keys()))
        profile = entities[entity_id]

        base_time = current_time + timedelta(days=random.randint(1, 10))

        attack_data.append({
            "entity_id": entity_id,
            "entity_type": profile["entity_type"],
            "timestamp": base_time.strftime("%Y-%m-%d %H:%M:%S"),
            "source_ip": profile["typical_ip"],
            "geo_location": profile["typical_geo"],
            "resource_accessed": random.choice(profile["normal_resources"]),
            "auth_method": profile["preferred_auth"],
            "session_duration": round(np.random.normal(profile["avg_session"], 5), 2),
            "command_sequence": "LOGIN,READ",
            "device_fingerprint": profile["device_fingerprint"],
            "login_status": "success",
            "label": "normal"
        })

        attack_time = base_time + timedelta(minutes=random.randint(5, 20))

        attack_data.append({
            "entity_id": entity_id,
            "entity_type": profile["entity_type"],
            "timestamp": attack_time.strftime("%Y-%m-%d %H:%M:%S"),
            "source_ip": fake.ipv4(),
            "geo_location": fake.country(),
            "resource_accessed": random.choice(profile["normal_resources"]),
            "auth_method": profile["preferred_auth"],
            "session_duration": round(np.random.normal(profile["avg_session"], 5), 2),
            "command_sequence": "LOGIN,READ",
            "device_fingerprint": fake.mac_address(),
            "login_status": "success",
            "label": "impossible_travel"
        })

    return attack_data

def inject_lateral_movement(entities, current_time, num_attacks=40):
    attack_data = []

    sensitive_resources = [
        "/admin/settings",
        "port:22",
        "db_query",
        "/backup",
        "/internal/config"
    ]

    for _ in range(num_attacks):
        entity_id = random.choice(list(entities.keys()))
        profile = entities[entity_id]

        attack_time = current_time + timedelta(days=random.randint(1, 20))

        path = (
            profile["normal_resources"] +
            random.sample(sensitive_resources, 3)
        )

        for resource in path:
            attack_time += timedelta(minutes=random.randint(1, 4))

            attack_data.append({
                "entity_id": entity_id,
                "entity_type": profile["entity_type"],
                "timestamp": attack_time.strftime("%Y-%m-%d %H:%M:%S"),
                "source_ip": profile["typical_ip"],
                "geo_location": profile["typical_geo"],
                "resource_accessed": resource,
                "auth_method": profile["preferred_auth"],
                "session_duration": round(random.uniform(60, 250), 2),
                "command_sequence": random.choice([
                    "LOGIN,READ",
                    "READ,SEARCH",
                    "SEARCH,DOWNLOAD",
                    "READ,DOWNLOAD"
                ]),
                "device_fingerprint": profile["device_fingerprint"],
                "login_status": "success",
                "label": "lateral_movement"
            })

    return attack_data

def inject_low_and_slow(entities, current_time, num_attacks=40):
    attack_data = []

    for _ in range(num_attacks):
        entity_id = random.choice(list(entities.keys()))
        profile = entities[entity_id]

        start_day = current_time + timedelta(days=random.randint(1, 10))

        for day in range(7):
            attack_time = (
                start_day +
                timedelta(days=day)
            ).replace(
                hour=random.randint(1, 4),
                minute=random.randint(0, 59)
            )

            attack_data.append({
                "entity_id": entity_id,
                "entity_type": profile["entity_type"],
                "timestamp": attack_time.strftime("%Y-%m-%d %H:%M:%S"),
                "source_ip": profile["typical_ip"],
                "geo_location": profile["typical_geo"],
                "resource_accessed": random.choice(profile["normal_resources"]),
                "auth_method": profile["preferred_auth"],
                "session_duration": round(random.uniform(250, 700), 2),
                "command_sequence": random.choice([
                    "LOGIN,READ",
                    "READ,SEARCH",
                    "SEARCH,DOWNLOAD",
                    "READ,DOWNLOAD"
                ]),
                "device_fingerprint": profile["device_fingerprint"],
                "login_status": "success",
                "label": "low_and_slow"
            })

    return attack_data

def inject_device_spoofing(entities, current_time, num_attacks=50):
    attack_data = []

    for _ in range(num_attacks):
        entity_id = random.choice(list(entities.keys()))
        profile = entities[entity_id]

        attack_time = current_time + timedelta(days=random.randint(1, 15))

        attack_data.append({
            "entity_id": entity_id,
            "entity_type": profile["entity_type"],
            "timestamp": attack_time.strftime("%Y-%m-%d %H:%M:%S"),
            "source_ip": profile["typical_ip"],
            "geo_location": profile["typical_geo"],
            "resource_accessed": random.choice(profile["normal_resources"]),
            "auth_method": profile["preferred_auth"],
            "session_duration": round(np.random.normal(profile["avg_session"], 5), 2),
            "command_sequence": "LOGIN,READ",
            "device_fingerprint": fake.mac_address(),
            "login_status": "success",
            "label": "device_spoofing"
        })

    return attack_data

if __name__ == "__main__":
    print("Initializing synthetic data generation pipeline...")
    
    start_time = datetime.now() - timedelta(days=90)
    entities = create_entity_profiles(num_entities=1000)
    
    print("Generating baseline behavior...")
    baseline_data = generate_normal_baseline(entities, start_time, num_records=100000)
    
    print("Injecting threat scenarios...")
    brute_force_data = inject_brute_force(entities, start_time, num_attacks=300)
    cred_stuffing_data = inject_credential_stuffing(entities, start_time, num_campaigns=100)
    impossible_travel_data = inject_impossible_travel(entities, start_time, num_attacks=300)
    lateral_movement_data = inject_lateral_movement(entities, start_time, num_attacks=250)
    low_and_slow_data = inject_low_and_slow(entities, start_time, num_attacks=250)
    device_spoofing_data = inject_device_spoofing(entities, start_time, num_attacks=300)
    
    all_data = (baseline_data + brute_force_data + cred_stuffing_data + 
                impossible_travel_data + lateral_movement_data + 
                low_and_slow_data + device_spoofing_data)
    
    df = pd.DataFrame(all_data)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values(by=['entity_id', 'timestamp']).reset_index(drop=True)
    
    output_path = "synthetic_access_logs.csv"
    df.to_csv(output_path, index=False)
    
    print(f"\nSuccess! Generated {len(df)} total events.")