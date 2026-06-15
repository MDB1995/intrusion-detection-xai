import streamlit as st
import joblib
import pandas as pd

st.set_page_config(
    page_title="Network Intrusion Detection System",
    page_icon="🛡️",
    layout="wide"
)

# ── Train model if needed ──────────────────────────────
@st.cache_resource
def initialize():
    from train import train_and_save
    train_and_save()
    return True

with st.spinner("⏳ Initializing system... please wait..."):
    initialize()

# ── Title ──────────────────────────────────────────────
st.title("🛡️ Network Intrusion Detection System")
st.markdown("*Explainable AI for Security Operations — Inspired by AI-REASON project*")
st.divider()

# Key metrics
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Model Accuracy", "99.97%")
with col2:
    st.metric("Training Data", "494,520")
with col3:
    st.metric("Features", "41")
with col4:
    st.metric("MITRE Techniques", "8")

st.divider()

st.markdown("""
## 🚀 How to use:

👈 **Use the sidebar** to navigate between pages:

| Page | What it does |
|---|---|
| **Analysis** | Select and analyze network connections |
| **Assistant** | Chat with AI security analyst |
| **Feedback** | Rate AI explanations |
| **Simulator** | Live SOC traffic simulation |
| **About** | Learn about the project |
""")

st.info("💡 Start by going to the **Analysis** page and clicking 'Analyze Connection'!")

st.divider()
st.caption("Built for AI-REASON project demonstration | Jönköping University")