import streamlit as st
import json
import os
import joblib
from cyber_agents import get_agent_perspective, get_round_summary, get_final_summary, AGENTS

st.set_page_config(
    page_title="Security Debate",
    page_icon="⚔️",
    layout="wide"
)

st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; }
    .agent-box {
        background: #ffffff;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
        border-left: 4px solid #ddd;
        box-shadow: 0 1px 4px rgba(0,0,0,0.08);
    }
    .agent-name {
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 8px;
    }
    .round-header {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        font-weight: 700;
        margin: 24px 0 12px;
    }
    .citation-box {
        margin-top: 8px;
        font-size: 0.72rem;
        color: #666;
        background: #f5f5f5;
        padding: 5px 10px;
        border-radius: 6px;
        border-left: 3px solid #ccc;
    }
</style>
""", unsafe_allow_html=True)

# ── Session State ──────────────────────────────────────
defaults = {
    'debate_rounds': {},
    'debate_current_round': 1,
    'debate_spoken_rounds': [],
    'debate_final_summary': '',
    'debate_recommendations': [],
    'debate_initialized': False,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

ROUND_NAMES = {
    1: "① Initialization",
    2: "② Critique & Conflict",
    3: "③ Negotiation & Update"
}
ROUND_COLORS = {1: "#4A90D9", 2: "#E74C3C", 3: "#5CB85C"}

VOICE_PROFILES = {
    "shadow":  {"rate": 1.2,  "pitch": 0.8,  "gender": "male"},
    "phantom": {"rate": 0.85, "pitch": 0.6,  "gender": "male"},
    "ghost":   {"rate": 1.0,  "pitch": 1.2,  "gender": "female"},
}

# ── Check analysis exists ──────────────────────────────
if 'analyzed' not in st.session_state:
    st.warning("⚠️ No connection analyzed yet!")
    st.info("👈 Go to **Analysis** page first and click 'Analyze Connection'")
    st.stop()

connection = st.session_state['connection']
prediction = st.session_state['prediction']
top_features = st.session_state['top_features']
matched_threats = st.session_state['matched_threats']
llm_explanation = st.session_state.get('llm_explanation', '')

# ── Build context strings ──────────────────────────────
connection_context = f"""
Prediction: {"ATTACK" if prediction == 1 else "NORMAL"}
Top features: {', '.join([f"{f}={connection[f]:.2f}" for f in list(top_features.index)])}
"""

shap_context = "\n".join([
    f"- {feat}: value={connection[feat]:.2f}, SHAP impact={val:.4f}"
    for feat, val in top_features.items()
])

mitre_context = "\n".join([
    f"- {t['name']} ({t['id']}): {t.get('detection', '')}"
    for t in matched_threats
])

# ── Render static agent ────────────────────────────────
def render_agent_static(agent):
    response = agent.get('response', '').strip()
    if not response:
        return
    cited = agent.get('cited_standard', '').strip()
    citation_html = f"<div class='citation-box'>🎯 {cited}</div>" if cited else ""
    st.markdown(f"""
<div class='agent-box' style='border-left-color:{agent["color"]}'>
    <div class='agent-name' style='color:{agent["color"]}'>{agent["emoji"]} {agent["name"]} — {agent.get("role","")}</div>
    <div style='font-size:0.88rem;line-height:1.75;color:#1a1a1a;'>{response}</div>
    {citation_html}
</div>""", unsafe_allow_html=True)
    reasoning = agent.get('reasoning', '').strip()
    if reasoning:
        with st.expander(f"🧠 {agent['name']} — XAI Reasoning"):
            st.markdown(reasoning)

# ── Render new round with typewriter + voice ───────────
def render_round_with_typewriter(perspectives, round_num):
    agents_data = []
    for agent_key, agent in perspectives.items():
        response = agent.get('response', '').strip()
        if not response:
            continue
        profile = VOICE_PROFILES.get(agent_key, {"rate": 1.0, "pitch": 1.0, "gender": "male"})
        safe_text = (response
            .replace("\\", " ")
            .replace("'", " ")
            .replace('"', ' ')
            .replace("\n", " ")
            .replace("\r", " "))
        word_count = len(safe_text.split())
        speech_ms = int((word_count / (profile['rate'] * 2.5)) * 1000)
        char_delay = max(12, min(35, speech_ms // max(len(safe_text), 1)))
        cited = agent.get('cited_standard', '').strip()
        agents_data.append({
            "key": agent_key,
            "name": agent.get('name', ''),
            "emoji": agent.get('emoji', ''),
            "role": agent.get('role', ''),
            "color": agent.get('color', '#888'),
            "text": safe_text,
            "rate": profile['rate'],
            "pitch": profile['pitch'],
            "gender": profile['gender'],
            "charDelay": char_delay,
            "citation": cited
        })

    if not agents_data:
        return

    containers_html = f"""
<div style='margin-bottom:14px;'>
    <button id='mute_btn_{round_num}' onclick='toggleMute_{round_num}()'
        style='padding:5px 18px; border:1px solid #ddd; border-radius:20px;
               background:#fff; cursor:pointer; font-size:0.78rem;
               font-weight:600; color:#555;'>
        🔇 Mute
    </button>
</div>"""

    for a in agents_data:
        uid = f"{a['key']}_{round_num}"
        citation_html = f"<div class='citation-box'>🎯 {a['citation']}</div>" if a['citation'] else ""
        containers_html += f"""
<div class='agent-box' style='border-left-color:{a["color"]}; min-height:60px;'>
    <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;'>
        <div class='agent-name' style='color:{a["color"]}; margin-bottom:0;'>
            {a["emoji"]} {a["name"]} — {a["role"]}
        </div>
        <span id='status_{uid}' style='font-size:0.7rem; color:#aaa;'></span>
    </div>
    <div style='font-size:0.88rem; line-height:1.75; color:#1a1a1a;' id='text_{uid}'></div>
    {citation_html}
</div>"""

    agents_json = json.dumps(agents_data)

    html = f"""
{containers_html}

<script>
(function() {{
    var RN = {round_num};
    var agents = {agents_json};
    var isMuted = false;
    var currentIndex = 0;
    var activeUtterance = null;

    function pickVoice(gender) {{
        var voices = window.speechSynthesis.getVoices();
        var en = voices.filter(function(v) {{ return v.lang.startsWith('en'); }});
        var picked = null;
        if (gender === 'female') {{
            picked = en.find(function(v) {{
                return v.name.includes('Zira') || v.name.includes('Samantha') ||
                       v.name.includes('Karen') || v.name.includes('Victoria') ||
                       v.name.toLowerCase().includes('female');
            }});
            if (!picked) picked = en[0];
        }} else {{
            picked = en.find(function(v) {{
                return v.name.includes('David') || v.name.includes('Daniel') ||
                       v.name.includes('Mark') || v.name.toLowerCase().includes('male');
            }});
            if (!picked) picked = en[1] || en[0];
        }}
        return picked;
    }}

    function runAgent(index) {{
        if (index >= agents.length) return;
        currentIndex = index;
        var agent = agents[index];
        var uid = agent.key + '_' + RN;
        var el = document.getElementById('text_' + uid);
        var status = document.getElementById('status_' + uid);
        if (!el) {{ runAgent(index + 1); return; }}

        if (status) status.textContent = '🎙 speaking...';

        var i = 0;
        var done = false;

        function typeNext() {{
            if (i < agent.text.length) {{
                el.textContent += agent.text.charAt(i);
                i++;
                setTimeout(typeNext, agent.charDelay);
            }} else {{
                if (!done) {{
                    done = true;
                    if (status) status.textContent = '✓';
                    setTimeout(function() {{ runAgent(index + 1); }}, 800);
                }}
            }}
        }}

        function startVoice() {{
            if (isMuted) return;
            if (activeUtterance) window.speechSynthesis.cancel();
            activeUtterance = new SpeechSynthesisUtterance(agent.text);
            activeUtterance.rate = agent.rate;
            activeUtterance.pitch = agent.pitch;
            var voice = pickVoice(agent.gender);
            if (voice) activeUtterance.voice = voice;
            window.speechSynthesis.speak(activeUtterance);
        }}

        var voices = window.speechSynthesis.getVoices();
        if (voices.length === 0) {{
            window.speechSynthesis.onvoiceschanged = function() {{ startVoice(); }};
        }} else {{
            startVoice();
        }}

        typeNext();
    }}

    window['toggleMute_' + RN] = function() {{
        var btn = document.getElementById('mute_btn_' + RN);
        isMuted = !isMuted;
        if (isMuted) {{
            window.speechSynthesis.cancel();
            btn.textContent = '🔊 Unmute';
            btn.style.background = '#fff0f0';
            btn.style.borderColor = '#ffcccc';
        }} else {{
            btn.textContent = '🔇 Mute';
            btn.style.background = '#fff';
            btn.style.borderColor = '#ddd';
            if (currentIndex < agents.length) {{
                var agent = agents[currentIndex];
                var uid = agent.key + '_' + RN;
                var el = document.getElementById('text_' + uid);
                var spoken = el ? el.textContent : '';
                var remaining = agent.text.substring(spoken.length);
                if (remaining.length > 0) {{
                    activeUtterance = new SpeechSynthesisUtterance(remaining);
                    activeUtterance.rate = agent.rate;
                    activeUtterance.pitch = agent.pitch;
                    var voice = pickVoice(agent.gender);
                    if (voice) activeUtterance.voice = voice;
                    window.speechSynthesis.speak(activeUtterance);
                }}
            }}
        }}
    }};

    runAgent(0);
}})();
</script>
"""
    total_height = 70 + len(agents_data) * 180
    st.components.v1.html(html, height=total_height)

    # XAI reasoning expanders
    for agent_key, agent in perspectives.items():
        reasoning = agent.get('reasoning', '').strip()
        if reasoning and agent.get('response', '').strip():
            with st.expander(f"🧠 {agent.get('name','')} — XAI Reasoning"):
                st.markdown(reasoning)

# ══════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## ⚔️ Security Debate")
    st.caption("Multi-Agent AI for Cybersecurity Analysis")
    st.divider()

    # Connection summary
    if prediction == 1:
        st.error("🚨 ATTACK CONNECTION")
    else:
        st.success("✅ NORMAL CONNECTION")

    st.divider()
    st.markdown("**🎯 Top SHAP Features:**")
    for feat, val in top_features.items():
        st.caption(f"• {feat}: {connection[feat]:.2f} (SHAP: {val:.4f})")

    st.divider()
    st.markdown("**🗡️ MITRE Techniques:**")
    for t in matched_threats:
        st.caption(f"• {t['name']} ({t['id']})")

    st.divider()

    # Round progress
    for r in [1, 2, 3]:
        if r in st.session_state.debate_rounds:
            st.markdown(f"✅ Round {r} complete")
        elif r == st.session_state.debate_current_round:
            st.markdown(f"▶️ Round {r} — active")
        else:
            st.markdown(f"⬜ Round {r}")

    st.divider()
    if st.button("↺ Reset Debate"):
        for key in ['debate_rounds', 'debate_current_round',
                    'debate_spoken_rounds', 'debate_final_summary',
                    'debate_recommendations', 'debate_initialized']:
            st.session_state[key] = defaults[key]
        st.rerun()

# ══════════════════════════════════════════════════════
# MAIN AREA
# ══════════════════════════════════════════════════════
st.title("⚔️ Multi-Agent Security Debate")
st.markdown("*Three AI agents debate this connection using Chain of Thought + XAI*")
st.divider()

# ── Show agent cards ───────────────────────────────────
cols = st.columns(3)
for col, (key, agent) in zip(cols, AGENTS.items()):
    with col:
        profile = VOICE_PROFILES[key]
        voice_label = "🎙️ Deep male" if key == "shadow" else "🎙️ Slow male" if key == "phantom" else "🎙️ Calm female"
        st.markdown(f"""
<div style="background:{agent['color']}22; border:2px solid {agent['color']};
            border-radius:10px; padding:15px; text-align:center">
    <h2>{agent['emoji']}</h2>
    <h4 style="color:{agent['color']}">{agent['name']}</h4>
    <p style="font-size:12px; margin:0"><b>{agent['role']}</b></p>
    <p style="font-size:11px; color:gray; margin:4px 0">{voice_label}</p>
</div>
""", unsafe_allow_html=True)

st.divider()

# ── Completed rounds ───────────────────────────────────
for round_num in [1, 2, 3]:
    if round_num not in st.session_state.debate_rounds:
        continue

    round_data = st.session_state.debate_rounds[round_num]
    color = ROUND_COLORS[round_num]
    is_new = round_num not in st.session_state.debate_spoken_rounds

    st.markdown(
        f"<div class='round-header' style='color:{color}'>{ROUND_NAMES[round_num]}</div>",
        unsafe_allow_html=True
    )

    if is_new:
        render_round_with_typewriter(round_data['perspectives'], round_num)
        st.session_state.debate_spoken_rounds.append(round_num)
    else:
        for agent_key, agent in round_data['perspectives'].items():
            render_agent_static(agent)

    # Round summary
    if round_data.get('summary'):
        st.markdown(f"""
<div style="background:#F8FAFC; border:1px solid #E2E8F0;
            border-radius:8px; padding:12px; margin:10px 0;
            font-size:0.82rem; color:#555;">
    <b>🎙️ Moderator:</b> {round_data['summary']}
</div>
""", unsafe_allow_html=True)

# ── Active round button ────────────────────────────────
current = st.session_state.debate_current_round

if current <= 3 and current not in st.session_state.debate_rounds:
    color = ROUND_COLORS[current]
    st.markdown(
        f"<div class='round-header' style='color:{color}'>{ROUND_NAMES[current]}</div>",
        unsafe_allow_html=True
    )

    btn_labels = {
        1: "▶ Start Initialization",
        2: "▶ Start Critique & Conflict",
        3: "▶ Start Negotiation & Update"
    }

    if st.button(btn_labels[current], type="primary"):
        with st.spinner(f"Round {current} — agents are debating..."):
            perspectives = {}
            conversation_history = []

            # Build history from previous rounds
            for prev_num, prev_data in st.session_state.debate_rounds.items():
                for ak, ad in prev_data['perspectives'].items():
                    conversation_history.append({
                        "role": "user",
                        "content": f"Round {prev_num} - {ad['name']}: {ad['response']}"
                    })
                conversation_history.append({
                    "role": "assistant",
                    "content": f"Moderator: {prev_data['summary']}"
                })

            # Each agent speaks — seeing previous agents this round
            for agent_key in AGENTS.keys():
                perspective = get_agent_perspective(
                    agent_key=agent_key,
                    connection_context=connection_context,
                    shap_context=shap_context,
                    mitre_context=mitre_context,
                    round_number=current,
                    previous_perspectives=perspectives,
                    conversation_history=conversation_history
                )
                perspectives[agent_key] = perspective

            # Round summary
            summary = get_round_summary(
                connection_context=connection_context,
                round_number=current,
                perspectives=perspectives
            )

            st.session_state.debate_rounds[current] = {
                'perspectives': perspectives,
                'summary': summary
            }

            # Collect recommendations
            for ak, ad in perspectives.items():
                if ad.get('recommendation', '').strip():
                    st.session_state.debate_recommendations.append({
                        'agent': ad,
                        'round': current,
                        'text': ad['recommendation'],
                        'citation': ad.get('cited_standard', '')
                    })

            st.session_state.debate_current_round = current + 1
        st.rerun()

# ── Final summary ──────────────────────────────────────
if len(st.session_state.debate_rounds) == 3:
    if not st.session_state.debate_final_summary:
        if st.button("📋 Generate Security Intelligence Report", type="primary"):
            with st.spinner("Generating final security intelligence..."):
                summary = get_final_summary(
                    connection_context=connection_context,
                    all_rounds=st.session_state.debate_rounds
                )
                st.session_state.debate_final_summary = summary
            st.rerun()
    else:
        st.divider()
        st.markdown("### 📋 Final Security Intelligence Report")

        # Recommendations
        if st.session_state.debate_recommendations:
            st.markdown("#### 💡 Key Observations Per Round")
            for rec in st.session_state.debate_recommendations:
                a = rec['agent']
                citation_html = f"<div class='citation-box'>🎯 {rec['citation']}</div>" if rec['citation'] else ""
                st.markdown(f"""
<div class='agent-box' style='border-left-color:{a["color"]}'>
    <div class='agent-name' style='color:{a["color"]}'>{a["emoji"]} {a["name"]} — R{rec["round"]}</div>
    <div style='font-size:0.85rem;color:#1a1a1a;'>{rec["text"]}</div>
    {citation_html}
</div>""", unsafe_allow_html=True)

        st.divider()
        st.markdown("#### 📄 Full Intelligence Report")
        st.markdown(st.session_state.debate_final_summary)

        st.divider()
        st.success("👻 Ghost's cover is blown — the undercover white hat has revealed the full picture!")

st.divider()
st.caption("⚔️ Multi-Agent Security Debate | AI-REASON Project | Jönköping University")