import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import os
import datetime

st.set_page_config(
    page_title="Analyst Feedback",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Analyst Feedback")
st.markdown("*Human-Centred Technology — AI-REASON Research*")
st.divider()

# Database path
db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'feedback.db')

def init_db():
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS analyst_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            connection_id INTEGER,
            prediction TEXT,
            helpful TEXT,
            comment TEXT,
            attack_type TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_feedback(connection_id, prediction, helpful, comment, attack_type):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''
        INSERT INTO analyst_feedback 
        (timestamp, connection_id, prediction, helpful, comment, attack_type)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        datetime.datetime.now().isoformat(),
        connection_id,
        "ATTACK" if prediction == 1 else "NORMAL",
        helpful, comment, attack_type
    ))
    conn.commit()
    conn.close()

init_db()

# Check if analysis exists
if 'analyzed' not in st.session_state:
    st.warning("⚠️ No connection analyzed yet!")
    st.info("👈 Go to **Analysis** page first and click 'Analyze Connection'")
    
    # Still show historical feedback stats
    st.divider()
    st.subheader("📋 Historical Feedback")
else:
    # Show current analysis summary
    connection = st.session_state['connection']
    prediction = st.session_state['prediction']
    top_features = st.session_state['top_features']
    matched_threats = st.session_state['matched_threats']
    sample_idx = st.session_state['sample_idx']
    llm_explanation = st.session_state['llm_explanation']

    # Current analysis summary
    st.subheader("📡 Current Analysis Summary")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if prediction == 1:
            st.error("🚨 ATTACK DETECTED")
        else:
            st.success("✅ NORMAL TRAFFIC")
    
    with col2:
        st.markdown("**Top SHAP features:**")
        for feat, shap_val in top_features.items():
            st.caption(f"• {feat}: {connection[feat]:.2f}")
    
    with col3:
        st.markdown("**Matched MITRE:**")
        for threat in matched_threats:
            st.caption(f"• {threat['name']}")

    st.divider()

    # Feedback section
    st.subheader("📝 Rate This Explanation")
    st.markdown("*Your feedback helps improve AI-REASON*")

    helpful = None
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        if st.button("✅ Very helpful", use_container_width=True):
            helpful = "helpful"
            st.session_state['helpful'] = helpful
    with col_b:
        if st.button("⚠️ Partially helpful", use_container_width=True):
            helpful = "partial"
            st.session_state['helpful'] = helpful
    with col_c:
        if st.button("❌ Not helpful", use_container_width=True):
            helpful = "not_helpful"
            st.session_state['helpful'] = helpful

    # Get helpful from session if button was clicked
    if 'helpful' in st.session_state:
        helpful = st.session_state['helpful']

    comment = st.text_area(
        "Comments (optional):",
        placeholder="Was the attack type correct? Were the actions appropriate?",
        height=80
    )

    if st.button("Submit Feedback", type="primary"):
        if helpful:
            save_feedback(
                connection_id=sample_idx,
                prediction=prediction,
                helpful=helpful,
                comment=comment,
                attack_type=matched_threats[0]['name'] if matched_threats else "Unknown"
            )
            st.success("✅ Feedback saved! Thank you.")
            if 'helpful' in st.session_state:
                del st.session_state['helpful']
        else:
            st.warning("Please select a helpfulness rating first!")

    st.divider()

# Always show stats
st.subheader("📊 Feedback Statistics")

try:
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query(
        "SELECT * FROM analyst_feedback ORDER BY timestamp DESC",
        conn
    )
    conn.close()

    if df.empty:
        st.info("No feedback collected yet.")
    else:
        # Metrics
        total = len(df)
        helpful_count = len(df[df['helpful'] == 'helpful'])
        partial_count = len(df[df['helpful'] == 'partial'])
        not_helpful_count = len(df[df['helpful'] == 'not_helpful'])

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Feedback", total)
        with col2:
            st.metric("✅ Helpful", helpful_count)
        with col3:
            st.metric("⚠️ Partial", partial_count)
        with col4:
            st.metric("❌ Not Helpful", not_helpful_count)

        st.divider()

        col_left, col_right = st.columns(2)

        with col_left:
            # Pie chart
            st.subheader("Distribution")
            labels = ['Helpful', 'Partial', 'Not Helpful']
            values = [helpful_count, partial_count, not_helpful_count]
            colors = ["16A34A", "EA580C", "DC2626"]
            
            non_zero = [(l, v, c) for l, v, c in zip(labels, values, colors) if v > 0]
            if non_zero:
                fig, ax = plt.subplots(figsize=(5, 4))
                ax.pie(
                    [v for _, v, _ in non_zero],
                    labels=[l for l, _, _ in non_zero],
                    colors=["#" + c for _, _, c in non_zero],
                    autopct='%1.1f%%', startangle=90
                )
                st.pyplot(fig)
                plt.close()

        with col_right:
            # Research insight
            st.subheader("Research Insight")
            helpfulness_rate = helpful_count / total * 100 if total > 0 else 0
            st.info(f"""
**XAI Effectiveness Score: {helpfulness_rate:.1f}%**

Target for AI-REASON: >80%

This directly measures whether AI explanations 
help SOC analysts make better decisions — 
the core research question of the 
Human-Centred Technology group.
            """)

        st.divider()
        st.subheader("Recent Feedback")
        st.dataframe(
            df[['timestamp', 'connection_id', 'prediction', 
                'helpful', 'attack_type', 'comment']].head(10),
            use_container_width=True
        )

except Exception as e:
    st.error(f"Database error: {e}")

st.divider()
st.caption("Built for AI-REASON project — Jönköping University")