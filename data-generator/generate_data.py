import pandas as pd
import numpy as np
from faker import Faker
import random
from datetime import datetime, timedelta

fake = Faker()

# Define resources and commands for realism
RESOURCES = ['/api/v1/data', '/login', '/dashboard', 'port:22', '/admin/settings', 'db_query']
AUTH_METHODS = ['password', 'token', 'certificate', 'biometric']

def create_entity_profiles(num_entities=200):
    entities = {}
    for _ in range(num_entities):
        entity_id = fake.uuid4()
        entities[entity_id] = {
            'entity_type': random.choice(['user', 'user', 'service_account', 'edge_device']),
            'typical_ip': fake.ipv4(),
            'typical_geo': fake.city(),
            'device_fingerprint': fake.mac_address()
        }
    return entities

def generate_normal_baseline(entities, start_time, num_records=5000):
    data = []
    current_time = start_time
    
    for _ in range(num_records):
        entity_id = random.choice(list(entities.keys()))
        profile = entities[entity_id]
        current_time += timedelta(minutes=random.randint(1, 60))
        
        data.append({
            'entity_id': entity_id,
            'entity_type': profile['entity_type'],
            'timestamp': current_time.strftime("%Y-%m-%d %H:%M:%S"),
            'source_ip': profile['typical_ip'],
            'geo_location': profile['typical_geo'],
            'resource_accessed': random.choice(['/api/v1/data', '/login', '/dashboard']),
            'auth_method': random.choice(['password', 'token']),
            'session_duration': round(random.uniform(5.0, 120.0), 2),
            'command_sequence': "READ, GET",
            'device_fingerprint': profile['device_fingerprint'],
            'label': 'normal'
        })
    return data

def inject_brute_force(entities, current_time, num_attacks=5):
    attack_data = []
    for _ in range(num_attacks):
        target_entity = random.choice(list(entities.keys()))
        attack_ip = fake.ipv4()
        attack_time = current_time + timedelta(hours=random.randint(1, 48))
        
        for _ in range(20):
            attack_time += timedelta(seconds=random.randint(1, 3))
            attack_data.append({
                'entity_id': target_entity,
                'entity_type': entities[target_entity]['entity_type'],
                'timestamp': attack_time.strftime("%Y-%m-%d %H:%M:%S"),
                'source_ip': attack_ip,
                'geo_location': fake.city(),
                'resource_accessed': '/login',
                'auth_method': 'password',
                'session_duration': 0.0,
                'command_sequence': "FAILED_AUTH",
                'device_fingerprint': fake.mac_address(),
                'label': 'brute_force'
            })
    return attack_data

def inject_credential_stuffing(entities, current_time, num_campaigns=3):
    attack_data = []
    for _ in range(num_campaigns):
        attack_ip = fake.ipv4()
        attack_time = current_time + timedelta(days=random.randint(1, 10))
        
        # Attacker tries many different entities from one IP
        targeted_entities = random.sample(list(entities.keys()), 30)
        
        for entity_id in targeted_entities:
            attack_time += timedelta(seconds=random.randint(2, 10))
            attack_data.append({
                'entity_id': entity_id,
                'entity_type': entities[entity_id]['entity_type'],
                'timestamp': attack_time.strftime("%Y-%m-%d %H:%M:%S"),
                'source_ip': attack_ip,
                'geo_location': fake.city(),
                'resource_accessed': '/login',
                'auth_method': 'password',
                'session_duration': 0.0,
                'command_sequence': "FAILED_AUTH",
                'device_fingerprint': fake.mac_address(),
                'label': 'credential_stuffing'
            })
    return attack_data

def inject_impossible_travel(entities, current_time, num_attacks=5):
    attack_data = []
    for _ in range(num_attacks):
        entity_id = random.choice(list(entities.keys()))
        profile = entities[entity_id]
        
        base_time = current_time + timedelta(days=random.randint(1, 5))
        attack_data.append({
            'entity_id': entity_id,
            'entity_type': profile['entity_type'],
            'timestamp': base_time.strftime("%Y-%m-%d %H:%M:%S"),
            'source_ip': profile['typical_ip'],
            'geo_location': profile['typical_geo'],
            'resource_accessed': '/dashboard',
            'auth_method': 'token',
            'session_duration': 30.0,
            'command_sequence': "READ",
            'device_fingerprint': profile['device_fingerprint'],
            'label': 'normal'
        })
        
        impossible_time = base_time + timedelta(minutes=10)
        attack_data.append({
            'entity_id': entity_id,
            'entity_type': profile['entity_type'],
            'timestamp': impossible_time.strftime("%Y-%m-%d %H:%M:%S"),
            'source_ip': fake.ipv4(),
            'geo_location': fake.country(),
            'resource_accessed': '/dashboard',
            'auth_method': 'token',
            'session_duration': 45.0,
            'command_sequence': "READ",
            'device_fingerprint': fake.mac_address(),
            'label': 'impossible_travel'
        })
    return attack_data

def inject_lateral_movement(entities, current_time, num_attacks=5):
    attack_data = []
    for _ in range(num_attacks):
        entity_id = random.choice(list(entities.keys()))
        profile = entities[entity_id]
        attack_time = current_time + timedelta(days=random.randint(1, 15))
        
        # Normal user suddenly accessing a string of sensitive resources they never touch
        unusual_resources = ['port:22', '/admin/settings', 'db_query']
        for resource in unusual_resources:
            attack_time += timedelta(minutes=random.randint(1, 5))
            attack_data.append({
                'entity_id': entity_id,
                'entity_type': profile['entity_type'],
                'timestamp': attack_time.strftime("%Y-%m-%d %H:%M:%S"),
                'source_ip': profile['typical_ip'],
                'geo_location': profile['typical_geo'],
                'resource_accessed': resource,
                'auth_method': 'certificate',
                'session_duration': round(random.uniform(60.0, 300.0), 2),
                'command_sequence': "ESCALATE, DUMP, EXEC",
                'device_fingerprint': profile['device_fingerprint'],
                'label': 'lateral_movement'
            })
    return attack_data

def inject_low_and_slow(entities, current_time, num_attacks=3):
    attack_data = []
    for _ in range(num_attacks):
        entity_id = random.choice(list(entities.keys()))
        profile = entities[entity_id]
        
        # Off-hours access (e.g., 3 AM) spread over several days
        base_date = current_time + timedelta(days=random.randint(1, 5))
        
        for day_offset in range(5):
            attack_time = base_date + timedelta(days=day_offset)
            # Set time to roughly 3 AM
            attack_time = attack_time.replace(hour=3, minute=random.randint(0, 59))
            
            attack_data.append({
                'entity_id': entity_id,
                'entity_type': profile['entity_type'],
                'timestamp': attack_time.strftime("%Y-%m-%d %H:%M:%S"),
                'source_ip': profile['typical_ip'],
                'geo_location': profile['typical_geo'],
                'resource_accessed': '/api/v1/data',
                'auth_method': 'token',
                'session_duration': round(random.uniform(300.0, 600.0), 2),
                'command_sequence': "READ, EXPORT_CHUNK",
                'device_fingerprint': profile['device_fingerprint'],
                'label': 'low_and_slow'
            })
    return attack_data

def inject_device_spoofing(entities, current_time, num_attacks=5):
    attack_data = []
    for _ in range(num_attacks):
        entity_id = random.choice(list(entities.keys()))
        profile = entities[entity_id]
        attack_time = current_time + timedelta(days=random.randint(1, 10))
        
        attack_data.append({
            'entity_id': entity_id,
            'entity_type': profile['entity_type'],
            'timestamp': attack_time.strftime("%Y-%m-%d %H:%M:%S"),
            'source_ip': profile['typical_ip'], 
            'geo_location': profile['typical_geo'],
            'resource_accessed': '/api/v1/data',
            'auth_method': 'token',
            'session_duration': 15.0,
            'command_sequence': "DATA_EXPORT",
            'device_fingerprint': fake.mac_address(),
            'label': 'device_spoofing'
        })
    return attack_data

if __name__ == "__main__":
    print("Initializing synthetic data generation pipeline...")
    
    start_time = datetime.now() - timedelta(days=30)
    entities = create_entity_profiles(num_entities=150)
    
    print("Generating baseline behavior...")
    baseline_data = generate_normal_baseline(entities, start_time, num_records=8000)
    
    print("Injecting threat scenarios...")
    brute_force_data = inject_brute_force(entities, start_time, num_attacks=15)
    cred_stuffing_data = inject_credential_stuffing(entities, start_time, num_campaigns=5)
    impossible_travel_data = inject_impossible_travel(entities, start_time, num_attacks=15)
    lateral_movement_data = inject_lateral_movement(entities, start_time, num_attacks=10)
    low_and_slow_data = inject_low_and_slow(entities, start_time, num_attacks=10)
    device_spoofing_data = inject_device_spoofing(entities, start_time, num_attacks=15)
    
    all_data = (baseline_data + brute_force_data + cred_stuffing_data + 
                impossible_travel_data + lateral_movement_data + 
                low_and_slow_data + device_spoofing_data)
    
    df = pd.DataFrame(all_data)
    
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values(by='timestamp').reset_index(drop=True)
    
    output_path = "synthetic_access_logs.csv"
    df.to_csv(output_path, index=False)
    
    print(f"\nSuccess! Generated {len(df)} total events.")
    print("Anomaly Distribution:")
    print(df['label'].value_counts())