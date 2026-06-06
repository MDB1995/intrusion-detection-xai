import streamlit as st
import pandas as pd
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import shap
import matplotlib.pyplot as plt
from explain import explain_connection
import joblib
import sys
from io import StringIO

# ── Page config ───────────────────────────────────────
st.set_page_config(
    page_title="Network Intrusion Detection System",
    page_icon="🛡️",
    layout="wide"
)

# ── Title ─────────────────────────────────────────────
st.title("AI-Powered Network Intrusion Detection System")
st.markdown("*Explainable AI for Security Operations — Inspired by AI-REASON project*")
st.divider()

# ── Load and train model ───────────────────────────────
@st.cache_resource
def load_model():
    model = joblib.load('model.pkl')
    X_test = joblib.load('X_test.pkl')
    X = joblib.load('X.pkl')
    return model, X_test, X

model, X_test, X = load_model()

# ── Sidebar ────────────────────────────────────────────
st.sidebar.title("Controls")
st.sidebar.markdown("Select a connection to analyze:")

sample_idx = st.sidebar.slider(
    "Connection Number", 
    min_value=0, 
    max_value=100, 
    value=0
)

analyze_btn = st.sidebar.button("Analyze Connection", type="primary")

# ── Main content ───────────────────────────────────────
X_sample = X_test.sample(101, random_state=42)

col1, col2 = st.columns(2)

with col1:
    st.subheader(" Connection Details")
    connection = X_sample.iloc[sample_idx]
    st.dataframe(
        connection.to_frame().rename(columns={connection.name: "Value"}),
        height=400
    )

with col2:
    st.subheader("Model Prediction")
    prediction = model.predict([connection])[0]
    
    if prediction == 1:
        st.error("ATTACK DETECTED!")
        st.metric("Threat Level", "HIGH", " Immediate action required")
    else:
        st.success("NORMAL TRAFFIC")
        st.metric("Threat Level", "LOW", " No action required")
    
    # Accuracy metric
    st.metric("Model Accuracy", "99.97%", "Trained on 494,020 connections")

st.divider()

# ── SHAP Analysis ──────────────────────────────────────
if analyze_btn:
    st.subheader("SHAP Explainability Analysis")
    
    with st.spinner("Calculating SHAP values..."):
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X_sample)
        shap_attack = shap_values[:, :, 1]
        shap_row = shap_attack[sample_idx]
    
    # SHAP bar plot
    fig, ax = plt.subplots(figsize=(10, 6))
    shap.summary_plot(
        shap_attack, X_sample, 
        plot_type="bar", show=False
    )
    st.pyplot(fig)
    plt.close()

    st.divider()

    # ── AI Explanation ─────────────────────────────────
    st.subheader("AI Security Report")
    
    with st.spinner("Generating AI explanation..."):
        # Get top 3 features
        feature_names = X.columns.tolist()
        shap_series = pd.Series(shap_row, index=feature_names)
        top_features = shap_series.abs().nlargest(3)
        
        # Display top features
        st.markdown("**Top 3 features that triggered this decision:**")
        for feat, shap_val in top_features.items():
            actual_val = connection[feat]
            avg_val = X[feat].mean()
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.metric(feat, f"{actual_val:.2f}")
            with col_b:
                st.metric("Average", f"{avg_val:.2f}")
            with col_c:
                st.metric("SHAP Impact", f"{shap_val:.4f}")
        
        st.divider()
        
        # Capture the explanation
        top_features, ai_explanation = explain_connection(connection, shap_row, prediction, X, sample_idx)

        # Display Claude explanation
        st.markdown("**🤖 Claude AI Analysis:**")
        st.markdown(ai_explanation)

st.divider()
st.caption("Built for AI-REASON project demonstration | Jönköping University")