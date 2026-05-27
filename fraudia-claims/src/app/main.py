"""
src/app/main.py
FraudIA Claims — Dashboard principal de análisis antifraude.
"""

import streamlit as st
import pandas as pd
import json
import os
import sys
from datetime import datetime, date

# ── path setup ─────────────────────────────────────────────────
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, ROOT)

# ── page config (MUST be first Streamlit call) ─────────────────
st.set_page_config(
    page_title="FraudIA Claims",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── demo data loader ───────────────────────────────────────────
@st.cache_data
def cargar_datos_demo():
    path = os.path.join(ROOT, "data/synthetic/siniestros_demo.json")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    # generate on-the-fly if missing
    sys.path.insert(0, os.path.join(ROOT, "data/synthetic"))
    from generate_demo import generar_dataset
    return generar_dataset()

# ── imports (soft-fail) ────────────────────────────────────────
try:
    import plotly.graph_objects as go
    import plotly.express as px
    PLOTLY = True
except ImportError:
    PLOTLY = False

# ═══════════════════════════════════════════════════════════════
# CSS — enterprise dark theme
# ═══════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=Space+Mono:wght@400;700&family=Inter:wght@300;400;500;600&display=swap');

/* ── reset & base ── */
*, *::before, *::after { box-sizing: border-box; }

.stApp {
    background: #070B14 !important;
    font-family: 'Inter', sans-serif !important;
    color: #C8D4E8 !important;
}

/* hide default streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 0 !important; max-width: 100% !important; }
section[data-testid="stSidebar"] { display: none; }
div[data-testid="stToolbar"] { display: none; }

/* ── scrollbar ── */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: #0D1220; }
::-webkit-scrollbar-thumb { background: #1E3A5F; border-radius: 4px; }

/* ── topbar ── */
.topbar {
    position: sticky; top: 0; z-index: 999;
    background: rgba(7,11,20,0.95);
    backdrop-filter: blur(20px);
    border-bottom: 1px solid rgba(30,58,95,0.6);
    padding: 0 32px;
    height: 56px;
    display: flex; align-items: center; justify-content: space-between;
}
.topbar-logo {
    font-family: 'Syne', sans-serif;
    font-weight: 800; font-size: 20px;
    color: #fff; letter-spacing: -0.5px;
}
.topbar-logo span { color: #3B82F6; }
.topbar-right { display: flex; align-items: center; gap: 16px; }
.topbar-user {
    font-size: 12px; color: #64748B;
    font-family: 'Space Mono', monospace;
}
.topbar-btn {
    background: rgba(59,130,246,0.12);
    border: 1px solid rgba(59,130,246,0.3);
    color: #3B82F6; padding: 6px 14px;
    border-radius: 6px; font-size: 12px;
    cursor: pointer; transition: all 0.2s;
    font-family: 'Inter', sans-serif; font-weight: 500;
}
.topbar-badge {
    background: #1E3A5F; color: #60A5FA;
    font-size: 10px; font-family: 'Space Mono', monospace;
    padding: 3px 8px; border-radius: 4px; letter-spacing: 0.05em;
}

/* ── main layout ── */
.main-wrap {
    display: grid;
    grid-template-columns: 1fr 340px;
    gap: 0;
    height: calc(100vh - 56px);
    overflow: hidden;
}
.left-panel { overflow-y: auto; padding: 24px 24px 24px 32px; }
.right-panel {
    border-left: 1px solid rgba(30,58,95,0.5);
    background: rgba(10,15,28,0.8);
    overflow-y: auto;
    padding: 24px 20px;
    display: flex; flex-direction: column; gap: 16px;
}

/* ── section titles ── */
.section-title {
    font-family: 'Syne', sans-serif;
    font-weight: 700; font-size: 11px;
    letter-spacing: 0.12em; text-transform: uppercase;
    color: #3B82F6; margin-bottom: 14px;
    display: flex; align-items: center; gap: 8px;
}
.section-title::after {
    content: ''; flex: 1;
    height: 1px; background: rgba(59,130,246,0.2);
}

/* ── KPI cards ── */
.kpi-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px; margin-bottom: 20px;
}
.kpi-card {
    background: rgba(13,18,32,0.9);
    border: 1px solid rgba(30,58,95,0.5);
    border-radius: 10px;
    padding: 16px 18px;
    position: relative; overflow: hidden;
    transition: border-color 0.2s, transform 0.2s;
}
.kpi-card:hover { border-color: rgba(59,130,246,0.4); transform: translateY(-1px); }
.kpi-card::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0;
    height: 2px;
}
.kpi-card.blue::before { background: linear-gradient(90deg, #3B82F6, transparent); }
.kpi-card.red::before { background: linear-gradient(90deg, #EF4444, transparent); }
.kpi-card.amber::before { background: linear-gradient(90deg, #F59E0B, transparent); }
.kpi-card.green::before { background: linear-gradient(90deg, #10B981, transparent); }
.kpi-label { font-size: 10px; color: #64748B; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 6px; }
.kpi-value { font-family: 'Syne', sans-serif; font-weight: 800; font-size: 28px; color: #fff; line-height: 1; }
.kpi-sub { font-size: 11px; color: #475569; margin-top: 4px; }

/* ── risk semaphore ── */
.risk-pill {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 4px 10px; border-radius: 20px;
    font-size: 11px; font-weight: 600; letter-spacing: 0.04em;
}
.risk-alto { background: rgba(239,68,68,0.12); color: #F87171; border: 1px solid rgba(239,68,68,0.3); }
.risk-medio { background: rgba(245,158,11,0.12); color: #FBBF24; border: 1px solid rgba(245,158,11,0.3); }
.risk-bajo { background: rgba(16,185,129,0.12); color: #34D399; border: 1px solid rgba(16,185,129,0.3); }
.risk-dot { width: 6px; height: 6px; border-radius: 50%; }
.risk-alto .risk-dot { background: #EF4444; box-shadow: 0 0 6px #EF4444; }
.risk-medio .risk-dot { background: #F59E0B; box-shadow: 0 0 6px #F59E0B; }
.risk-bajo .risk-dot { background: #10B981; box-shadow: 0 0 6px #10B981; }

/* ── score bar ── */
.score-bar-wrap { margin: 4px 0; }
.score-bar-track {
    height: 4px; background: rgba(30,58,95,0.4);
    border-radius: 2px; overflow: hidden;
}
.score-bar-fill {
    height: 100%; border-radius: 2px;
    transition: width 0.6s ease;
}

/* ── claims table ── */
.claims-table {
    width: 100%; border-collapse: collapse;
    font-size: 12px;
}
.claims-table th {
    text-align: left; padding: 8px 12px;
    font-size: 10px; font-weight: 600;
    letter-spacing: 0.08em; text-transform: uppercase;
    color: #64748B;
    border-bottom: 1px solid rgba(30,58,95,0.5);
}
.claims-table td {
    padding: 10px 12px;
    border-bottom: 1px solid rgba(30,58,95,0.2);
    color: #94A3B8; vertical-align: middle;
}
.claims-table tr:hover td { background: rgba(30,58,95,0.15); }
.claim-id {
    font-family: 'Space Mono', monospace;
    font-size: 11px; color: #3B82F6;
}
.claim-monto { color: #E2E8F0; font-weight: 500; }

/* ── alerts panel ── */
.alert-item {
    background: rgba(239,68,68,0.06);
    border: 1px solid rgba(239,68,68,0.2);
    border-left: 3px solid #EF4444;
    border-radius: 6px; padding: 10px 12px;
    margin-bottom: 8px;
}
.alert-item.medium {
    background: rgba(245,158,11,0.06);
    border-color: rgba(245,158,11,0.2);
    border-left-color: #F59E0B;
}
.alert-id {
    font-family: 'Space Mono', monospace;
    font-size: 10px; color: #94A3B8;
}
.alert-desc { font-size: 12px; color: #CBD5E1; margin-top: 3px; }

/* ── form modal ── */
.form-overlay {
    position: fixed; inset: 0; z-index: 1000;
    background: rgba(0,0,0,0.7); backdrop-filter: blur(4px);
    display: flex; align-items: center; justify-content: center;
}
.form-modal {
    background: #0D1220;
    border: 1px solid rgba(59,130,246,0.3);
    border-radius: 12px; padding: 28px 32px;
    width: 640px; max-height: 90vh; overflow-y: auto;
    box-shadow: 0 25px 80px rgba(0,0,0,0.6), 0 0 0 1px rgba(59,130,246,0.1);
}
.form-title {
    font-family: 'Syne', sans-serif;
    font-weight: 800; font-size: 18px; color: #fff;
    margin-bottom: 20px; display: flex; align-items: center; gap: 10px;
}

/* ── streamlit overrides ── */
.stTextInput > div > div > input,
.stSelectbox > div > div > div,
.stNumberInput > div > div > input,
.stTextArea > div > div > textarea,
.stDateInput > div > div > input {
    background: rgba(13,18,32,0.8) !important;
    border: 1px solid rgba(30,58,95,0.6) !important;
    color: #C8D4E8 !important;
    border-radius: 6px !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 13px !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: rgba(59,130,246,0.6) !important;
    box-shadow: 0 0 0 2px rgba(59,130,246,0.1) !important;
}
label[data-baseweb="label"], .stTextInput label,
.stSelectbox label, .stNumberInput label,
.stTextArea label, .stDateInput label {
    color: #64748B !important;
    font-size: 11px !important;
    font-weight: 500 !important;
    letter-spacing: 0.05em !important;
    text-transform: uppercase !important;
}
.stButton > button {
    border-radius: 6px !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 500 !important;
    transition: all 0.2s !important;
}

/* primary button */
.stButton > button[kind="primary"],
.stFormSubmitButton > button {
    background: linear-gradient(135deg, #2563EB, #1D4ED8) !important;
    color: #fff !important; border: none !important;
    box-shadow: 0 4px 15px rgba(37,99,235,0.3) !important;
}
.stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #3B82F6, #2563EB) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(37,99,235,0.4) !important;
}

/* ── chat ── */
.chat-wrap { display: flex; flex-direction: column; height: 100%; gap: 12px; }
.chat-messages { flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; }
.chat-bubble {
    padding: 10px 14px; border-radius: 10px;
    font-size: 12px; line-height: 1.5; max-width: 90%;
}
.chat-bubble.user {
    background: rgba(37,99,235,0.2);
    border: 1px solid rgba(59,130,246,0.3);
    color: #BFDBFE; align-self: flex-end;
    border-bottom-right-radius: 3px;
}
.chat-bubble.ai {
    background: rgba(13,18,32,0.9);
    border: 1px solid rgba(30,58,95,0.5);
    color: #CBD5E1; align-self: flex-start;
    border-bottom-left-radius: 3px;
}
.chat-label {
    font-size: 9px; color: #475569;
    font-family: 'Space Mono', monospace;
    margin-bottom: 3px;
}
.chat-quick-btn {
    background: rgba(30,58,95,0.3);
    border: 1px solid rgba(59,130,246,0.2);
    color: #60A5FA; padding: 5px 10px;
    border-radius: 15px; font-size: 10px;
    cursor: pointer; margin: 2px;
    white-space: nowrap;
}

/* ── login ── */
.login-wrap {
    min-height: 100vh; display: flex;
    align-items: center; justify-content: center;
    background: #070B14;
    background-image: radial-gradient(ellipse at 20% 50%, rgba(30,58,95,0.3) 0%, transparent 60%),
                      radial-gradient(ellipse at 80% 20%, rgba(37,99,235,0.15) 0%, transparent 50%);
}
.login-card {
    background: rgba(13,18,32,0.95);
    border: 1px solid rgba(30,58,95,0.6);
    border-radius: 16px; padding: 48px 40px;
    width: 400px;
    box-shadow: 0 40px 100px rgba(0,0,0,0.5), 0 0 0 1px rgba(59,130,246,0.08);
}
.login-logo {
    font-family: 'Syne', sans-serif;
    font-weight: 800; font-size: 28px;
    color: #fff; text-align: center; margin-bottom: 4px;
}
.login-logo span { color: #3B82F6; }
.login-sub {
    text-align: center; font-size: 12px; color: #475569;
    letter-spacing: 0.1em; text-transform: uppercase;
    font-family: 'Space Mono', monospace;
    margin-bottom: 32px;
}
.login-divider {
    height: 1px; background: rgba(30,58,95,0.5);
    margin: 20px 0;
}

/* ── new claim button ── */
.new-claim-btn {
    display: inline-flex; align-items: center; gap: 8px;
    background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%);
    color: #fff; padding: 10px 20px;
    border-radius: 8px; font-size: 13px; font-weight: 600;
    cursor: pointer; border: none;
    box-shadow: 0 4px 20px rgba(37,99,235,0.35);
    transition: all 0.2s;
    font-family: 'Inter', sans-serif;
}
.new-claim-btn:hover {
    background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%);
    transform: translateY(-1px);
    box-shadow: 0 6px 24px rgba(37,99,235,0.45);
}

/* ── tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid rgba(30,58,95,0.4) !important;
    gap: 0 !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: #64748B !important;
    border: none !important;
    font-size: 12px !important;
    font-weight: 500 !important;
    padding: 10px 18px !important;
    font-family: 'Inter', sans-serif !important;
}
.stTabs [aria-selected="true"] {
    color: #3B82F6 !important;
    border-bottom: 2px solid #3B82F6 !important;
}

/* chart container */
.chart-card {
    background: rgba(13,18,32,0.9);
    border: 1px solid rgba(30,58,95,0.5);
    border-radius: 10px; padding: 16px;
    margin-bottom: 16px;
}

/* ── explanation card ── */
.explain-card {
    background: rgba(13,18,32,0.9);
    border: 1px solid rgba(30,58,95,0.5);
    border-left: 3px solid #3B82F6;
    border-radius: 8px; padding: 14px 16px;
}
.explain-card h5 {
    font-family: 'Syne', sans-serif;
    font-size: 12px; color: #3B82F6; margin: 0 0 8px;
    text-transform: uppercase; letter-spacing: 0.08em;
}
.explain-card p { font-size: 12px; color: #94A3B8; line-height: 1.6; margin: 0; }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# SESSION STATE
# ═══════════════════════════════════════════════════════════════
def init_state():
    defaults = {
        "logged_in": False,
        "username": "",
        "show_form": False,
        "siniestros": [],
        "chat_history": [],  # [{role, content}]
        "selected_id": None,
        "filter_risk": "Todos",
        "search_query": "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v
    if not st.session_state["siniestros"]:
        st.session_state["siniestros"] = cargar_datos_demo()

init_state()

# ═══════════════════════════════════════════════════════════════
# helpers
# ═══════════════════════════════════════════════════════════════
def risk_pill_html(nivel: str) -> str:
    cls = {"Alto": "risk-alto", "Medio": "risk-medio", "Bajo": "risk-bajo"}.get(nivel, "risk-bajo")
    return f'<span class="risk-pill {cls}"><span class="risk-dot"></span>{nivel}</span>'

def score_bar_html(score: int) -> str:
    color = "#EF4444" if score >= 70 else "#F59E0B" if score >= 40 else "#10B981"
    return f"""
    <div class="score-bar-wrap">
      <div style="font-size:11px;color:#E2E8F0;font-weight:600;margin-bottom:3px;">{score}</div>
      <div class="score-bar-track">
        <div class="score-bar-fill" style="width:{score}%;background:{color};"></div>
      </div>
    </div>"""

def analizar_siniestro(s: dict) -> dict:
    """Pipeline de análisis completo en modo local."""
    try:
        from src.rules.fraud_rules import evaluar_todas_las_reglas
        from src.models.fraud_model import calcular_score_ml
        from src.features.build_features import detectar_narrativas_similares, construir_features_completas

        narrativas_prev = [x.get("narrativa", "") for x in st.session_state["siniestros"] if x.get("id") != s.get("id")]

        res_reglas = evaluar_todas_las_reglas(s)
        res_ml = calcular_score_ml(s)
        res_nlp = detectar_narrativas_similares(s.get("narrativa", ""), narrativas_prev)
        features = construir_features_completas(s, res_reglas, res_ml, res_nlp)

        s["score_riesgo"] = features["score_final"]
        s["nivel_riesgo"] = features["nivel_riesgo"]
        s["alertas"] = features["alertas"]
        return s
    except Exception:
        return s

# ═══════════════════════════════════════════════════════════════
# LOGIN PAGE
# ═══════════════════════════════════════════════════════════════
def page_login():
    st.markdown("""
    <div style="min-height:100vh;display:flex;align-items:center;justify-content:center;
    background:#070B14;background-image:radial-gradient(ellipse at 20% 50%,rgba(30,58,95,0.3) 0%,transparent 60%),
    radial-gradient(ellipse at 80% 20%,rgba(37,99,235,0.15) 0%,transparent 50%);">
    </div>""", unsafe_allow_html=True)

    col_pad, col_form, col_pad2 = st.columns([1, 1.2, 1])
    with col_form:
        st.markdown('<div style="height:15vh"></div>', unsafe_allow_html=True)
        st.markdown("""
        <div style="text-align:center;margin-bottom:32px;">
            <div style="font-family:Syne,sans-serif;font-weight:800;font-size:36px;color:#fff;letter-spacing:-1px;">
                Fraud<span style="color:#3B82F6">IA</span>
            </div>
            <div style="font-size:11px;color:#475569;letter-spacing:0.15em;text-transform:uppercase;
            font-family:'Space Mono',monospace;margin-top:6px;">
                Claims Intelligence Platform
            </div>
        </div>""", unsafe_allow_html=True)

        st.markdown("""
        <div style="background:rgba(13,18,32,0.95);border:1px solid rgba(30,58,95,0.6);
        border-radius:16px;padding:36px 32px;
        box-shadow:0 40px 100px rgba(0,0,0,0.5),0 0 0 1px rgba(59,130,246,0.08);">
        """, unsafe_allow_html=True)

        with st.form("login_form"):
            st.markdown('<p style="font-size:11px;color:#64748B;letter-spacing:0.08em;text-transform:uppercase;margin-bottom:4px;">Usuario</p>', unsafe_allow_html=True)
            username = st.text_input("", placeholder="analista@empresa.com", label_visibility="collapsed")
            st.markdown('<p style="font-size:11px;color:#64748B;letter-spacing:0.08em;text-transform:uppercase;margin:12px 0 4px;">Contraseña</p>', unsafe_allow_html=True)
            password = st.text_input("", type="password", placeholder="••••••••••", label_visibility="collapsed")
            st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)
            submitted = st.form_submit_button("Iniciar sesión →", use_container_width=True, type="primary")

            if submitted:
                if username and password:
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = username.split("@")[0].title()
                    st.rerun()
                else:
                    st.error("Ingresa usuario y contraseña.")

        st.markdown("""
        <div style="margin-top:16px;padding:10px 14px;background:rgba(30,58,95,0.2);
        border-radius:6px;border:1px solid rgba(30,58,95,0.4);">
            <p style="font-size:10px;color:#475569;margin:0;font-family:'Space Mono',monospace;">
            DEMO — Ingresa cualquier usuario y contraseña para continuar
            </p>
        </div>""", unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
# TOPBAR
# ═══════════════════════════════════════════════════════════════
def render_topbar():
    col_logo, col_mid, col_right = st.columns([2, 4, 2])
    with col_logo:
        st.markdown("""
        <div style="padding:12px 0;font-family:Syne,sans-serif;font-weight:800;font-size:18px;color:#fff;">
            Fraud<span style="color:#3B82F6">IA</span>
            <span style="font-size:10px;color:#475569;font-family:'Space Mono',monospace;
            font-weight:400;margin-left:8px;vertical-align:middle;">CLAIMS v1.0</span>
        </div>""", unsafe_allow_html=True)
    with col_mid:
        st.markdown("""
        <div style="display:flex;align-items:center;gap:8px;padding:12px 0;">
            <span style="font-size:10px;color:#475569;font-family:'Space Mono',monospace;">SISTEMA ACTIVO</span>
            <span style="width:6px;height:6px;border-radius:50%;background:#10B981;
            box-shadow:0 0 6px #10B981;display:inline-block;"></span>
        </div>""", unsafe_allow_html=True)
    with col_right:
        c1, c2 = st.columns([3, 1])
        with c1:
            st.markdown(f"""
            <div style="padding:12px 0;text-align:right;font-size:11px;color:#64748B;
            font-family:'Space Mono',monospace;">
                {st.session_state.get('username','Analista')}
            </div>""", unsafe_allow_html=True)
        with c2:
            if st.button("⎋", key="logout_btn", help="Cerrar sesión"):
                st.session_state["logged_in"] = False
                st.rerun()

    st.markdown('<hr style="margin:0 0 20px;border:none;border-top:1px solid rgba(30,58,95,0.5);">', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
# KPI SECTION
# ═══════════════════════════════════════════════════════════════
def render_kpis(data: list):
    total = len(data)
    altos = sum(1 for s in data if s.get("nivel_riesgo") == "Alto")
    medios = sum(1 for s in data if s.get("nivel_riesgo") == "Medio")
    monto = sum(s.get("monto_reclamado", 0) for s in data)
    score_avg = sum(s.get("score_riesgo", 0) for s in data) / total if total else 0

    c1, c2, c3, c4 = st.columns(4)
    cards = [
        (c1, "blue", "Total siniestros", str(total), f"{medios} en revisión"),
        (c2, "red", "Riesgo alto", str(altos), f"{altos/total*100:.0f}% del portafolio" if total else "—"),
        (c3, "amber", "Score promedio", f"{score_avg:.0f}", "Índice de riesgo global"),
        (c4, "green", "Monto total", f"${monto:,.0f}", "Suma reclamada"),
    ]
    for col, cls, label, val, sub in cards:
        with col:
            st.markdown(f"""
            <div class="kpi-card {cls}">
                <div class="kpi-label">{label}</div>
                <div class="kpi-value">{val}</div>
                <div class="kpi-sub">{sub}</div>
            </div>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
# CHARTS
# ═══════════════════════════════════════════════════════════════
def render_charts(data: list):
    if not PLOTLY or not data:
        return

    df = pd.DataFrame(data)

    col1, col2 = st.columns(2)

    # Risk distribution donut
    with col1:
        st.markdown('<div class="section-title">Distribución de riesgo</div>', unsafe_allow_html=True)
        risk_counts = df["nivel_riesgo"].value_counts()
        colors = {"Alto": "#EF4444", "Medio": "#F59E0B", "Bajo": "#10B981"}
        fig = go.Figure(go.Pie(
            labels=risk_counts.index.tolist(),
            values=risk_counts.values.tolist(),
            hole=0.65,
            marker_colors=[colors.get(l, "#64748B") for l in risk_counts.index],
            textinfo="percent",
            textfont=dict(size=11, color="#C8D4E8"),
            hovertemplate="<b>%{label}</b><br>%{value} casos<extra></extra>",
        ))
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            showlegend=True,
            legend=dict(font=dict(color="#64748B", size=11), bgcolor="rgba(0,0,0,0)"),
            margin=dict(l=0, r=0, t=10, b=10), height=200,
            annotations=[dict(text=f"<b style='font-size:22px'>{len(df)}</b><br><span style='font-size:11px'>casos</span>",
                              showarrow=False, font=dict(color="#fff", size=14))]
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # Score histogram
    with col2:
        st.markdown('<div class="section-title">Score de riesgo</div>', unsafe_allow_html=True)
        fig2 = go.Figure(go.Histogram(
            x=df["score_riesgo"].tolist(),
            nbinsx=10,
            marker=dict(
                color=df["score_riesgo"].tolist(),
                colorscale=[[0, "#10B981"], [0.4, "#F59E0B"], [1, "#EF4444"]],
                line=dict(color="rgba(0,0,0,0)", width=0),
            ),
            hovertemplate="Score: %{x}<br>Casos: %{y}<extra></extra>",
        ))
        fig2.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(showgrid=False, color="#475569", tickfont=dict(size=10)),
            yaxis=dict(showgrid=True, gridcolor="rgba(30,58,95,0.3)", color="#475569", tickfont=dict(size=10)),
            margin=dict(l=0, r=0, t=10, b=30), height=200,
            bargap=0.1,
        )
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})


# ═══════════════════════════════════════════════════════════════
# CLAIMS TABLE
# ═══════════════════════════════════════════════════════════════
def render_table(data: list):
    if not data:
        st.markdown('<p style="color:#475569;font-size:13px;">Sin registros.</p>', unsafe_allow_html=True)
        return

    rows = ""
    for s in data:
        nivel = s.get("nivel_riesgo", "Bajo")
        score = s.get("score_riesgo", 0)
        alertas = s.get("alertas", [])
        pill = risk_pill_html(nivel)
        bar = score_bar_html(score)
        alert_count = len(alertas)
        alert_badge = f'<span style="background:rgba(239,68,68,0.15);color:#F87171;padding:2px 6px;border-radius:4px;font-size:10px;font-weight:600;">{alert_count} alertas</span>' if alert_count else '<span style="color:#374151;font-size:10px;">—</span>'

        rows += f"""
        <tr>
          <td><span class="claim-id">{s.get('id_siniestro','')}</span></td>
          <td style="color:#E2E8F0;">{s.get('cliente','')}</td>
          <td style="color:#94A3B8;">{s.get('tipo_siniestro','')}</td>
          <td class="claim-monto">${s.get('monto_reclamado',0):,.0f}</td>
          <td>{pill}</td>
          <td>{bar}</td>
          <td>{alert_badge}</td>
          <td style="color:#475569;font-size:11px;">{s.get('ciudad','')}</td>
        </tr>"""

    st.markdown(f"""
    <div style="overflow-x:auto;">
    <table class="claims-table">
      <thead>
        <tr>
          <th>ID Siniestro</th><th>Cliente</th><th>Tipo</th>
          <th>Monto</th><th>Riesgo</th><th>Score</th>
          <th>Alertas</th><th>Ciudad</th>
        </tr>
      </thead>
      <tbody>{rows}</tbody>
    </table>
    </div>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
# ALERTS PANEL (right sidebar)
# ═══════════════════════════════════════════════════════════════
def render_alerts_panel(data: list):
    st.markdown('<div class="section-title">🔴 Alertas activas</div>', unsafe_allow_html=True)
    altos = [s for s in data if s.get("nivel_riesgo") == "Alto"][:6]
    if not altos:
        st.markdown('<p style="color:#475569;font-size:12px;">Sin alertas activas.</p>', unsafe_allow_html=True)
    for s in altos:
        alertas = s.get("alertas", [])
        desc = alertas[0] if alertas else "Anomalía detectada"
        st.markdown(f"""
        <div class="alert-item">
            <div class="alert-id">{s.get('id_siniestro')} · ${s.get('monto_reclamado',0):,.0f}</div>
            <div class="alert-desc">{desc}</div>
        </div>""", unsafe_allow_html=True)

    medios = [s for s in data if s.get("nivel_riesgo") == "Medio"][:4]
    if medios:
        st.markdown('<div class="section-title" style="margin-top:16px;">🟡 Seguimiento</div>', unsafe_allow_html=True)
        for s in medios:
            alertas = s.get("alertas", [])
            desc = alertas[0] if alertas else "Requiere revisión rutinaria"
            st.markdown(f"""
            <div class="alert-item medium">
                <div class="alert-id">{s.get('id_siniestro')} · {s.get('cliente','')}</div>
                <div class="alert-desc">{desc}</div>
            </div>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
# CHAT PANEL (right sidebar)
# ═══════════════════════════════════════════════════════════════
def render_chat_panel(data: list):
    st.markdown('<div class="section-title">🤖 Asistente IA</div>', unsafe_allow_html=True)

    # Suggested questions
    sugerencias = [
        "¿Qué casos priorizar?",
        "¿Narrativas similares?",
        "Resumen de riesgo alto",
        "¿Proveedor con más alertas?",
    ]

    cols = st.columns(2)
    for i, sug in enumerate(sugerencias):
        with cols[i % 2]:
            if st.button(sug, key=f"sug_{i}", use_container_width=True):
                st.session_state["chat_history"].append({"role": "user", "content": sug})
                _send_chat(sug, data)

    # Conversation history
    if st.session_state["chat_history"]:
        st.markdown('<div style="margin:12px 0 8px;border-top:1px solid rgba(30,58,95,0.4);padding-top:12px;"></div>', unsafe_allow_html=True)
        for msg in st.session_state["chat_history"][-8:]:
            role = msg["role"]
            label = "ANALISTA" if role == "user" else "FRAUDIA IA"
            cls = "user" if role == "user" else "ai"
            st.markdown(f"""
            <div>
              <div class="chat-label">{label}</div>
              <div class="chat-bubble {cls}">{msg['content']}</div>
            </div>""", unsafe_allow_html=True)

    # Input
    st.markdown('<div style="margin-top:12px;"></div>', unsafe_allow_html=True)
    with st.form("chat_form", clear_on_submit=True):
        query = st.text_input("", placeholder="Consulta al asistente IA…", label_visibility="collapsed")
        sent = st.form_submit_button("Enviar →", use_container_width=True, type="primary")
        if sent and query.strip():
            st.session_state["chat_history"].append({"role": "user", "content": query})
            _send_chat(query, data)
            st.rerun()

    if st.button("🗑 Limpiar conversación", key="clear_chat"):
        st.session_state["chat_history"] = []
        st.rerun()


def _send_chat(pregunta: str, data: list):
    try:
        from src.ai_agent.claims_agent import agente_responder
        historial_prev = [m for m in st.session_state["chat_history"][:-1]]
        respuesta = agente_responder(pregunta, historial_prev, data)
    except Exception as e:
        respuesta = f"Error en el agente: {str(e)[:100]}"
    st.session_state["chat_history"].append({"role": "assistant", "content": respuesta})


# ═══════════════════════════════════════════════════════════════
# NEW CLAIM FORM
# ═══════════════════════════════════════════════════════════════
def render_new_claim_form():
    st.markdown("""
    <div style="background:rgba(13,18,32,0.98);border:1px solid rgba(59,130,246,0.35);
    border-radius:12px;padding:24px 28px;margin-bottom:20px;
    box-shadow:0 20px 60px rgba(0,0,0,0.5),0 0 0 1px rgba(59,130,246,0.08);">
    <div style="font-family:Syne,sans-serif;font-weight:800;font-size:16px;color:#fff;
    margin-bottom:20px;display:flex;align-items:center;gap:8px;">
    🛡️ Registrar nuevo siniestro
    <span style="font-size:10px;color:#3B82F6;font-family:'Space Mono',monospace;
    font-weight:400;margin-left:4px;background:rgba(59,130,246,0.1);
    padding:3px 8px;border-radius:4px;">ANÁLISIS AUTOMÁTICO</span>
    </div>
    </div>""", unsafe_allow_html=True)

    with st.form("form_siniestro", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            id_sin = st.text_input("ID Siniestro", placeholder="SIN-2024-0021")
            cliente = st.text_input("Cliente", placeholder="Nombre completo")
            tipo = st.selectbox("Tipo de siniestro", [
                "Robo de vehículo", "Accidente de tránsito", "Daño parcial",
                "Incendio", "Robo de contenido", "Responsabilidad civil",
                "Asistencia vial", "Granizo", "Otro",
            ])
            monto = st.number_input("Monto reclamado ($)", min_value=0.0, step=100.0)
            historial = st.number_input("Historial de reclamos previos", min_value=0, step=1)

        with c2:
            fecha_inc = st.date_input("Fecha del incidente", value=date.today())
            fecha_pol = st.date_input("Fecha contratación póliza", value=date.today())
            ciudad = st.selectbox("Ciudad", [
                "Bogotá", "Medellín", "Cali", "Barranquilla", "Cartagena",
                "Bucaramanga", "Pereira", "Manizales", "Ibagué", "Santa Marta", "Otra",
            ])
            proveedor = st.text_input("Proveedor / Taller", placeholder="Nombre del taller")

        narrativa = st.text_area("Descripción narrativa del siniestro",
                                 placeholder="Describe detalladamente el incidente reportado…",
                                 height=100)

        col_s, col_c = st.columns([2, 1])
        with col_s:
            submitted = st.form_submit_button("🔍 Registrar y analizar", use_container_width=True, type="primary")
        with col_c:
            cancelar = st.form_submit_button("Cancelar", use_container_width=True)

        if cancelar:
            st.session_state["show_form"] = False
            st.rerun()

        if submitted:
            if not id_sin or not cliente:
                st.error("ID de siniestro y cliente son obligatorios.")
            else:
                nuevo = {
                    "id": len(st.session_state["siniestros"]) + 1,
                    "id_siniestro": id_sin,
                    "cliente": cliente,
                    "tipo_siniestro": tipo,
                    "monto_reclamado": float(monto),
                    "fecha_incidente": str(fecha_inc),
                    "fecha_poliza": str(fecha_pol),
                    "ciudad": ciudad,
                    "proveedor": proveedor or "Sin especificar",
                    "historial_reclamos": int(historial),
                    "narrativa": narrativa,
                    "score_riesgo": 0,
                    "nivel_riesgo": "Bajo",
                    "alertas": [],
                    "fecha_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }

                with st.spinner("Ejecutando análisis de riesgo…"):
                    nuevo = analizar_siniestro(nuevo)

                st.session_state["siniestros"].insert(0, nuevo)
                st.session_state["show_form"] = False

                nivel = nuevo.get("nivel_riesgo", "Bajo")
                score = nuevo.get("score_riesgo", 0)
                alertas = nuevo.get("alertas", [])

                if nivel == "Alto":
                    st.error(f"⚠️ Siniestro registrado · Nivel de riesgo **ALTO** (score {score}). {len(alertas)} alerta(s) detectada(s).")
                elif nivel == "Medio":
                    st.warning(f"🟡 Siniestro registrado · Nivel de riesgo **MEDIO** (score {score}).")
                else:
                    st.success(f"✅ Siniestro registrado · Nivel de riesgo **BAJO** (score {score}).")

                st.rerun()


# ═══════════════════════════════════════════════════════════════
# DETAIL VIEW
# ═══════════════════════════════════════════════════════════════
def render_detail(s: dict):
    st.markdown(f"""
    <div style="background:rgba(13,18,32,0.9);border:1px solid rgba(30,58,95,0.5);
    border-radius:10px;padding:20px 24px;margin-bottom:16px;">
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px;">
        <div>
            <div style="font-family:'Space Mono',monospace;font-size:11px;color:#3B82F6;">{s.get('id_siniestro')}</div>
            <div style="font-family:Syne,sans-serif;font-weight:700;font-size:18px;color:#fff;">{s.get('cliente')}</div>
        </div>
        <div>{risk_pill_html(s.get('nivel_riesgo','Bajo'))}</div>
    </div>
    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;font-size:12px;">
        <div><span style="color:#64748B;">Tipo:</span> <span style="color:#C8D4E8;">{s.get('tipo_siniestro')}</span></div>
        <div><span style="color:#64748B;">Monto:</span> <span style="color:#E2E8F0;font-weight:600;">${s.get('monto_reclamado',0):,.0f}</span></div>
        <div><span style="color:#64748B;">Ciudad:</span> <span style="color:#C8D4E8;">{s.get('ciudad')}</span></div>
        <div><span style="color:#64748B;">Incidente:</span> <span style="color:#C8D4E8;">{s.get('fecha_incidente')}</span></div>
        <div><span style="color:#64748B;">Póliza:</span> <span style="color:#C8D4E8;">{s.get('fecha_poliza')}</span></div>
        <div><span style="color:#64748B;">Historial:</span> <span style="color:#C8D4E8;">{s.get('historial_reclamos')} reclamos</span></div>
    </div>
    <div style="margin-top:12px;padding-top:12px;border-top:1px solid rgba(30,58,95,0.4);">
        <div style="font-size:10px;color:#64748B;margin-bottom:4px;text-transform:uppercase;letter-spacing:0.08em;">Narrativa</div>
        <div style="font-size:12px;color:#94A3B8;line-height:1.6;">{s.get('narrativa','—')}</div>
    </div>
    </div>""", unsafe_allow_html=True)

    alertas = s.get("alertas", [])
    if alertas:
        st.markdown('<div class="section-title">Indicadores de riesgo detectados</div>', unsafe_allow_html=True)
        for a in alertas:
            st.markdown(f'<div class="alert-item"><div class="alert-desc">⚡ {a}</div></div>', unsafe_allow_html=True)

    # IA explanation
    st.markdown('<div class="section-title" style="margin-top:16px;">Explicación IA</div>', unsafe_allow_html=True)
    try:
        from src.explainability.explain_score import explicar_siniestro
        features = {
            "score_final": s.get("score_riesgo", 0),
            "nivel_riesgo": s.get("nivel_riesgo", "Bajo"),
            "alertas": alertas,
            "nlp": {"max_similitud": 0},
        }
        explicacion = explicar_siniestro(s, features)
    except Exception as e:
        explicacion = f"Módulo de explicación no disponible: {str(e)[:60]}"

    st.markdown(f"""
    <div class="explain-card">
        <h5>Análisis automatizado</h5>
        <p>{explicacion.replace(chr(10), '<br>')}</p>
    </div>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
# MAIN DASHBOARD
# ═══════════════════════════════════════════════════════════════
def page_dashboard():
    render_topbar()
    data = st.session_state["siniestros"]

    # ── LEFT content, RIGHT panel ──
    left_col, right_col = st.columns([3.2, 1])

    with left_col:
        # KPIs
        render_kpis(data)

        # Controls row
        c_btn, c_filter, c_search = st.columns([1.5, 1.5, 2])
        with c_btn:
            if st.button("＋ Nuevo registro", key="open_form_btn", use_container_width=True, type="primary"):
                st.session_state["show_form"] = not st.session_state.get("show_form", False)

        with c_filter:
            filtro = st.selectbox("Filtrar por riesgo", ["Todos", "Alto", "Medio", "Bajo"],
                                  key="risk_filter", label_visibility="collapsed")

        with c_search:
            busqueda = st.text_input("", placeholder="🔍 Buscar por cliente, ID, ciudad…",
                                     label_visibility="collapsed")

        st.markdown('<div style="height:4px"></div>', unsafe_allow_html=True)

        # Form inline
        if st.session_state.get("show_form", False):
            render_new_claim_form()

        # Filter data
        filtered = data
        if filtro != "Todos":
            filtered = [s for s in data if s.get("nivel_riesgo") == filtro]
        if busqueda:
            q = busqueda.lower()
            filtered = [s for s in filtered if
                        q in s.get("cliente", "").lower() or
                        q in s.get("id_siniestro", "").lower() or
                        q in s.get("ciudad", "").lower() or
                        q in s.get("tipo_siniestro", "").lower()]

        # Tabs
        tab_table, tab_charts, tab_detail = st.tabs(["📋 Tabla de siniestros", "📊 Análisis visual", "🔍 Detalle"])

        with tab_table:
            st.markdown(f'<p style="font-size:11px;color:#475569;margin-bottom:12px;">{len(filtered)} registros mostrados</p>', unsafe_allow_html=True)
            render_table(filtered)

        with tab_charts:
            render_charts(filtered)

        with tab_detail:
            if filtered:
                opciones = {f"{s['id_siniestro']} — {s['cliente']}": s for s in filtered}
                sel = st.selectbox("Seleccionar siniestro", list(opciones.keys()), label_visibility="collapsed")
                if sel:
                    render_detail(opciones[sel])
            else:
                st.markdown('<p style="color:#475569;font-size:13px;">Sin registros para mostrar.</p>', unsafe_allow_html=True)

    with right_col:
        tab_alerts, tab_chat = st.tabs(["🔴 Alertas", "🤖 IA Chat"])
        with tab_alerts:
            render_alerts_panel(data)
        with tab_chat:
            render_chat_panel(data)


# ═══════════════════════════════════════════════════════════════
# ROUTER
# ═══════════════════════════════════════════════════════════════
if st.session_state.get("logged_in"):
    page_dashboard()
else:
    page_login()
