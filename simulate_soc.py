import pandas as pd
import numpy as np
import time
import random
from datetime import datetime
import joblib

print("🏭 AI-REASON SOC Simulator Starting...")
print("Simulating industrial network traffic...\n")

# ── Load trained model ─────────────────────────────────
model = joblib.load('model.pkl')
X = joblib.load('X.pkl')
feature_names = X.columns.tolist()

# ── Base normal connection ──────────────────────────────
def generate_normal_connection():
    return {
        'duration': random.uniform(0, 10),
        'protocol_type': 1,
        'service': random.randint(10, 30),
        'flag': 9,
        'src_bytes': random.randint(100, 2000),
        'dst_bytes': random.randint(100, 5000),
        'land': 0,
        'wrong_fragment': 0,
        'urgent': 0,
        'hot': random.randint(0, 5),
        'num_failed_logins': 0,
        'logged_in': 1,
        'lnum_compromised': 0,
        'lroot_shell': 0,
        'lsu_attempted': 0,
        'lnum_root': 0,
        'lnum_file_creations': 0,
        'lnum_shells': 0,
        'lnum_access_files': 0,
        'lnum_outbound_cmds': 0,
        'is_host_login': 0,
        'is_guest_login': 0,
        'count': random.randint(1, 50),
        'srv_count': random.randint(1, 50),
        'serror_rate': 0.0,
        'srv_serror_rate': 0.0,
        'rerror_rate': 0.0,
        'srv_rerror_rate': 0.0,
        'same_srv_rate': random.uniform(0.8, 1.0),
        'diff_srv_rate': random.uniform(0.0, 0.2),
        'srv_diff_host_rate': random.uniform(0.0, 0.2),
        'dst_host_count': random.randint(100, 255),
        'dst_host_srv_count': random.randint(100, 255),
        'dst_host_same_srv_rate': random.uniform(0.8, 1.0),
        'dst_host_diff_srv_rate': random.uniform(0.0, 0.1),
        'dst_host_same_src_port_rate': random.uniform(0.0, 0.2),
        'dst_host_srv_diff_host_rate': random.uniform(0.0, 0.1),
        'dst_host_serror_rate': 0.0,
        'dst_host_srv_serror_rate': 0.0,
        'dst_host_rerror_rate': 0.0,
        'dst_host_srv_rerror_rate': 0.0,
    }

def generate_dos_attack():
    conn = generate_normal_connection()
    conn.update({
        'src_bytes': 0,
        'dst_bytes': 0,
        'logged_in': 0,
        'count': 511,
        'srv_count': 511,
        'serror_rate': 1.0,
        'srv_serror_rate': 1.0,
        'dst_host_serror_rate': 1.0,
        'dst_host_srv_serror_rate': 1.0,
        'same_srv_rate': 1.0,
        'diff_srv_rate': 0.0,
    })
    return conn

def generate_probe_attack():
    conn = generate_normal_connection()
    conn.update({
        'src_bytes': 0,
        'dst_bytes': 0,
        'logged_in': 0,
        'count': random.randint(1, 10),
        'srv_count': random.randint(1, 5),
        'serror_rate': 0.0,
        'rerror_rate': 1.0,
        'srv_rerror_rate': 1.0,
        'diff_srv_rate': 1.0,
        'same_srv_rate': 0.0,
        'dst_host_diff_srv_rate': 1.0,
    })
    return conn

def generate_r2l_attack():
    conn = generate_normal_connection()
    conn.update({
        'logged_in': 0,
        'num_failed_logins': random.randint(3, 10),
        'src_bytes': random.randint(1000, 5000),
        'dst_bytes': random.randint(0, 100),
        'count': random.randint(1, 5),
        'srv_count': random.randint(1, 5),
    })
    return conn

def generate_modbus_normal():
    conn = generate_normal_connection()
    conn.update({
        'protocol_type': 1,
        'service': 5,
        'duration': random.uniform(0.001, 0.1),
        'src_bytes': random.randint(6, 12),
        'dst_bytes': random.randint(6, 260),
        'count': random.randint(1, 10),
    })
    return conn

def generate_modbus_attack():
    conn = generate_modbus_normal()
    conn.update({
        'count': random.randint(200, 511),
        'srv_count': random.randint(200, 511),
        'src_bytes': 0,
        'dst_bytes': 0,
        'serror_rate': random.uniform(0.8, 1.0),
        'dst_host_srv_serror_rate': random.uniform(0.8, 1.0),
    })
    return conn

# ── Traffic scenarios ───────────────────────────────────
scenarios = [
    {"name": "Normal Office Traffic",  "generator": generate_normal_connection, "weight": 60},
    {"name": "Normal Modbus Traffic",  "generator": generate_modbus_normal,     "weight": 20},
    {"name": "DoS/SYN Flood Attack",   "generator": generate_dos_attack,        "weight": 8},
    {"name": "Port Scan Probe",        "generator": generate_probe_attack,      "weight": 6},
    {"name": "Remote Login Attack",    "generator": generate_r2l_attack,        "weight": 3},
    {"name": "Modbus Protocol Attack", "generator": generate_modbus_attack,     "weight": 3},
]

weights = [s["weight"] for s in scenarios]

# ── Run simulation ─────────────────────────────────────
print("="*65)
print(f"{'Time':<10} {'Scenario':<30} {'Prediction':<12} {'Alert'}")
print("="*65)

results = []
n_connections = 50

for i in range(n_connections):
    scenario = random.choices(scenarios, weights=weights)[0]
    conn_dict = scenario["generator"]()
    conn_df = pd.DataFrame([conn_dict])[feature_names]

    prediction = model.predict(conn_df)[0]
    proba = model.predict_proba(conn_df)[0][1]

    result = {
        'time': datetime.now().strftime("%H:%M:%S"),
        'scenario': scenario["name"],
        'prediction': prediction,
        'confidence': proba,
    }
    results.append(result)

    pred_label = "🚨 ATTACK" if prediction == 1 else "✅ NORMAL"
    alert = "⚠️  ALERT!" if prediction == 1 else ""
    print(f"{result['time']:<10} {scenario['name']:<30} {pred_label:<12} {alert}")

    time.sleep(0.1)

# ── Summary ────────────────────────────────────────────
print("\n" + "="*65)
print("📊 SIMULATION SUMMARY")
print("="*65)

total = len(results)
attacks = sum(1 for r in results if r['prediction'] == 1)
normals = total - attacks

print(f"Total connections analyzed: {total}")
print(f"Normal:                     {normals} ({normals/total*100:.1f}%)")
print(f"Attacks detected:           {attacks} ({attacks/total*100:.1f}%)")

print("\n🔍 Detected Attacks:")
for r in results:
    if r['prediction'] == 1:
        print(f"  • {r['time']} — {r['scenario']} (confidence: {r['confidence']:.2f})")

# Save results
pd.DataFrame(results).to_csv('simulation_results.csv', index=False)
print("\n✅ Results saved to simulation_results.csv")
print("🏭 AI-REASON SOC Simulation Complete!")