import os
import pandas as pd
from anthropic import Anthropic
from dotenv import load_dotenv

# Load API key from .env file
load_dotenv()
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def explain_connection(connection, shap_row, prediction, X, sample_idx):

    feature_names = X.columns.tolist()
    shap_series = pd.Series(shap_row, index=feature_names)
    top_features = shap_series.abs().nlargest(3)

    # Build description of top features for Claude
    feature_description = ""
    for feat, shap_val in top_features.items():
        actual_val = connection[feat]
        avg_val = X[feat].mean()
        feature_description += f"- {feat}: value={actual_val:.2f}, average={avg_val:.2f}, SHAP impact={shap_val:.4f}\n"

    # Build prompt for Claude
    prompt = f"""
You are a cybersecurity analyst AI assistant.

A network intrusion detection system has analyzed a network connection and made this prediction:
Prediction: {"ATTACK" if prediction == 1 else "NORMAL"}

The top 3 features that influenced this decision are:
{feature_description}

Please explain in simple English:
1. Why this connection was flagged as {"an attack" if prediction == 1 else "normal"}
2. What each feature means in cybersecurity terms
3. What type of attack this might be
4. What action should a security analyst take

Keep the explanation clear and concise.
"""

    print("\n" + "="*60)
    print("SECURITY ANALYSIS REPORT")
    print("="*60)
    print(f"\nConnection #{sample_idx + 1} Analysis:")
    print(f"   Prediction: {'ATTACK' if prediction == 1 else '✅ NORMAL'}")
    print(f"\nTop 3 features that triggered this decision:")
    print(feature_description)

    print("AI Explanation:")
    print("-"*60)

    # Call Claude API
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    print(message.content[0].text)
    print("="*60)