import streamlit as st
import joblib
import pandas as pd
from anthropic import Anthropic
from dotenv import load_dotenv
import os

load_dotenv()

st.set_page_config(
    page_title="Security Analyst Assistant",
    page_icon="💬",
    layout="wide"
)

st.title("💬 Virtual Security Analyst Assistant")
st.markdown("*Ask me anything about the analyzed connection*")
st.divider()

# Check if analysis has been run
if 'analyzed' not in st.session_state:
    st.warning("⚠️ No connection analyzed yet!")
    st.info("👈 Go to the **Analysis** page first and click 'Analyze Connection'")
    st.stop()

# Get data from session state
connection = st.session_state['connection']
prediction = st.session_state['prediction']
top_features = st.session_state['top_features']
llm_explanation = st.session_state['llm_explanation']
matched_threats = st.session_state['matched_threats']
sample_idx = st.session_state['sample_idx']

# Show current analysis summary
if prediction == 1:
    st.sidebar.error("🚨 Current: ATTACK")
else:
    st.sidebar.success("✅ Current: NORMAL")

st.sidebar.markdown("**Top features:**")
for feat, shap_val in top_features.items():
    st.sidebar.caption(f"• {feat}: {connection[feat]:.2f}")

st.sidebar.divider()
st.sidebar.markdown("**Ask me about:**")
st.sidebar.markdown("- Why this was flagged")
st.sidebar.markdown("- What the features mean")
st.sidebar.markdown("- What action to take")
st.sidebar.markdown("- How SHAP works")
st.sidebar.markdown("- What MITRE ATT&CK is")

# Initialize chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Display chat history
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input
if user_question := st.chat_input("Ask anything about network security or this connection..."):
    
    with st.chat_message("user"):
        st.markdown(user_question)
    
    st.session_state.chat_history.append({
        "role": "user",
        "content": user_question
    })
    
    # Build context
    feature_vals = "\n".join([
        f"- {col}: {connection[col]:.2f}"
        for col in ['dst_bytes', 'count', 'src_bytes', 
                    'srv_count', 'logged_in',
                    'dst_host_srv_serror_rate']
    ])
    
    chat_context = f"""
You are a virtual security analyst assistant helping 
analyze network connections.

CURRENT CONNECTION:
Connection #{sample_idx}
Prediction: {"ATTACK" if prediction == 1 else "NORMAL"}

Key feature values:
{feature_vals}

Previous conversation:
{chr(10).join([f"{m['role']}: {m['content']}" 
               for m in st.session_state.chat_history[-4:]])}

User question: {user_question}

Answer concisely and clearly.
Focus on cybersecurity context.
If asked about SHAP, explain it simply.
If asked what to do, give specific actions.
"""
    
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            client = Anthropic(
                api_key=os.getenv("ANTHROPIC_API_KEY")
            )
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=500,
                messages=[{
                    "role": "user",
                    "content": chat_context
                }]
            )
            answer = response.content[0].text
            st.markdown(answer)
    
    st.session_state.chat_history.append({
        "role": "assistant",
        "content": answer
    })

# Clear chat
if st.session_state.chat_history:
    if st.sidebar.button("🗑️ Clear Chat"):
        st.session_state.chat_history = []
        st.rerun()

st.divider()
st.caption("Built for AI-REASON project demonstration | Jönköping University")