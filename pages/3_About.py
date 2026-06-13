import streamlit as st

st.set_page_config(
    page_title="About",
    page_icon="📖",
    layout="wide"
)

st.title("📖 About This Project")
st.divider()

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
## Network Intrusion Detection with XAI

Built to demonstrate AI-powered security operations
with full explainability — directly aligned with
the **AI-REASON** research project at 
Jönköping University.

## Four Layers:
1. **Detection** — Random Forest (99.97% accuracy)
2. **Explainability** — SHAP TreeExplainer
3. **Communication** — Claude LLM API
4. **Threat Intelligence** — RAG + MITRE ATT&CK

## Dataset:
- KDD Cup 1999 — 494,020 real network connections
- 500 synthetic attack samples via CTGAN
- 41 features per connection
- 22 attack types + normal traffic
""")

with col2:
    st.markdown("""
## Tech Stack:

| Component | Technology |
|---|---|
| ML Model | Random Forest |
| Explainability | SHAP |
| LLM | Claude Sonnet |
| Vector DB | ChromaDB |
| Embeddings | Sentence Transformers |
| Synthetic Data | CTGAN |
| Web Interface | Streamlit |
| Language | Python |

## GitHub:
[github.com/MDB1995/intrusion-detection-xai](https://github.com/MDB1995/intrusion-detection-xai)
""")

st.divider()

st.markdown("""
## Research Context:

This project is a prototype for the **AI-REASON** project:
*AI-assisted Reliable and Explainable Analysis 
for Security OperatioNs*

The system addresses three core AI-REASON goals:
- **Faster decisions** — millisecond ML prediction
- **Reliable assessment** — 99.97% accuracy
- **Explainable outputs** — SHAP + LLM + RAG
""")

st.divider()
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Model Accuracy", "99.97%")
with col2:
    st.metric("Training Connections", "494,520")
with col3:
    st.metric("MITRE ATT&CK Techniques", "8")

st.divider()
st.markdown("**Developer:** Modhubroty Dey Barnile")
st.caption("Built for AI-REASON project demonstration | Jönköping University")