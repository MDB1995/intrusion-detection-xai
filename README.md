# intrusion-detection-xai
AI-powered Network Intrusion Detection System with Explainable AI (SHAP) and LLM-generated security reports using Claude API

# Network Intrusion Detection System with Explainable AI

An AI-powered network intrusion detection system that combines 
Machine Learning with Explainable AI (SHAP) and LLM-generated 
security reports.

## Project Overview
This project detects network attacks from traffic data and explains 
WHY each connection was flagged : making AI decisions transparent 
for security analysts.

## Features
- Detects network attacks with 99.97% accuracy
- SHAP explainability shows top features driving each decision
- Claude LLM generates human-readable security reports
- Identifies attack types (DoS, SYN Flood, Probe attacks)
- Actionable recommendations for security analysts

## Dataset
KDD Cup 1999 Network Intrusion Dataset
- 494,020 network connections
- 41 features per connection
- Attack types: DoS, Probe, R2L, U2R

## Tech Stack
- Python
- Scikit-learn (Random Forest Classifier)
- SHAP (Explainable AI)
- Anthropic Claude API (LLM explanation)
- Pandas, NumPy, Matplotlib

## How It Works
1. Load and preprocess network traffic data
2. Train Random Forest classifier
3. Use SHAP to identify top features driving each decision
4. Send SHAP results to Claude API
5. Generate human-readable security report

## Results
| Metric | Score |
|--------|-------|
| Accuracy | 99.97% |
| Precision | 1.00 |
| Recall | 1.00 |
| F1-Score | 1.00 |

## Synthetic Data Generation
- Used CTGAN (Conditional GAN) to generate synthetic 
  rare attack samples
- Addresses class imbalance problem in real networks
- Generated 500 synthetic attack samples as proof of concept

## System Architecture

The system has 4 layers:
1. **Detection Layer** — Random Forest classifier (99.97% accuracy)
2. **Explainability Layer** — SHAP TreeExplainer (global + local)
3. **Communication Layer** — Claude LLM generates security reports
4. **Threat Intelligence Layer** — RAG with ChromaDB + MITRE ATT&CK

## Web Application
Run the interactive demo:
```bash
python main.py        # Train and save model first
streamlit run app.py  # Launch web app
```

The dashboard shows three columns:
- SHAP Analysis with feature importance plots
- LLM-generated security report
- MITRE ATT&CK threat intelligence

## Project Structure
```
intrusion-detection-xai/
├── main.py          # ML pipeline + SHAP
├── explain.py       # Claude LLM explanation
├── rag_explain.py   # RAG + MITRE ATT&CK
├── synthetic.py     # CTGAN synthetic data
├── app.py           # Streamlit web app
└── .gitignore
```
## Setup
```bash
