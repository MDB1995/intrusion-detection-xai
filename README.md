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

## Setup
```bash
