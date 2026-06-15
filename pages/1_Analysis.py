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



# Page config
st.set_page_config(
    page_title="Network Intrusion Detection System",
    page_icon="🛡️",
    layout="wide"
)

# Title
st.title("Network Intrusion Detection System")
st.markdown("*Explainable AI for Security Operations — Inspired by AI-REASON project*")
st.divider()

# Load and train model
@st.cache_resource
def load_model():
    model = joblib.load('model.pkl')
    X_test = joblib.load('X_test.pkl')
    X = joblib.load('X.pkl')
    return model, X_test, X

model, X_test, X = load_model()

# Sidebar 
st.sidebar.title("Controls")
st.sidebar.markdown("Select a connection to analyze:")

# Remember slider position
default_idx = st.session_state.get('sample_idx', 0)

sample_idx = st.sidebar.slider(
    "Connection Number", 
    min_value=0, 
    max_value=100, 
    value=default_idx
)

# Save slider position immediately
st.session_state['sample_idx'] = sample_idx

analyze_btn = st.sidebar.button("Analyze Connection", type="primary")

# Add reset button
# Only rerun if button clicked OR
# analyzed before with SAME connection
already_analyzed = (
    'analyzed' in st.session_state and 
    st.session_state.get('last_analyzed_idx') == sample_idx
)

if analyze_btn or already_analyzed:
    if st.sidebar.button("🔄 Reset Analysis"):
        for key in ['analyzed', 'connection', 'prediction', 
                    'top_features', 'llm_explanation', 
                    'rag_explanation', 'matched_threats',
                    'sample_idx', 'shap_attack', 
                    'shap_row', 'X_sample']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

# Main content
X_sample = X_test.sample(101, random_state=42)

col1, col2 = st.columns(2)

with col1:
    st.subheader(" Connection Details")
    connection = X_sample.iloc[sample_idx]
    # Update session state when slider changes
    if 'analyzed' in st.session_state:
        st.session_state['sample_idx'] = sample_idx
        st.session_state['connection'] = connection
        prediction = model.predict([connection])[0]
        st.session_state['prediction'] = prediction
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

# SHAP Analysis 
if analyze_btn or 'analyzed' in st.session_state:
    with st.spinner("Running full analysis..."):
    
    # Calculate SHAP
        from explain import get_shap_values, explain_connection
        from rag_explain import rag_explain
        
        shap_attack = get_shap_values(model, X_sample)
        shap_row = shap_attack[sample_idx]
        
        # Get top features
        feature_names = X.columns.tolist()
        shap_series = pd.Series(shap_row, index=feature_names)
        top_features = shap_series.abs().nlargest(3)
        
        # Get LLM explanation
        _, llm_explanation = explain_connection(
            connection, shap_row, prediction, X, sample_idx
        )
        
        # Get RAG explanation
        rag_explanation, matched_threats = rag_explain(
            top_features, prediction, connection
        )

        # ── Save to session state ──────────────────────────
        st.session_state['analyzed'] = True
        st.session_state['last_analyzed_idx'] = sample_idx
        st.session_state['connection'] = connection
        st.session_state['prediction'] = prediction
        st.session_state['top_features'] = top_features
        st.session_state['llm_explanation'] = llm_explanation
        st.session_state['rag_explanation'] = rag_explanation
        st.session_state['matched_threats'] = matched_threats
        st.session_state['sample_idx'] = sample_idx
        st.session_state['shap_attack'] = shap_attack
        st.session_state['shap_row'] = shap_row
        st.session_state['X_sample'] = X_sample
    
    # Three column layout
    st.subheader("Complete Security Analysis")
    st.markdown("""
    <style>
        [data-testid="column"] {
            border: 1px solid #ddd;
            border-radius: 10px;
            padding: 15px;
            background-color: #f9f9f9;
        }
    </style>
""", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    
    # Column 1: SHAP Analysis
    with col1:
        st.markdown("### SHAP Analysis")
        st.markdown("**Top 3 features:**")
        for feat, shap_val in top_features.items():
            actual_val = connection[feat]
            avg_val = X[feat].mean()
            st.metric(
                label=feat,
                value=f"{actual_val:.2f}",
                delta=f"avg: {avg_val:.2f}"
            )
            st.caption(f"SHAP impact: {shap_val:.4f}")
        
        st.divider()
        st.markdown("**SHAP Bar Chart:**")
        from explain import get_shap_bar_fig, get_shap_summary_fig
        fig1 = get_shap_bar_fig(shap_attack, X_sample)
        st.pyplot(fig1)
        
        st.markdown("**SHAP Summary Plot:**")
        fig2 = get_shap_summary_fig(shap_attack, X_sample)
        st.pyplot(fig2)

        st.markdown("**This Connection Specifically:**")
        from explain import get_shap_local_fig
        fig3 = get_shap_local_fig(shap_attack, X_sample, sample_idx)
        st.pyplot(fig3)

        st.divider()
        st.markdown("**SHAP Explanation:**")
        
        # Generate natural language explanation for SHAP
        top_feat_name = list(top_features.index)[0]
        top_feat_val = connection[top_feat_name]
        top_feat_avg = X[top_feat_name].mean()
        top_shap = list(top_features.values)[0]
        
        direction = "higher" if top_feat_val > top_feat_avg else "lower"
        
        st.info(f"""
**Global Explanation (Bar Chart):**
The bar chart shows the most important features 
across all 100 analyzed connections. 
**{top_feat_name}** has the highest average impact 
on attack detection.

**Local Explanation (Beeswarm):**
Each dot represents one connection.
🔴 Red = high feature value → pushes toward Attack
🔵 Blue = low feature value → pushes toward Normal

**For this specific connection:**
The top trigger was **{top_feat_name}** with value 
**{top_feat_val:.2f}** — which is {direction} than 
the average of **{top_feat_avg:.2f}**. 
This pushed the model toward 
**{'ATTACK' if prediction == 1 else 'NORMAL'}** 
with SHAP impact of **{top_shap:.4f}**.
        """)

    # Column 2: LLM Explanation
    with col2:
        st.markdown("### LLM Analysis")
        st.markdown(llm_explanation)

    # Column 3: RAG Threat Intelligence
    with col3:
        st.markdown("### MITRE ATT&CK Intel")
        st.markdown("**Matched techniques:**")
        for threat in matched_threats:
            st.error(f"{threat['name']}")
            st.caption(f"ID: {threat['id']}")
        
        st.divider()
        st.markdown("**RAG Analysis:**")
        st.markdown(rag_explanation)

    st.divider()

    # ── Final Aggregated Summary ───────────────────────────
    st.subheader("Final Verdict & Recommended Action")

    with st.spinner("Aggregating all analysis..."):
        
        # Build aggregated prompt
        feature_summary = "\n".join([
            f"- {feat}: value={connection[feat]:.2f}, SHAP impact={shap_val:.4f}"
            for feat, shap_val in top_features.items()
        ])
        
        mitre_summary = "\n".join([
            f"- {t['name']} ({t['id']}): {t['mitigation']}"
            for t in matched_threats
        ])
        
        aggregation_prompt = f"""
    You are a senior cybersecurity analyst making a final decision.

    You have received THREE independent analyses. Reference each one explicitly:

    1. SHAP ANALYSIS found these top triggers:
    {chr(10).join([f"   • {feat}: value={connection[feat]:.2f} (SHAP impact={shap_val:.4f})" for feat, shap_val in top_features.items()])}

    2. LLM ANALYSIS identified:
    {llm_explanation[:200]}...

    3. RAG THREAT INTELLIGENCE matched:
    {chr(10).join([f"   • {t['name']} ({t['id']})" for t in matched_threats])}

    Write your final verdict in this EXACT format:

    ## SHAP Says:
    One sentence summarizing what the top SHAP features indicate

    ## LLM Says:
    One sentence summarizing the LLM attack identification

    ## RAG Says:
    One sentence summarizing the MITRE ATT&CK match

    ## Final Verdict:
    - **Attack Type:** (specific name)
    - **Confidence:** High/Medium/Low
    - **Reason:** One sentence combining all three analyses

    ## Immediate Action:
    One clear directive — what to do RIGHT NOW

    ## 30-Minute Plan:
    - Point 1
    - Point 2
    - Point 3
    """
        
        from anthropic import Anthropic
        from dotenv import load_dotenv
        import os
        load_dotenv()
        
        final_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
        final_message = final_client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=400,
            messages=[{"role": "user", "content": aggregation_prompt}]
        )
        
        # Display with clear visual
        if prediction == 1:
            st.error("THREAT CONFIRMED")
        else:
            st.success("NO THREAT DETECTED")
        
        st.markdown(final_message.content[0].text)
        
        # Action button
        st.warning(" Take action now based on the recommendations above!")

    st.divider()



st.divider()
st.caption("Built for AI-REASON project demonstration | Jönköping University")