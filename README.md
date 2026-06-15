# 🛡️ Network Intrusion Detection System with Explainable AI

An AI-powered network intrusion detection system combining Machine Learning, 
Explainable AI (SHAP), LLM-generated security reports, and RAG-based threat 
intelligence — directly inspired by the **AI-REASON project** at Jönköping University.

---

## 🎯 Project Overview

This system addresses three core AI-REASON goals:
- **Faster decisions** — millisecond ML prediction on network connections
- **Reliable assessment** — 99.97% accuracy with precision and recall of 1.00
- **Explainable outputs** — SHAP + LLM + RAG combined analysis

---

## 🏗️ Four Layer Architecture

| Layer | Technology | Purpose |
|---|---|---|
| **Detection** | Random Forest | Classifies normal vs attack traffic |
| **Explainability** | SHAP TreeExplainer | Global + local feature importance |
| **Communication** | Claude LLM API | Human-readable security reports |
| **Threat Intelligence** | RAG + MITRE ATT&CK | Grounded threat analysis |

---

## ✨ Features

- ✅ Network intrusion detection — 99.97% accuracy
- ✅ SHAP explainability — bar chart, beeswarm, waterfall plots
- ✅ Claude LLM security reports — plain English for SOC analysts
- ✅ RAG system — ChromaDB + MITRE ATT&CK framework
- ✅ Synthetic data generation — CTGAN for rare attack samples
- ✅ Anomaly detection — Isolation Forest for unknown attacks
- ✅ Incident priority scoring — CRITICAL/HIGH/MEDIUM/LOW
- ✅ Analyst feedback system — SQLite database for HCT research
- ✅ Multi-page Streamlit web application

---

## 📊 Dataset

- **KDD Cup 1999** — 494,020 real network connections
- **500 synthetic samples** — generated via CTGAN
- **41 features** per connection
- **22 attack types** — DoS, Probe, R2L, U2R

---

## 📁 Project Structure
intrusion-detection-xai/

├── main.py              # ML pipeline + SHAP + RAG

├── explain.py           # SHAP functions + Claude LLM

├── rag_explain.py       # RAG + MITRE ATT&CK system

├── synthetic.py         # CTGAN synthetic data

├── app.py               # Streamlit landing page

├── pages/

│   ├── 1_Analysis.py    # Main analysis dashboard

│   ├── 2_Assistant.py   # AI chatbot

│   ├── 3_About.py       # Project info

│   └── 4_Feedback.py    # Analyst feedback + stats

├── .env                 # API key (not uploaded)

└── .gitignore

---

## 🚀 Setup

Install dependencies:
```bash
pip install pandas numpy scikit-learn shap matplotlib streamlit
pip install anthropic python-dotenv chromadb sentence-transformers ctgan joblib
```

Create `.env` file:
ANTHROPIC_API_KEY=your-key-here

Run pipeline:
```bash
python main.py
```

Launch web app:
```bash
streamlit run app.py
```

---

## 📈 Results

| Metric | Score |
|---|---|
| Accuracy | 99.97% |
| Precision | 1.00 |
| Recall | 1.00 |
| F1-Score | 1.00 |

---

## 🔬 Research Alignment — AI-REASON

| AI-REASON Requirement | My Implementation |
|---|---|
| Behavioral analysis | Trained on 97,277 normal connections |
| Rule-based + AI combined | Random Forest + SHAP + RAG |
| Interpretable AI | SHAP with mathematical guarantees |
| Incident prioritization | CRITICAL/HIGH/MEDIUM/LOW scoring |
| SOC analyst support | LLM plain English reports |
| Human-centered design | Feedback system with SQLite |

---

## 🌐 Live Demo
**[Click here to access the live app](https://intrusion-detection-xai-amadzq2yjuqxpza7z4xuqg.streamlit.app/)**

## 🔮 Future PhD Research Direction

- Industrial protocols — Modbus, DNP3, OPC-UA
- Real-time stream processing with Zeek/Suricata
- Full MITRE ATT&CK API integration (700+ techniques)
- Local LLM for industrial data privacy
- Human evaluation with Dizparc SOC analysts
- XAI faithfulness evaluation framework

---

## 👨‍💻 Developer

**Modhubroty Dey Barnile**
MSc Applied Computer Science · MSc Artificial Intelligence

Built for **AI-REASON project** demonstration — Jönköping University
