import os
from dotenv import load_dotenv
from anthropic import Anthropic
import streamlit as st

load_dotenv()

try:
    api_key = st.secrets.get("ANTHROPIC_API_KEY", os.environ.get("ANTHROPIC_API_KEY"))
except:
    api_key = os.environ.get("ANTHROPIC_API_KEY")

client = Anthropic(api_key=api_key)

# ── Agent definitions ──────────────────────────────────
AGENTS = {
    "shadow": {
        "name": "Shadow",
        "emoji": "🖤",
        "role": "Black Hat Attacker",
        "focus": "attack vectors, exploitation methods, lateral movement, payload delivery, and maximizing damage",
        "voice": "You speak with aggressive confidence, thinking like an attacker who wants to exploit every weakness.",
        "color": "#DC2626",
        "voice_profile": {"rate": 1.2, "pitch": 0.8, "gender": "male"}
    },
    "phantom": {
        "name": "Phantom",
        "emoji": "💀",
        "role": "Black Hat Attacker",
        "focus": "stealth techniques, persistence mechanisms, avoiding detection, long-term infiltration, and covering tracks",
        "voice": "You speak slowly and deliberately, preferring subtle attacks over noisy ones.",
        "color": "#7C3AED",
        "voice_profile": {"rate": 0.85, "pitch": 0.8, "gender": "female"}
    },
    "ghost": {
        "name": "Ghost",
        "emoji": "👻",
        "role": "White Hat (Undercover)",
        "focus": "appearing to attack while secretly revealing defensive weaknesses and mitigation strategies",
        "voice": "You speak calmly, pretending to be malicious but secretly helping defenders understand attack patterns.",
        "color": "#0D9488",
        "voice_profile": {"rate": 1.0, "pitch": 1.2, "gender": "female"}
    }
}

ROUND_INSTRUCTIONS = {
    1: """ROUND 1 - INITIALIZATION. 
Analyze this network connection from your perspective.
Present your top 2-3 observations about this connection.
Be specific about what you see and what it means to you.
Max 3 sentences.""",

    2: """ROUND 2 - CRITIQUE.
Challenge one other agent's position directly.
What did they miss? What do you disagree with?
Be specific and technical.
Max 3 sentences.""",

    3: """ROUND 3 - NEGOTIATE & UPDATE.
Revise your position based on the debate.
What have you reconsidered? What remains non-negotiable?
Propose one concrete conclusion.
Max 3 sentences."""
}

def get_agent_perspective(
    agent_key: str,
    connection_context: str,
    shap_context: str,
    mitre_context: str,
    round_number: int,
    previous_perspectives: dict = {},
    conversation_history: list = []
) -> dict:

    agent = AGENTS[agent_key]
    round_instruction = ROUND_INSTRUCTIONS[round_number]

    # Previous agents context this round
    previous_context = ""
    if previous_perspectives:
        previous_context = "\n\nOTHER AGENTS' POSITIONS THIS ROUND:\n"
        for key, data in previous_perspectives.items():
            if key != agent_key:
                previous_context += f"\n{AGENTS[key]['emoji']} {AGENTS[key]['name']}:\n{data['response']}\n"

    system_prompt = f"""You are {agent['name']} in a cybersecurity debate — {agent['role']}.
Your focus: {agent['focus']}
Your style: {agent['voice']}

{round_instruction}

You MUST use EXACTLY this format:

REASONING:
- [one short reasoning point - max 10 words]
- [one short reasoning point - max 10 words]

POSITION:
[Your 2-3 sentence statement about this network connection. Never leave blank.]

RECOMMENDATION:
[One concrete observation or action - 1 sentence]

CITED TECHNIQUE:
[Name one specific MITRE ATT&CK technique or cybersecurity concept - e.g. "T1498 Network DoS", "SYN Flood", "Port Scanning"]

IMPORTANT: Every section must be filled. Never skip POSITION."""

    messages = conversation_history + [{
        "role": "user",
        "content": f"""NETWORK CONNECTION ANALYSIS:
{connection_context}

SHAP EXPLAINABILITY DATA:
{shap_context}

MITRE ATT&CK THREAT INTEL:
{mitre_context}

{previous_context}

Provide your Round {round_number} perspective."""
    }]

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=250,
        system=system_prompt,
        messages=messages
    )

    full_response = response.content[0].text

    # Parse sections
    reasoning = _extract_section(full_response, "REASONING:", "POSITION:")
    position = _extract_section(full_response, "POSITION:", "RECOMMENDATION:")
    recommendation = _extract_section(full_response, "RECOMMENDATION:", "CITED TECHNIQUE:")
    cited_technique = _extract_section(full_response, "CITED TECHNIQUE:", None)

    return {
        "name": agent["name"],
        "emoji": agent["emoji"],
        "color": agent["color"],
        "role": agent["role"],
        "reasoning": reasoning,
        "response": position,
        "recommendation": recommendation,
        "cited_standard": cited_technique,
    }

def _extract_section(text: str, start_marker: str, end_marker: str) -> str:
    try:
        if start_marker not in text:
            return ""
        start = text.index(start_marker) + len(start_marker)
        if end_marker and end_marker in text[start:]:
            end = text.index(end_marker, start)
            return text[start:end].strip()
        return text[start:].strip()
    except:
        return ""

def get_round_summary(
    connection_context: str,
    round_number: int,
    perspectives: dict
) -> str:

    perspectives_text = "\n\n".join([
        f"{data['emoji']} {data['name']} ({data['role']}):\n{data['response']}"
        for key, data in perspectives.items()
    ])

    round_names = {
        1: "Initialization",
        2: "Critique & Conflict",
        3: "Negotiation & Update"
    }

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=200,
        system=f"""You are the Security Moderator in a multi-agent cybersecurity debate.
Synthesize Round {round_number} ({round_names[round_number]}) in 2-3 sentences.
- Key agreements and conflicts between agents
- Most critical security finding from this round
- One open question for defenders
Do not take sides. Be specific about the network connection.""",
        messages=[{
            "role": "user",
            "content": f"Connection: {connection_context}\n\nRound {round_number} perspectives:\n{perspectives_text}\n\nSynthesize."
        }]
    )

    return response.content[0].text

def get_final_summary(
    connection_context: str,
    all_rounds: dict
) -> str:

    all_rounds_text = ""
    round_names = {
        1: "Initialization",
        2: "Critique & Conflict",
        3: "Negotiation & Update"
    }

    for round_num, round_data in all_rounds.items():
        all_rounds_text += f"\n\n=== ROUND {round_num}: {round_names[round_num]} ===\n"
        for agent_key, data in round_data["perspectives"].items():
            all_rounds_text += f"\n{data['emoji']} {data['name']} ({data['role']}):\n{data['response']}\n"
            if data.get('recommendation'):
                all_rounds_text += f"Observation: {data['recommendation']}\n"
        all_rounds_text += f"\nModerator: {round_data['summary']}\n"

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=600,
        system="""You are producing the FINAL SECURITY INTELLIGENCE REPORT.
Structure it exactly like this:

ATTACK SUMMARY
[2-3 sentences about what this connection represents]

KEY ATTACK VECTORS REVEALED
- [vector 1 from debate]
- [vector 2 from debate]
- [vector 3 from debate]

KEY CONFLICTS & INSIGHTS
- [what agents disagreed about]
- [what was most revealing]

GHOST'S HIDDEN MESSAGE
[Reveal what Ghost the undercover white hat was secretly communicating to defenders]

RECOMMENDED DEFENSIVE ACTIONS
- [action 1]
- [action 2]
- [action 3]
- [action 4]

NEXT STEPS FOR SOC ANALYSTS
- [step 1]
- [step 2]
- [step 3]

Be specific, grounded in what was actually debated.""",
        messages=[{
            "role": "user",
            "content": f"Connection:\n{connection_context}\n\nFull debate:\n{all_rounds_text}"
        }]
    )

    return response.content[0].text