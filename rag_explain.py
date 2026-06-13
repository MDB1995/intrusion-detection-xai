import chromadb
from sentence_transformers import SentenceTransformer
from anthropic import Anthropic
from dotenv import load_dotenv
import os
import pandas as pd

load_dotenv()
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# ── Initialize RAG components ──────────────────────────
print("Initializing RAG system...")
chroma_client = chromadb.Client()
collection = chroma_client.create_collection("threat_intelligence")
encoder = SentenceTransformer('all-MiniLM-L6-v2')

# ── Load threat intelligence ───────────────────────────
threat_data = [
    {
        "id": "T1498",
        "name": "Network Denial of Service",
        "description": "Adversaries may perform Network DoS attacks to degrade or block availability. SYN floods send large numbers of TCP SYN packets to consume server resources.",
        "detection": "Detect SYN floods by monitoring for high rates of SYN packets without ACK packets. Look for dst_host_srv_serror_rate above 0.5.",
        "mitigation": "Enable SYN cookies, rate limiting, and upstream filtering."
    },
    {
        "id": "T1046",
        "name": "Network Service Scanning",
        "description": "Adversaries may attempt to get a listing of services running on remote hosts using tools like Nmap. Port scanning sends packets to discover open services.",
        "detection": "Monitor for large numbers of connection attempts to multiple ports. Low src_bytes with high connection counts indicate scanning.",
        "mitigation": "Use firewalls to limit port exposure. Monitor and alert on port scan patterns."
    },
    {
        "id": "T1110",
        "name": "Brute Force",
        "description": "Adversaries may use brute force techniques to gain access to accounts including password guessing and credential stuffing.",
        "detection": "Monitor for multiple failed login attempts. Look for high wrong_fragment rates and repeated connection attempts.",
        "mitigation": "Implement account lockout policies and multi-factor authentication."
    },
    {
        "id": "T1071",
        "name": "Application Layer Protocol",
        "description": "Adversaries may communicate using application layer protocols to avoid detection. HTTP, FTP, and SMTP can blend malicious traffic with normal traffic.",
        "detection": "Monitor for unusual patterns in application protocols. Look for abnormal src_bytes and dst_bytes combinations.",
        "mitigation": "Deep packet inspection and application layer filtering."
    },
    {
        "id": "T1078",
        "name": "Valid Accounts",
        "description": "Adversaries may obtain and abuse credentials to gain access. Compromised accounts allow attackers to blend in with normal user activity.",
        "detection": "logged_in=1 with unusual traffic patterns is suspicious. Monitor for unusual login times and access patterns.",
        "mitigation": "Implement privileged account management and monitor account usage."
    },
    {
        "id": "T1595",
        "name": "Active Scanning",
        "description": "Adversaries may execute active reconnaissance scans to gather information. This includes IP scanning and vulnerability scanning.",
        "detection": "Monitor for high rates of ICMP packets and connection attempts across multiple IPs. High ipsweep and portsweep patterns.",
        "mitigation": "Limit external scanning visibility and monitor for scanning patterns."
    },
    {
        "id": "T1499",
        "name": "Endpoint Denial of Service",
        "description": "Adversaries may perform DoS attacks to degrade or block availability of services including flooding attacks that overwhelm target resources.",
        "detection": "Monitor for high count values and srv_count spikes. Neptune and smurf attacks show extremely high connection rates.",
        "mitigation": "Rate limiting, traffic scrubbing, and DDoS protection services."
    },
    {
        "id": "T1133",
        "name": "External Remote Services",
        "description": "Adversaries may use external remote services to gain initial access. VPNs, RDP, and other remote access tools can be exploited.",
        "detection": "Monitor remote access services for unusual login patterns and data transfers.",
        "mitigation": "Limit exposure of remote services and enforce strong authentication."
    }
]

# Store in ChromaDB
for item in threat_data:
    text = f"{item['name']} {item['description']} {item['detection']}"
    embedding = encoder.encode(text).tolist()
    collection.add(
        documents=[text],
        embeddings=[embedding],
        metadatas=[{
            "id": item["id"],
            "name": item["name"],
            "detection": item["detection"],
            "mitigation": item["mitigation"]
        }],
        ids=[item["id"]]
    )

print("RAG system ready!")

def rag_explain(top_features, prediction, connection):
    """
    Takes SHAP top features → searches threat intel → 
    generates enriched Claude explanation
    """
    
    # Build search query from top features
    feature_names = list(top_features.index)
    feature_values = [connection[f] for f in feature_names]
    
    query = f"attack detection features: {' '.join(feature_names)} values: {feature_values}"
    
    # Search ChromaDB
    query_embedding = encoder.encode(query).tolist()
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=2
    )
    
    # Extract threat intelligence
    threat_intel = ""
    for i, metadata in enumerate(results['metadatas'][0]):
        threat_intel += f"""
Threat {i+1}: {metadata['name']} ({metadata['id']})
Detection: {metadata['detection']}
Mitigation: {metadata['mitigation']}
"""
    
    # Build feature description
    feature_description = ""
    for feat, shap_val in top_features.items():
        actual_val = connection[feat]
        feature_description += f"- {feat}: value={actual_val:.2f}, SHAP impact={shap_val:.4f}\n"
    
    # Build enriched prompt
    prompt = f"""
You are a cybersecurity analyst using AI-assisted threat intelligence.

DETECTION RESULT: {"ATTACK" if prediction == 1 else "NORMAL"}

TOP SHAP FEATURES THAT TRIGGERED THIS ALERT:
{feature_description}

RELEVANT MITRE ATT&CK THREAT INTELLIGENCE:
{threat_intel}

Using both the SHAP analysis and MITRE ATT&CK intelligence, provide:
1. Which specific MITRE ATT&CK technique this matches
2. Why these features indicate this attack type
3. Confidence level (High/Medium/Low) and why
4. Specific recommended actions based on MITRE mitigations

Be specific, concise, and actionable.
"""
    
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )
    
    return message.content[0].text, results['metadatas'][0]


# ── Test it ────────────────────────────────────────────
# if __name__ == "__main__":
#     import pandas as pd
    
#     # Simulate SHAP top features from your project
#     top_features = pd.Series({
#         'dst_host_srv_serror_rate': 0.034,
#         'src_bytes': 0.030,
#         'srv_count': 0.035
#     })
    
#     # Simulate connection values
#     connection = {
#         'dst_host_srv_serror_rate': 1.0,
#         'src_bytes': 0.0,
#         'srv_count': 2.0
#     }
    
#     print("\n" + "="*60)
#     print(" RAG-ENHANCED SECURITY ANALYSIS")
#     print("="*60)
    
#     explanation, matched_threats = rag_explain(
#         top_features, 1, connection
#     )
    
#     print("\nMatched MITRE ATT&CK Techniques:")
#     for threat in matched_threats:
#         print(f"  • {threat['name']} ({threat['id']})")
    
#     print("\nAI Analysis with Threat Intelligence:")
#     print("-"*60)
#     print(explanation)
#     print("="*60)