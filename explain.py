import os
import pandas as pd
from anthropic import Anthropic
from dotenv import load_dotenv
import shap
import matplotlib.pyplot as plt

load_dotenv()
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def get_shap_values(model, X_sample):
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_sample)
    shap_attack = shap_values[:, :, 1]
    return shap_attack

def get_shap_bar_fig(shap_attack, X_sample):
    fig, ax = plt.subplots(figsize=(10, 6))
    shap.summary_plot(shap_attack, X_sample, plot_type="bar", show=False)
    plt.tight_layout()
    return fig

def get_shap_summary_fig(shap_attack, X_sample):
    fig, ax = plt.subplots(figsize=(10, 6))
    shap.summary_plot(shap_attack, X_sample, show=False)
    plt.tight_layout()
    return fig

def get_shap_local_fig(shap_attack, X_sample, sample_idx):
    """Shows SHAP explanation for ONE specific connection"""
    fig, ax = plt.subplots(figsize=(10, 4))
    shap.waterfall_plot(
        shap.Explanation(
            values=shap_attack[sample_idx],
            base_values=0,
            data=X_sample.iloc[sample_idx],
            feature_names=X_sample.columns.tolist()
        ),
        show=False
    )
    plt.tight_layout()
    return fig

def explain_connection(connection, shap_row, prediction, X, sample_idx):
    feature_names = X.columns.tolist()
    shap_series = pd.Series(shap_row, index=feature_names)
    top_features = shap_series.abs().nlargest(3)

    feature_description = ""
    for feat, shap_val in top_features.items():
        actual_val = connection[feat]
        avg_val = X[feat].mean()
        feature_description += f"- {feat}: value={actual_val:.2f}, average={avg_val:.2f}, SHAP impact={shap_val:.4f}\n"

    prompt = f"""
You are a cybersecurity analyst AI assistant.
A network intrusion detection system predicted: {"ATTACK" if prediction == 1 else "NORMAL"}

Top 3 features that influenced this decision:
{feature_description}

Explain in simple English:
1. Why this connection was flagged
2. What each feature means in cybersecurity
3. What type of attack this might be
4. Recommended analyst actions

Be concise and clear.
"""
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )

    return top_features, message.content[0].text