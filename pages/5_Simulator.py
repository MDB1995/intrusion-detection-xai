import streamlit as st
import pandas as pd
import random
import time
import joblib
from datetime import datetime

st.set_page_config(
    page_title="SOC Simulator",
    page_icon="🏭",
    layout="wide"
)

st.title("🏭 Industrial SOC Traffic Simulator")
st.markdown("*Simulating real-time network traffic — inspired by Dizparc SOC environment*")
st.divider()

# ── Load model ─────────────────────────────────────────
@st.cache_resource
def load_model():
    model = joblib.load('model.pkl')
    X = joblib.load('X.pkl')
    return model, X

model, X = load_model()
feature_names = X.columns.tolist()

# ── Traffic generators ──────────────────────────────────
def generate_normal_connection():
    return {
        'duration': random.uniform(0, 10),
        'protocol_type': 1,
        'service': random.randint(10, 30),
        'flag': 9,
        'src_bytes': random.randint(100, 2000),
        'dst_bytes': random.randint(100, 5000),
        'land': 0, 'wrong_fragment': 0, 'urgent': 0,
        'hot': random.randint(0, 5),
        'num_failed_logins': 0, 'logged_in': 1,
        'lnum_compromised': 0, 'lroot_shell': 0,
        'lsu_attempted': 0, 'lnum_root': 0,
        'lnum_file_creations': 0, 'lnum_shells': 0,
        'lnum_access_files': 0, 'lnum_outbound_cmds': 0,
        'is_host_login': 0, 'is_guest_login': 0,
        'count': random.randint(1, 50),
        'srv_count': random.randint(1, 50),
        'serror_rate': 0.0, 'srv_serror_rate': 0.0,
        'rerror_rate': 0.0, 'srv_rerror_rate': 0.0,
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
        'src_bytes': 0, 'dst_bytes': 0, 'logged_in': 0,
        'count': 511, 'srv_count': 511,
        'serror_rate': 1.0, 'srv_serror_rate': 1.0,
        'dst_host_serror_rate': 1.0,
        'dst_host_srv_serror_rate': 1.0,
    })
    return conn

def generate_probe_attack():
    conn = generate_normal_connection()
    conn.update({
        'src_bytes': 0, 'dst_bytes': 0, 'logged_in': 0,
        'count': random.randint(1, 10),
        'rerror_rate': 1.0, 'diff_srv_rate': 1.0,
        'same_srv_rate': 0.0,
    })
    return conn

def generate_modbus_normal():
    conn = generate_normal_connection()
    conn.update({
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
        'src_bytes': 0, 'dst_bytes': 0,
        'serror_rate': random.uniform(0.8, 1.0),
        'dst_host_srv_serror_rate': random.uniform(0.8, 1.0),
    })
    return conn

scenarios = [
    {"name": "Normal Office Traffic",  "generator": generate_normal_connection, "weight": 55, "type": "normal"},
    {"name": "Normal Modbus Traffic",  "generator": generate_modbus_normal,     "weight": 25, "type": "normal"},
    {"name": "DoS/SYN Flood Attack",   "generator": generate_dos_attack,        "weight": 8,  "type": "attack"},
    {"name": "Port Scan Probe",        "generator": generate_probe_attack,      "weight": 7,  "type": "attack"},
    {"name": "Modbus Protocol Attack", "generator": generate_modbus_attack,     "weight": 5,  "type": "attack"},
]
weights = [s["weight"] for s in scenarios]

# ── Sidebar controls ────────────────────────────────────
st.sidebar.title("⚙️ Simulator Controls")
n_connections = st.sidebar.slider("Connections to simulate", 10, 100, 30)
speed = st.sidebar.select_slider(
    "Simulation speed",
    options=["Slow", "Normal", "Fast"],
    value="Normal"
)
speed_map = {"Slow": 0.3, "Normal": 0.1, "Fast": 0.02}

run_btn = st.sidebar.button("▶️ Run Simulation", type="primary")
st.sidebar.divider()
st.sidebar.markdown("**Traffic Mix:**")
st.sidebar.markdown("- 55% Normal office")
st.sidebar.markdown("- 25% Normal Modbus")
st.sidebar.markdown("- 20% Various attacks")

# ── Stats placeholders ──────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
total_placeholder = col1.empty()
normal_placeholder = col2.empty()
attack_placeholder = col3.empty()
rate_placeholder = col4.empty()

total_placeholder.metric("Total Analyzed", "0")
normal_placeholder.metric("✅ Normal", "0")
attack_placeholder.metric("🚨 Attacks", "0")
rate_placeholder.metric("Detection Rate", "0%")

st.divider()

# ── Live feed ───────────────────────────────────────────
st.subheader("📡 Live Connection Feed")
feed_placeholder = st.empty()

# ── Alert section ───────────────────────────────────────
st.subheader("🚨 Security Alerts")
alert_placeholder = st.empty()

# ── Run simulation ──────────────────────────────────────
if run_btn:
    results = []
    alerts = []

    for i in range(n_connections):
        scenario = random.choices(scenarios, weights=weights)[0]
        conn_dict = scenario["generator"]()
        conn_df = pd.DataFrame([conn_dict])[feature_names]

        prediction = model.predict(conn_df)[0]
        proba = model.predict_proba(conn_df)[0][1]

        result = {
            'Time': datetime.now().strftime("%H:%M:%S"),
            'Connection': f"#{i+1:03d}",
            'Scenario': scenario["name"],
            'Status': "🚨 ATTACK" if prediction == 1 else "✅ NORMAL",
            'Confidence': f"{proba:.0%}"
        }
        results.append(result)

        if prediction == 1:
            alerts.append({
                'Time': result['Time'],
                'Type': scenario["name"],
                'Confidence': f"{proba:.0%}"
            })

        # Update metrics
        total = len(results)
        attacks = sum(1 for r in results if "ATTACK" in r['Status'])
        normals = total - attacks
        rate = attacks/total*100 if total > 0 else 0

        total_placeholder.metric("Total Analyzed", total)
        normal_placeholder.metric("✅ Normal", normals)
        attack_placeholder.metric("🚨 Attacks", attacks)
        rate_placeholder.metric("Detection Rate", f"{rate:.1f}%")

        # Update live feed — show last 10
        df_display = pd.DataFrame(results[-10:])
        feed_placeholder.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True
        )

        # Update alerts
        if alerts:
            df_alerts = pd.DataFrame(alerts)
            alert_placeholder.dataframe(
                df_alerts,
                use_container_width=True,
                hide_index=True
            )
        else:
            alert_placeholder.success("✅ No attacks detected yet")

        time.sleep(speed_map[speed])

    # ── Final summary ───────────────────────────────────
    st.divider()
    st.subheader("📊 Simulation Complete!")

    col_l, col_r = st.columns(2)

    with col_l:
        st.success(f"✅ Analyzed {n_connections} connections")
        st.info(f"🚨 Detected {len(alerts)} attacks ({len(alerts)/n_connections*100:.1f}%)")

        if alerts:
            st.markdown("**Attack breakdown:**")
            attack_types = {}
            for a in alerts:
                attack_types[a['Type']] = attack_types.get(a['Type'], 0) + 1
            for t, c in attack_types.items():
                st.markdown(f"- {t}: **{c}** detected")

    with col_r:
        st.markdown("**What this demonstrates:**")
        st.info("""
✅ Real-time network traffic analysis{\n}
✅ Industrial Modbus protocol simulation  
✅ Instant attack detection
✅ Confidence scoring per connection
✅ Automated alert generation

This pipeline is designed to connect to
real Dizparc SOC data streams.
        """)

st.divider()
st.caption("Built for AI-REASON project — Jönköping University × Dizparc Security Solutions")