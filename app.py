import streamlit as st
import sqlite3
import bcrypt
import re
import pandas as pd
import unicodedata
from io import BytesIO
from datetime import datetime

st.set_page_config(
    page_title="ProcessLab — Simulateur intelligent",
    layout="wide",
    page_icon="🧪",
    initial_sidebar_state="collapsed"
)

# =========================================================
# 1. INITIALISATION ET TRADUCTIONS
# =========================================================
DEFAULT_PARAMS = {
    "m0": 1000.0, "x0_sol": 0.10, "residus": 20.0, "mR": 100.0,
    "xR": 0.40, "T2": 20.0, "T3": 80.0, "cp": 3.8,
    "x4": 0.40, "lambda_v": 2300.0
}

TRANSLATIONS = {
    "FR": {
        "app_subtitle": "Filtration • Chauffage • Évaporation",
        "theme_btn": "☀️ Clair" if st.session_state.get("theme_mode", "dark") == "dark" else "🌙 Sombre",
        "lang_btn": "🇬🇧 English",
        "login_tab": "🔑 Se connecter", "signup_tab": "📝 Créer un compte",
        "email": "📧 Email", "password": "🔒 Mot de passe",
        "confirm_pass": "🔒 Confirmer le mot de passe",
        "username": "👤 Nom d'utilisateur", "login_btn": "Se connecter →",
        "signup_btn": "Créer mon compte ✨", "sidebar_welcome": "Bonjour",
        "logout": "🚪 Se déconnecter",
        "info_msg": "Modifiez les paramètres puis consultez les résultats.",
        "sim_title": "Simulateur de bilan matière et énergétique",
        "sim_caption": "Ajustez les paramètres pour visualiser les résultats du procédé.",
        "tab_params": "⚙️ Paramètres", "tab_results": "📊 Résultats",
        "tab_conclusion": "📝 Conclusion", "tab_chat": "🤖 Assistant",
        "m0": "Débit initial m₀ (kg/h)", "x0": "Fraction massique en soluté x₀ (0–1)",
        "residus": "Résidus de filtration (kg/h)", "mR": "Débit d'apport mR (kg/h)",
        "xR": "Fraction massique de l'apport xR (0–1)",
        "T2": "Température d'entrée T₂ (°C)", "T3": "Température après chauffage T₃ (°C)",
        "cp": "Capacité thermique Cp (kJ/kg·K)",
        "x4": "Fraction massique finale visée x₄ (0–1)",
        "lambda_v": "Chaleur latente λv (kJ/kg)",
        "res_real_time": "Résultats de la simulation",
        "metric_m1": "Débit après filtration", "metric_x2": "Concentration du mélange",
        "metric_m4": "Débit final", "metric_mv": "Débit évaporé",
        "metric_Q3": "Puissance de chauffage", "metric_Q4": "Puissance d'évaporation",
        "metric_Q5": "Puissance de refroidissement", "metric_err": "Écart du bilan matière",
        "graphs": "Graphiques", "obj_reach": "Atteinte de la concentration cible",
        "obj_text": "Concentration cible", "concl_title": "Conclusion et recommandations",
        "summary": "Synthèse", "chat_title": "Assistant virtuel",
        "chat_placeholder": "Posez une question sur votre simulation...",
        "err_fill": "Veuillez remplir tous les champs.",
        "err_auth": "Email ou mot de passe incorrect.",
        "err_req": "Tous les champs sont obligatoires.",
        "err_email": "Adresse email invalide.", "err_pass": "Les mots de passe sont différents.",
        "err_len": "Le mot de passe doit contenir au moins 8 caractères.",
        "err_exist": "Cette adresse email est déjà utilisée.",
        "succ_create": "Compte créé avec succès !", "err_create": "Erreur lors de la création du compte.",
        "landing_title": "Simulez votre procédé industriel",
        "landing_sub": "Calculez la filtration, le chauffage et l'évaporation. Consultez les bilans, graphiques et recommandations.",
        "cta_start": "🚀 Commencer", "cta_login": "Déjà un compte ? Se connecter",
        "feat1": "⚡ Calculs rapides", "feat1_d": "Résultats calculés à partir de vos paramètres.",
        "feat2": "📊 Tableaux et graphiques", "feat2_d": "Suivez les débits et les puissances énergétiques.",
        "feat3": "🤖 Assistant", "feat3_d": "Obtenez des explications sur les grandeurs calculées.",
        "feat4": "📄 Rapport PDF", "feat4_d": "Exportez un rapport structuré.",
        "how_title": "Comment ça marche ?", "step1": "1. Créez un compte",
        "step1_d": "Inscrivez-vous pour accéder au simulateur.",
        "step2": "2. Saisissez les paramètres", "step2_d": "Définissez les débits, fractions et températures.",
        "step3": "3. Consultez le rapport", "step3_d": "Analysez les résultats et exportez le PDF.",
        "export_pdf": "📄 Télécharger le rapport PDF", "back_home": "← Retour à l'accueil"
    },
    "EN": {
        "app_subtitle": "Filtration • Heating • Evaporation",
        "theme_btn": "☀️ Light" if st.session_state.get("theme_mode", "dark") == "dark" else "🌙 Dark",
        "lang_btn": "🇫🇷 Français",
        "login_tab": "🔑 Login", "signup_tab": "📝 Create account",
        "email": "📧 Email", "password": "🔒 Password",
        "confirm_pass": "🔒 Confirm password", "username": "👤 Username",
        "login_btn": "Login →", "signup_btn": "Create account ✨",
        "sidebar_welcome": "Hello", "logout": "🚪 Log out",
        "info_msg": "Edit the parameters and consult the results.",
        "sim_title": "Material and energy balance simulator",
        "sim_caption": "Adjust the parameters to view the process results.",
        "tab_params": "⚙️ Parameters", "tab_results": "📊 Results",
        "tab_conclusion": "📝 Conclusion", "tab_chat": "🤖 Assistant",
        "m0": "Initial flow m₀ (kg/h)", "x0": "Solute mass fraction x₀ (0–1)",
        "residus": "Filtration residues (kg/h)", "mR": "Added flow mR (kg/h)",
        "xR": "Added stream mass fraction xR (0–1)",
        "T2": "Inlet temperature T₂ (°C)", "T3": "Temperature after heating T₃ (°C)",
        "cp": "Heat capacity Cp (kJ/kg·K)", "x4": "Target final mass fraction x₄ (0–1)",
        "lambda_v": "Latent heat λv (kJ/kg)",
        "res_real_time": "Simulation results",
        "metric_m1": "Flow after filtration", "metric_x2": "Mixture concentration",
        "metric_m4": "Final flow", "metric_mv": "Evaporated flow",
        "metric_Q3": "Heating power", "metric_Q4": "Evaporation power",
        "metric_Q5": "Cooling power", "metric_err": "Material balance deviation",
        "graphs": "Charts", "obj_reach": "Target concentration achievement",
        "obj_text": "Target concentration", "concl_title": "Conclusion and recommendations",
        "summary": "Summary", "chat_title": "Virtual assistant",
        "chat_placeholder": "Ask a question about your simulation...",
        "err_fill": "Please fill in all fields.", "err_auth": "Incorrect email or password.",
        "err_req": "All fields are required.", "err_email": "Invalid email address.",
        "err_pass": "Passwords do not match.", "err_len": "Password must contain at least 8 characters.",
        "err_exist": "This email address is already in use.", "succ_create": "Account created successfully!",
        "err_create": "Account creation error.", "landing_title": "Simulate your industrial process",
        "landing_sub": "Calculate filtration, heating and evaporation. View balances, charts and recommendations.",
        "cta_start": "🚀 Get started", "cta_login": "Already have an account? Login",
        "feat1": "⚡ Fast calculations", "feat1_d": "Results calculated from your parameters.",
        "feat2": "📊 Tables and charts", "feat2_d": "Track flows and energy requirements.",
        "feat3": "🤖 Assistant", "feat3_d": "Get explanations about calculated values.",
        "feat4": "📄 PDF report", "feat4_d": "Export a structured report.",
        "how_title": "How does it work?", "step1": "1. Create an account",
        "step1_d": "Sign up to access the simulator.", "step2": "2. Enter parameters",
        "step2_d": "Set flow rates, fractions and temperatures.",
        "step3": "3. View the report", "step3_d": "Review results and export the PDF.",
        "export_pdf": "📄 Download PDF report", "back_home": "← Back to home"
    }
}

for key, value in {
    "theme_mode": "light", "lang": "FR", "page": "landing",
    "logged_in": False, "params": DEFAULT_PARAMS.copy()
}.items():
    if key not in st.session_state:
        st.session_state[key] = value

def t(key):
    return TRANSLATIONS[st.session_state.lang].get(key, key)

# =========================================================
# 2. BASE DE DONNÉES ET AUTHENTIFICATION
# =========================================================
DB_NAME = "users.db"

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            )
        """)

def hash_password(password):
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(password, password_hash):
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False

def create_user(username, email, password):
    try:
        with sqlite3.connect(DB_NAME) as conn:
            conn.execute(
                "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                (username, email.lower(), hash_password(password))
            )
        return True
    except sqlite3.IntegrityError:
        return False

def authenticate_user(email, password):
    with sqlite3.connect(DB_NAME) as conn:
        row = conn.execute(
            "SELECT username, password_hash FROM users WHERE email = ?",
            (email.lower(),)
        ).fetchone()
    if row and verify_password(password, row[1]):
        return row[0]
    return None

init_db()

# =========================================================
# 3. STYLE GRAPHIQUE — SOFT / COOL / ELEGANT
# =========================================================
is_dark = st.session_state.theme_mode == "dark"
if is_dark:
    BG, CARD, CARD_SOLID = "#151B1A", "#202927", "#202927"
    TEXT, MUTED = "#F1F5F2", "#A8B7B0"
    INPUT_BG, BORDER = "#27322E", "#35443D"
    ACCENT, ACCENT2, ACCENT3 = "#9CC5B1", "#7FAE9A", "#B6CFC2"
    SHADOW, SOFT = "0 8px 28px rgba(0,0,0,.16)", "#26342E"
else:
    BG, CARD, CARD_SOLID = "#F6F8F6", "#FFFFFF", "#FFFFFF"
    TEXT, MUTED = "#25332D", "#7B8982"
    INPUT_BG, BORDER = "#FFFFFF", "#E4EAE5"
    ACCENT, ACCENT2, ACCENT3 = "#527C68", "#789C88", "#A8C2B2"
    SHADOW, SOFT = "0 8px 28px rgba(39,65,50,.055)", "#EDF3EE"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');
.stApp {{background:{BG};font-family:'DM Sans',sans-serif;color:{TEXT};}}
.block-container {{max-width:1180px;padding-top:2rem;padding-bottom:4rem;}}
h1,h2,h3,h4 {{color:{TEXT}!important;font-family:'Manrope',sans-serif!important;letter-spacing:-.035em;}}
h1 {{font-weight:800!important;}}
p,label,span,li {{color:{TEXT};}}
small,[data-testid="stCaptionContainer"] {{color:{MUTED}!important;}}
hr {{border-color:{BORDER}!important;}}
header[data-testid="stHeader"] {{background:transparent;}}
section[data-testid="stSidebar"] {{background:{CARD_SOLID};border-right:1px solid {BORDER};}}
section[data-testid="stSidebar"] .block-container {{padding-top:1.5rem;}}
.hero,.glass,.panel,.feature {{
  background:{CARD};border:1px solid {BORDER};border-radius:22px;
  box-shadow:{SHADOW};
}}
.hero {{padding:clamp(26px,4vw,46px);margin:18px 0 24px;position:relative;overflow:hidden;}}
.hero:after {{content:"";position:absolute;width:210px;height:210px;right:-65px;top:-90px;
  border-radius:50%;background:{SOFT};pointer-events:none;}}
.hero h1 {{color:{TEXT}!important;font-size:clamp(30px,4vw,44px)!important;
  line-height:1.12;margin:14px 0 12px;max-width:760px;position:relative;z-index:1;}}
.hero p {{color:{MUTED}!important;font-size:16px;line-height:1.7;max-width:720px;
  margin-bottom:0;position:relative;z-index:1;}}
.hero-badge {{display:inline-flex;background:{SOFT};color:{ACCENT}!important;
  border:1px solid {BORDER};padding:7px 12px;border-radius:999px;font-size:11px;
  font-weight:700;letter-spacing:.09em;}}
.feature {{height:100%;min-height:145px;padding:22px;transition:transform .2s ease;}}
.feature:hover {{transform:translateY(-3px);}}
.feature h3 {{font-size:16px;margin:0 0 7px;}}
.feature p {{color:{MUTED}!important;font-size:13px;line-height:1.6;}}
div[data-testid="stTextInput"] input,div[data-testid="stNumberInput"] input {{
  background:{INPUT_BG}!important;color:{TEXT}!important;border:1px solid {BORDER}!important;
  border-radius:12px!important;min-height:44px;box-shadow:none!important;}}
div[data-testid="stTextInput"] input:focus,div[data-testid="stNumberInput"] input:focus {{
  border-color:{ACCENT}!important;box-shadow:0 0 0 3px {SOFT}!important;}}
div[data-testid="stTextInput"] label,div[data-testid="stNumberInput"] label {{
  color:{TEXT}!important;font-weight:600;font-size:13px;}}
.stButton>button,.stFormSubmitButton>button {{
  background:{ACCENT}!important;color:#fff!important;border:1px solid {ACCENT}!important;
  border-radius:12px!important;padding:10px 18px;min-height:44px;font-weight:700;
  box-shadow:none!important;transition:all .18s ease;}}
.stButton>button:hover,.stFormSubmitButton>button:hover {{
  background:#426B57!important;border-color:#426B57!important;transform:translateY(-1px);}}
.stDownloadButton>button {{background:{SOFT}!important;color:{ACCENT}!important;
  border:1px solid {BORDER}!important;border-radius:12px!important;min-height:44px;font-weight:700;}}
button[data-baseweb="tab"] {{color:{MUTED}!important;font-weight:600;border-radius:10px 10px 0 0!important;padding:12px 16px!important;}}
button[data-baseweb="tab"][aria-selected="true"] {{color:{ACCENT}!important;
  border-bottom:2px solid {ACCENT}!important;background:transparent!important;}}
div[data-testid="stMetric"] {{background:{CARD};border:1px solid {BORDER};
  border-radius:17px;padding:17px 18px;box-shadow:{SHADOW};}}
div[data-testid="stMetricLabel"] {{color:{MUTED}!important;font-size:12px;font-weight:600;}}
div[data-testid="stMetricValue"] {{color:{ACCENT}!important;font-family:'Manrope',sans-serif;font-weight:800;}}
div[data-testid="stDataFrame"] {{border:1px solid {BORDER};border-radius:14px;overflow:hidden;}}
div[data-testid="stChatMessage"] {{background:{CARD};border:1px solid {BORDER};
  border-radius:16px;padding:12px 16px;margin-bottom:10px;}}
div[data-testid="stProgressBar"]>div>div {{background:{ACCENT}!important;border-radius:99px;}}
div[data-testid="stAlert"] {{border-radius:14px;}}
#MainMenu {{visibility:hidden;}} footer {{visibility:hidden;}}
</style>
""", unsafe_allow_html=True)

# =========================================================
# 3 BIS. IDENTITÉ VISUELLE CRÉATIVE — COULEURS & ÉLÉMENTS FLOTTANTS
# =========================================================
st.markdown("""
<style>
/* Fond vivant avec halos colorés */
.stApp {
  background:
    radial-gradient(ellipse at 8% 12%, rgba(160, 210, 197, .23), transparent 31%),
    radial-gradient(ellipse at 92% 18%, rgba(190, 177, 235, .20), transparent 28%),
    radial-gradient(ellipse at 82% 88%, rgba(255, 197, 155, .16), transparent 30%),
    linear-gradient(135deg, #F8FAF8 0%, #F4F7FA 48%, #FBF7F4 100%) !important;
  background-attachment: fixed !important;
}
.block-container {position:relative;z-index:1;}
/* Couleurs plus expressives */
:root {
  --mint:#4F9B83;
  --violet:#8977C7;
  --coral:#E58C78;
  --gold:#D7A84B;
}
.hero {
  background:linear-gradient(118deg,rgba(255,255,255,.97) 0%,rgba(245,250,247,.96) 48%,rgba(247,244,253,.96) 100%) !important;
  border:1px solid rgba(126,158,143,.23) !important;
  box-shadow:0 18px 48px rgba(66,91,79,.09), 0 3px 10px rgba(111,103,151,.035) !important;
}
.hero:before {
  content:"✧";
  position:absolute;right:19%;top:20px;font-size:35px;color:#D7A84B;
  opacity:.65;animation:twinkle 4s ease-in-out infinite;
}
.hero:after {
  width:260px;height:260px;right:-85px;top:-110px;
  background:radial-gradient(circle at 35% 35%,rgba(137,119,199,.19),rgba(79,155,131,.09) 58%,transparent 70%) !important;
}
.hero-badge {
  background:linear-gradient(100deg,#EAF5EF,#F0EDFA) !important;
  color:#587D70 !important;border-color:rgba(137,119,199,.16) !important;
}
.feature {
  position:relative;overflow:hidden;
  background:linear-gradient(145deg,rgba(255,255,255,.98),rgba(247,250,248,.96)) !important;
  box-shadow:0 12px 30px rgba(55,82,69,.055) !important;
}
.feature:after {
  content:"";position:absolute;width:90px;height:90px;right:-38px;bottom:-43px;
  border-radius:50%;background:linear-gradient(135deg,rgba(137,119,199,.14),rgba(229,140,120,.12));
}
.feature:hover {box-shadow:0 17px 34px rgba(76,112,93,.11) !important;}
div[data-testid="stMetric"] {
  background:linear-gradient(145deg,#FFFFFF,#F5F8F7) !important;
  border-color:rgba(113,153,132,.2) !important;
}
div[data-testid="stMetric"]:nth-of-type(3n+1) {border-top:3px solid #77B69D !important;}
div[data-testid="stMetric"]:nth-of-type(3n+2) {border-top:3px solid #A99AD8 !important;}
div[data-testid="stMetric"]:nth-of-type(3n) {border-top:3px solid #E8A28E !important;}
.stButton>button,.stFormSubmitButton>button {
  background:linear-gradient(110deg,#548F79,#6B9E89 58%,#8B80BC) !important;
  border:0 !important;box-shadow:0 7px 18px rgba(83,139,116,.2) !important;
}
.stButton>button:hover,.stFormSubmitButton>button:hover {
  background:linear-gradient(110deg,#477D68,#5D8E7A 58%,#7D70B0) !important;
  box-shadow:0 10px 23px rgba(83,139,116,.27) !important;
}
div[data-testid="stTextInput"] input:focus,div[data-testid="stNumberInput"] input:focus {
  border-color:#8B80BC !important;box-shadow:0 0 0 3px rgba(139,128,188,.13) !important;
}
/* Petits symboles scientifiques animés, décoratifs et non interactifs */
.floating-lab-art {
  position:fixed;inset:0;overflow:hidden;pointer-events:none;z-index:0;
}
.lab-symbol {
  position:absolute;display:block;opacity:.20;user-select:none;
  filter:drop-shadow(0 5px 9px rgba(84,111,98,.08));
  animation:floatAround 13s ease-in-out infinite;
}
.lab-symbol.s1 {top:13%;left:3%;font-size:27px;color:#559B83;animation-delay:-2s;}
.lab-symbol.s2 {top:24%;right:4%;font-size:30px;color:#8B7CC2;animation-delay:-6s;}
.lab-symbol.s3 {top:69%;left:5%;font-size:23px;color:#D88D78;animation-delay:-9s;}
.lab-symbol.s4 {top:79%;right:7%;font-size:28px;color:#D2A84D;animation-delay:-4s;}
.lab-symbol.s5 {top:47%;right:2%;font-size:19px;color:#6DAB99;animation-delay:-7s;}
.lab-symbol.s6 {top:5%;right:28%;font-size:18px;color:#9B8BCB;animation-delay:-1s;}
.lab-orb {
  position:absolute;width:9px;height:9px;border-radius:50%;
  background:linear-gradient(135deg,#8CC9B0,#A99BD8);
  box-shadow:0 0 18px rgba(137,119,199,.35);
  animation:orbDrift 11s ease-in-out infinite;
}
.lab-orb.o1 {top:38%;left:12%;}
.lab-orb.o2 {top:83%;left:43%;width:6px;height:6px;animation-delay:-5s;}
.lab-orb.o3 {top:15%;right:15%;width:7px;height:7px;animation-delay:-3s;}
@keyframes floatAround {
  0%,100% {transform:translate3d(0,0,0) rotate(-8deg);}
  50% {transform:translate3d(9px,-19px,0) rotate(10deg);}
}
@keyframes orbDrift {
  0%,100% {transform:translateY(0) scale(.9);opacity:.45;}
  50% {transform:translateY(-22px) scale(1.3);opacity:.9;}
}
@keyframes twinkle {
  0%,100% {transform:scale(.8) rotate(0);opacity:.35;}
  50% {transform:scale(1.2) rotate(18deg);opacity:.9;}
}
@media (prefers-reduced-motion: reduce) {
  .lab-symbol,.lab-orb,.hero:before {animation:none !important;}
}
@media (max-width: 700px) {
  .lab-symbol {opacity:.10;}
  .lab-symbol.s1,.lab-symbol.s3,.lab-symbol.s5 {display:none;}
}
</style>
<div class="floating-lab-art" aria-hidden="true">
  <span class="lab-symbol s1">⚗</span>
  <span class="lab-symbol s2">✧</span>
  <span class="lab-symbol s3">⌬</span>
  <span class="lab-symbol s4">❋</span>
  <span class="lab-symbol s5">⚛</span>
  <span class="lab-symbol s6">∿</span>
  <i class="lab-orb o1"></i><i class="lab-orb o2"></i><i class="lab-orb o3"></i>
</div>
""", unsafe_allow_html=True)


def get_logo():
    return f"""
    <div style="display:flex;align-items:center;gap:12px;padding:8px">
      <div style="width:46px;height:46px;border-radius:15px;background:{SOFT};
                  display:grid;place-items:center;font-size:23px">⚗️</div>
      <div style="line-height:1.12;text-align:left">
        <div style="font-family:Manrope,sans-serif;font-size:22px;font-weight:800;
                    letter-spacing:-.7px;color:{TEXT}">Process<span style="color:{ACCENT}">Lab</span></div>
        <div style="font-size:10px;font-weight:700;letter-spacing:2.5px;color:{MUTED};
                    margin-top:4px">PROCESS LAB · INDUSTRIE</div>
      </div>
    </div>
    """

def change_language():
    st.session_state.lang = "EN" if st.session_state.lang == "FR" else "FR"
    st.rerun()

def change_theme():
    st.session_state.theme_mode = "light" if st.session_state.theme_mode == "dark" else "dark"
    st.rerun()

def header_controls():
    c1, c2 = st.columns(2)
    with c1:
        if st.button(t("lang_btn"), use_container_width=True):
            change_language()
    with c2:
        if st.button(t("theme_btn"), use_container_width=True):
            change_theme()

# =========================================================
# 4. CALCULS DU PROCÉDÉ
# =========================================================
def calculate_process(p):
    m1 = p["m0"] - p["residus"]
    # Hypothèse : les résidus ne contiennent pas de soluté.
    solute_after_filter = p["m0"] * p["x0_sol"]
    x1 = solute_after_filter / m1 if m1 > 0 else 0.0
    m2 = m1 + p["mR"]
    solute_mixture = solute_after_filter + p["mR"] * p["xR"]
    x2 = solute_mixture / m2 if m2 > 0 else 0.0

    Q3 = m2 * p["cp"] * (p["T3"] - p["T2"]) / 3600
    m4 = solute_mixture / p["x4"] if p["x4"] > 0 else 0.0
    mv = m2 - m4
    Q4 = mv * p["lambda_v"] / 3600
    Q5 = m4 * p["cp"] * 55 / 3600

    feed = p["m0"] + p["mR"]
    output = p["residus"] + mv + m4
    error = feed - output

    return {
        "m1": m1, "x1": x1, "m2": m2, "x2": x2,
        "m4": m4, "mv": mv, "Q3": Q3, "Q4": Q4,
        "Q5": Q5, "feed": feed, "output": output, "error": error,
        "solute": solute_mixture
    }

def validate_params(p):
    errors = []
    if p["m0"] <= 0:
        errors.append("Le débit initial m₀ doit être strictement positif.")
    if p["mR"] < 0:
        errors.append("Le débit d'apport mR ne peut pas être négatif.")
    if not 0 <= p["x0_sol"] <= 1:
        errors.append("La fraction x₀ doit être comprise entre 0 et 1.")
    if not 0 <= p["xR"] <= 1:
        errors.append("La fraction xR doit être comprise entre 0 et 1.")
    if not 0 < p["x4"] <= 1:
        errors.append("La fraction cible x₄ doit être supérieure à 0 et inférieure ou égale à 1.")
    if not 0 <= p["residus"] < p["m0"]:
        errors.append("Les résidus doivent être positifs et inférieurs au débit initial.")
    if p["cp"] <= 0:
        errors.append("La capacité thermique Cp doit être positive.")
    if p["lambda_v"] <= 0:
        errors.append("La chaleur latente doit être positive.")
    if p["T3"] < p["T2"]:
        errors.append("T₃ est inférieur à T₂ : le calcul correspondrait à un refroidissement, pas à un chauffage.")
    return errors

def generate_conclusion(r, p):
    conclusions = []
    if r["mv"] < -1e-9:
        conclusions.append(
            "La concentration du mélange est déjà supérieure à la concentration cible. "
            "Le modèle ne peut pas représenter une dilution : augmentez la cible ou ajoutez une étape de dilution."
        )
    else:
        conclusions.append(
            f"Après filtration, le débit est de {r['m1']:.2f} kg/h. "
            f"Après mélange, le débit atteint {r['m2']:.2f} kg/h."
        )
        conclusions.append(
            f"La concentration du mélange est de {r['x2']*100:.2f} % ; "
            f"la concentration finale visée est de {p['x4']*100:.2f} %."
        )
        conclusions.append(
            f"Le débit final calculé est {r['m4']:.2f} kg/h et le débit évaporé est {r['mv']:.2f} kg/h."
        )
    if abs(r["error"]) <= 1e-6:
        conclusions.append("Le bilan matière est numériquement fermé selon les équations du modèle.")
    else:
        conclusions.append(f"Un écart de bilan de {r['error']:.4f} kg/h est observé.")
    if r["Q4"] > 200:
        conclusions.append(
            f"La puissance d'évaporation calculée est élevée ({r['Q4']:.2f} kW). "
            "Une étude de récupération thermique pourrait être pertinente."
        )
    if r["Q3"] >= 0:
        conclusions.append(f"La puissance thermique de chauffage calculée est de {r['Q3']:.2f} kW.")
    return conclusions

# =========================================================
# 5. RAPPORT PDF AVEC TABLEAUX
# =========================================================
def create_pdf_report(params, results, conclusions, username):
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        PageBreak, KeepTogether
    )
    from xml.sax.saxutils import escape

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=17*mm, leftMargin=17*mm,
        topMargin=25*mm, bottomMargin=18*mm,
        title="Rapport de simulation - Simulateur Pro V2",
        author="Simulateur Pro V2"
    )

    purple = colors.HexColor("#6941C6")
    navy = colors.HexColor("#172554")
    pale = colors.HexColor("#EEF2FF")
    grey = colors.HexColor("#64748B")
    green = colors.HexColor("#DCFCE7")
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="ReportTitle", parent=styles["Title"], fontName="Helvetica-Bold",
        fontSize=19, leading=23, textColor=navy, alignment=TA_CENTER, spaceAfter=5
    ))
    styles.add(ParagraphStyle(
        name="SectionTitle", parent=styles["Heading2"], fontName="Helvetica-Bold",
        fontSize=12, leading=15, textColor=purple, spaceBefore=12, spaceAfter=7
    ))
    styles.add(ParagraphStyle(
        name="SmallCell", parent=styles["BodyText"], fontName="Helvetica",
        fontSize=8.5, leading=11, textColor=navy
    ))
    styles.add(ParagraphStyle(
        name="SmallCellHeader", parent=styles["BodyText"], fontName="Helvetica-Bold",
        fontSize=8.5, leading=11, textColor=colors.white
    ))
    styles.add(ParagraphStyle(
        name="ReportBody", parent=styles["BodyText"], fontSize=9.5,
        leading=14, textColor=navy, spaceAfter=5
    ))

    def cell(value, header=False):
        safe = escape(str(value)).replace("\n", "<br/>")
        return Paragraph(safe, styles["SmallCellHeader" if header else "SmallCell"])

    def make_table(rows, widths=None):
        data = []
        for i, row in enumerate(rows):
            data.append([cell(v, header=(i == 0)) for v in row])
        table = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), purple),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("BACKGROUND", (0, 1), (-1, -1), colors.white),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, pale]),
            ("GRID", (0, 0), (-1, -1), 0.45, colors.HexColor("#D8DEEA")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 7),
            ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        return table

    def page_decor(canvas, document):
        canvas.saveState()
        w, h = A4
        canvas.setFillColor(purple)
        canvas.rect(0, h-13*mm, w, 13*mm, fill=1, stroke=0)
        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica-Bold", 9)
        canvas.drawString(17*mm, h-8.5*mm, "SIMULATEUR PRO V2  |  RAPPORT DE PROCÉDÉ")
        canvas.setStrokeColor(colors.HexColor("#D8DEEA"))
        canvas.line(17*mm, 13*mm, w-17*mm, 13*mm)
        canvas.setFillColor(grey)
        canvas.setFont("Helvetica", 7.5)
        canvas.drawString(17*mm, 8*mm, "Rapport généré automatiquement - Usage pédagogique")
        canvas.drawRightString(w-17*mm, 8*mm, f"Page {document.page}")
        canvas.restoreState()

    story = [
        Spacer(1, 5*mm),
        Paragraph("RAPPORT DE SIMULATION", styles["ReportTitle"]),
        Paragraph("Filtration • Mélange • Chauffage • Évaporation", styles["ReportBody"]),
        Spacer(1, 3*mm),
        make_table([
            ["Informations générales", "Valeur"],
            ["Utilisateur", username],
            ["Date de génération", datetime.now().strftime("%d/%m/%Y à %H:%M")],
            ["Application", "Simulateur Pro V2"],
        ], [65*mm, 105*mm]),
        Paragraph("1. Paramètres opératoires", styles["SectionTitle"]),
        make_table([["Paramètre", "Valeur"]] + [[k, v] for k, v in params.items()], [85*mm, 85*mm]),
        Paragraph("2. Bilan matière", styles["SectionTitle"]),
        make_table([["Grandeur", "Résultat"]] + [[k, v] for k, v in results.get("matter", {}).items()], [85*mm, 85*mm]),
        Paragraph("3. Bilan énergétique", styles["SectionTitle"]),
        make_table([["Grandeur", "Résultat"]] + [[k, v] for k, v in results.get("energy", {}).items()], [85*mm, 85*mm]),
        Paragraph("4. Conclusions et recommandations", styles["SectionTitle"]),
    ]

    for item in conclusions:
        story.append(Paragraph("• " + escape(str(item)), styles["ReportBody"]))

    story.append(Spacer(1, 5*mm))
    story.append(Paragraph(
        "<b>Note sur le modèle :</b> les calculs supposent que les résidus de filtration "
        "ne contiennent pas de soluté et que le soluté est non volatil. "
        "Le bilan matière est calculé à partir des mêmes relations de débit ; "
        "sa fermeture numérique ne constitue donc pas une validation expérimentale indépendante.",
        styles["ReportBody"]
    ))
    doc.build(story, onFirstPage=page_decor, onLaterPages=page_decor)
    buffer.seek(0)
    return buffer.getvalue()

# =========================================================
# 6. ASSISTANT
# =========================================================
def clean_text(text):
    text = text.lower()
    text = "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9\s]", " ", text)).strip()

def generate_bot_response(question):
    p = st.session_state.params
    errors = validate_params(p)
    if errors:
        return "Corrigez d'abord les paramètres : " + " ".join(errors)
    r = calculate_process(p)
    q = clean_text(question)

    if any(x in q for x in ["bonjour", "salut", "salam", "hello", "hi"]):
        return "Bonjour ! Vous pouvez me demander d'expliquer m1, x2, Q3, Q4, le bilan matière ou les hypothèses du modèle."
    if any(x in q for x in ["filtration", "m1", "residu"]):
        return f"Après filtration : m1 = m0 − résidus = {p['m0']:.2f} − {p['residus']:.2f} = **{r['m1']:.2f} kg/h**."
    if any(x in q for x in ["concentration", "x2", "melange"]):
        return f"La concentration massique du mélange est x2 = **{r['x2']*100:.2f} %**."
    if any(x in q for x in ["chauffage", "q3", "temperature"]):
        return f"La puissance de chauffage calculée est Q3 = **{r['Q3']:.2f} kW**."
    if any(x in q for x in ["evaporation", "evaporer", "q4", "mv", "m4"]):
        return f"Débit final m4 = **{r['m4']:.2f} kg/h**, débit évaporé mv = **{r['mv']:.2f} kg/h**, puissance Q4 = **{r['Q4']:.2f} kW**."
    if any(x in q for x in ["bilan", "erreur"]):
        return (
            f"Entrées = {r['feed']:.2f} kg/h ; sorties = {r['output']:.2f} kg/h ; "
            f"écart = **{r['error']:.6f} kg/h**. Attention : cet écart est calculé à partir "
            "des relations du modèle et n'est pas un contrôle expérimental indépendant."
        )
    if any(x in q for x in ["hypothese", "hypotheses", "solute"]):
        return "Le modèle suppose que les résidus filtrés ne contiennent pas de soluté et que le soluté ne s'évapore pas."
    if any(x in q for x in ["pdf", "rapport", "export"]):
        return "Ouvrez l'onglet Conclusion pour télécharger le rapport PDF."
    return "Posez une question sur la filtration, la concentration, le chauffage, l'évaporation ou le bilan matière."

# =========================================================
# 7. PAGE D'ACCUEIL
# =========================================================
def landing_page():
    header_controls()
    st.markdown(get_logo(), unsafe_allow_html=True)
    st.markdown(
        f"""<div class="hero">
        <span class="hero-badge">CHIMIE · GÉNIE DES PROCÉDÉS</span>
        <h1 style="font-size:34px;margin:14px 0 8px">{t('landing_title')}</h1>
        <p>{t('landing_sub')}</p>
        <div style="display:flex;flex-wrap:wrap;gap:8px;margin-top:22px;position:relative;z-index:1">
        <span class="hero-badge">01 · Filtration</span>
        <span class="hero-badge">02 · Chauffage</span>
        <span class="hero-badge">03 · Évaporation</span>
        </div></div>""",
        unsafe_allow_html=True
    )
    c1, c2 = st.columns(2)
    with c1:
        if st.button(t("cta_start"), use_container_width=True):
            st.session_state.page = "auth"
            st.rerun()
    with c2:
        if st.button(t("cta_login"), use_container_width=True):
            st.session_state.page = "auth"
            st.rerun()

    st.write("")
    features = [
        (t("feat1"), t("feat1_d")),
        (t("feat2"), t("feat2_d")),
        (t("feat3"), t("feat3_d")),
        (t("feat4"), t("feat4_d"))
    ]
    cols = st.columns(4)
    for col, (title, desc) in zip(cols, features):
        with col:
            st.markdown(f'<div class="feature"><h3>{title}</h3><p>{desc}</p></div>', unsafe_allow_html=True)

    st.write("")
    st.markdown(f"<h2 style='text-align:center'>{t('how_title')}</h2>", unsafe_allow_html=True)
    steps = [
        (t("step1"), t("step1_d")),
        (t("step2"), t("step2_d")),
        (t("step3"), t("step3_d"))
    ]
    cols = st.columns(3)
    for col, (title, desc) in zip(cols, steps):
        with col:
            st.markdown(f'<div class="feature"><h3>{title}</h3><p>{desc}</p></div>', unsafe_allow_html=True)
    st.markdown(
        f"<p style='text-align:center;color:{MUTED};margin-top:35px'>Simulateur Pro V2 • Conçu pour l'apprentissage du génie des procédés</p>",
        unsafe_allow_html=True
    )

# =========================================================
# 8. PAGE CONNEXION / INSCRIPTION
# =========================================================
def auth_page():
    if st.button(t("back_home")):
        st.session_state.page = "landing"
        st.rerun()

    left, center, right = st.columns([1, 1.6, 1])
    with center:
        st.markdown(get_logo(), unsafe_allow_html=True)
        header_controls()
        login_tab, signup_tab = st.tabs([t("login_tab"), t("signup_tab")])

        with login_tab:
            with st.form("login_form"):
                email = st.text_input(t("email"), placeholder="exemple@email.com")
                password = st.text_input(t("password"), type="password")
                submitted = st.form_submit_button(t("login_btn"), use_container_width=True)
            if submitted:
                if not email or not password:
                    st.error(t("err_fill"))
                else:
                    user = authenticate_user(email.strip(), password)
                    if user:
                        st.session_state.logged_in = True
                        st.session_state.username = user
                        st.session_state.page = "app"
                        st.rerun()
                    else:
                        st.error(t("err_auth"))

        with signup_tab:
            with st.form("signup_form"):
                username = st.text_input(t("username"))
                email = st.text_input(t("email"), placeholder="exemple@email.com")
                password = st.text_input(t("password"), type="password")
                confirm = st.text_input(t("confirm_pass"), type="password")
                submitted = st.form_submit_button(t("signup_btn"), use_container_width=True)
            if submitted:
                if not username or not email or not password or not confirm:
                    st.error(t("err_req"))
                elif not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email.strip()):
                    st.error(t("err_email"))
                elif password != confirm:
                    st.error(t("err_pass"))
                elif len(password) < 8:
                    st.error(t("err_len"))
                elif create_user(username.strip(), email.strip(), password):
                    st.session_state.logged_in = True
                    st.session_state.username = username.strip()
                    st.session_state.page = "app"
                    st.success(t("succ_create"))
                    st.rerun()
                else:
                    st.error(t("err_exist"))

# =========================================================
# 9. PAGE SIMULATEUR
# =========================================================
def simulator_page():
    with st.sidebar:
        st.markdown(get_logo(), unsafe_allow_html=True)
        st.markdown(f"**{t('sidebar_welcome')}, {st.session_state.get('username', 'Utilisateur')}**")
        if st.button(t("lang_btn"), use_container_width=True):
            change_language()
        if st.button(t("theme_btn"), use_container_width=True):
            change_theme()
        st.info(t("info_msg"))
        if st.button(t("logout"), use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.page = "landing"
            st.session_state.messages = []
            st.rerun()

    st.markdown(
        f"""<div class="hero">
        <span class="hero-badge">ESPACE DE SIMULATION</span>
        <h1 style="margin:10px 0 6px">{t('sim_title')}</h1>
        <p>{t('sim_caption')}</p><div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:20px;position:relative;z-index:1"><span class="hero-badge">Filtration</span><span class="hero-badge">Mélange</span><span class="hero-badge">Chauffage</span><span class="hero-badge">Évaporation</span></div></div>""",
        unsafe_allow_html=True
    )

    tab_params, tab_results, tab_conclusion, tab_chat = st.tabs([
        t("tab_params"), t("tab_results"), t("tab_conclusion"), t("tab_chat")
    ])

    with tab_params:
        st.subheader("Données d'entrée du procédé" if st.session_state.lang == "FR" else "Process input data")
        c1, c2 = st.columns(2)
        p0 = st.session_state.params
        with c1:
            m0 = st.number_input(t("m0"), min_value=0.001, value=float(p0["m0"]), step=10.0)
            x0_sol = st.number_input(t("x0"), min_value=0.0, max_value=1.0, value=float(p0["x0_sol"]), step=0.01, format="%.3f")
            residus = st.number_input(t("residus"), min_value=0.0, value=float(p0["residus"]), step=1.0)
            mR = st.number_input(t("mR"), min_value=0.0, value=float(p0["mR"]), step=10.0)
            xR = st.number_input(t("xR"), min_value=0.0, max_value=1.0, value=float(p0["xR"]), step=0.01, format="%.3f")
        with c2:
            T2 = st.number_input(t("T2"), value=float(p0["T2"]), step=1.0)
            T3 = st.number_input(t("T3"), value=float(p0["T3"]), step=1.0)
            cp = st.number_input(t("cp"), min_value=0.001, value=float(p0["cp"]), step=0.1)
            x4 = st.number_input(t("x4"), min_value=0.001, max_value=1.0, value=float(p0["x4"]), step=0.01, format="%.3f")
            lambda_v = st.number_input(t("lambda_v"), min_value=0.001, value=float(p0["lambda_v"]), step=10.0)

        st.session_state.params = {
            "m0": m0, "x0_sol": x0_sol, "residus": residus, "mR": mR,
            "xR": xR, "T2": T2, "T3": T3, "cp": cp, "x4": x4,
            "lambda_v": lambda_v
        }
        st.caption("Hypothèse de calcul : les résidus de filtration sont supposés exempts de soluté.")

    p = st.session_state.params
    validation_errors = validate_params(p)

    if validation_errors:
        with tab_results:
            st.error("Impossible d'effectuer une simulation cohérente avec les paramètres actuels.")
            for error in validation_errors:
                st.write("• " + error)
        with tab_conclusion:
            st.warning("Corrigez les paramètres dans l'onglet Paramètres pour obtenir le rapport.")
        with tab_chat:
            st.info("L'assistant sera disponible après correction des paramètres.")
        return

    r = calculate_process(p)
    conclusions = generate_conclusion(r, p)

    if r["mv"] < -1e-9:
        simulation_warning = (
            "La concentration initiale du mélange est supérieure à la concentration finale visée. "
            "Le calcul donne un débit évaporé négatif : ce cas nécessite une dilution et n'est pas représenté par ce modèle."
        )
    else:
        simulation_warning = None

    with tab_results:
        st.subheader(t("res_real_time"))
        if simulation_warning:
            st.warning(simulation_warning)

        metrics = [
            (t("metric_m1"), f"{r['m1']:,.2f} kg/h"),
            (t("metric_x2"), f"{r['x2']*100:.2f} %"),
            (t("metric_m4"), f"{r['m4']:,.2f} kg/h"),
            (t("metric_mv"), f"{r['mv']:,.2f} kg/h"),
            (t("metric_Q3"), f"{r['Q3']:,.2f} kW"),
            (t("metric_Q4"), f"{r['Q4']:,.2f} kW"),
            (t("metric_Q5"), f"{r['Q5']:,.2f} kW"),
            (t("metric_err"), f"{r['error']:,.6f} kg/h")
        ]
        for start in (0, 4):
            cols = st.columns(4)
            for col, (label, value) in zip(cols, metrics[start:start+4]):
                with col:
                    st.metric(label, value)

        st.divider()
        st.markdown("### Tableau 1 — Paramètres opératoires")
        params_table = pd.DataFrame([
            ["Débit initial m₀", p["m0"], "kg/h"],
            ["Fraction massique x₀", p["x0_sol"], "—"],
            ["Résidus de filtration", p["residus"], "kg/h"],
            ["Débit d'apport mR", p["mR"], "kg/h"],
            ["Fraction massique xR", p["xR"], "—"],
            ["Température T₂", p["T2"], "°C"],
            ["Température T₃", p["T3"], "°C"],
            ["Capacité thermique Cp", p["cp"], "kJ/(kg·K)"],
            ["Fraction finale visée x₄", p["x4"], "—"],
            ["Chaleur latente λv", p["lambda_v"], "kJ/kg"]
        ], columns=["Paramètre", "Valeur", "Unité"])
        st.dataframe(params_table, use_container_width=True, hide_index=True)

        st.markdown("### Tableau 2 — Bilan matière")
        matter_table = pd.DataFrame([
            ["Alimentation initiale (m₀)", p["m0"], "kg/h"],
            ["Résidus de filtration", p["residus"], "kg/h"],
            ["Débit après filtration (m₁)", r["m1"], "kg/h"],
            ["Apport ajouté (mR)", p["mR"], "kg/h"],
            ["Débit du mélange (m₂)", r["m2"], "kg/h"],
            ["Concentration du mélange (x₂)", r["x2"]*100, "%"],
            ["Produit final (m₄)", r["m4"], "kg/h"],
            ["Eau évaporée (mv)", r["mv"], "kg/h"],
            ["Total des entrées", r["feed"], "kg/h"],
            ["Total des sorties", r["output"], "kg/h"],
            ["Écart calculé", r["error"], "kg/h"]
        ], columns=["Grandeur", "Valeur", "Unité"])
        st.dataframe(matter_table, use_container_width=True, hide_index=True)

        st.markdown("### Tableau 3 — Bilan énergétique")
        energy_table = pd.DataFrame([
            ["Chauffage du mélange (Q₃)", r["Q3"], "kW"],
            ["Évaporation (Q₄)", r["Q4"], "kW"],
            ["Refroidissement du produit (Q₅)", r["Q5"], "kW"]
        ], columns=["Opération", "Puissance", "Unité"])
        st.dataframe(energy_table, use_container_width=True, hide_index=True)

        st.divider()
        st.markdown(f"### {t('graphs')}")
        g1, g2 = st.columns(2)
        with g1:
            st.caption("Évolution des débits massiques")
            flow_df = pd.DataFrame({
                "Étape": ["Initial", "Après filtration", "Après mélange", "Produit final"],
                "Débit (kg/h)": [p["m0"], r["m1"], r["m2"], r["m4"]]
            }).set_index("Étape")
            st.bar_chart(flow_df)
        with g2:
            st.caption("Puissances thermiques")
            energy_df = pd.DataFrame({
                "Opération": ["Chauffage", "Évaporation", "Refroidissement"],
                "Puissance (kW)": [r["Q3"], r["Q4"], r["Q5"]]
            }).set_index("Opération")
            st.bar_chart(energy_df)

        st.markdown(f"**{t('obj_reach')}**")
        ratio = max(0.0, min(r["x2"] / p["x4"], 1.0))
        st.progress(ratio)
        st.caption(f"{t('obj_text')} : {p['x4']*100:.2f} % | Concentration obtenue : {r['x2']*100:.2f} %")

        st.info(
            "Remarque : l'écart du bilan est calculé avec m₄ et mv issus des mêmes équations "
            "de conservation. Une valeur nulle confirme la cohérence arithmétique du modèle, "
            "mais ne remplace pas une validation expérimentale."
        )

    with tab_conclusion:
        st.subheader(t("concl_title"))
        if simulation_warning:
            st.warning(simulation_warning)
        for item in conclusions:
            st.markdown(f"- {item}")

        if not simulation_warning and r["x2"] >= p["x4"]:
            st.success("La concentration cible est atteinte ou dépassée selon le modèle.")
        elif not simulation_warning:
            st.warning("La concentration cible n'est pas atteinte.")

        params_pdf = {
            "Débit initial m₀": f"{p['m0']:.2f} kg/h",
            "Fraction massique x₀": f"{p['x0_sol']:.4f}",
            "Résidus": f"{p['residus']:.2f} kg/h",
            "Débit d'apport mR": f"{p['mR']:.2f} kg/h",
            "Fraction massique xR": f"{p['xR']:.4f}",
            "Température T₂": f"{p['T2']:.2f} °C",
            "Température T₃": f"{p['T3']:.2f} °C",
            "Capacité thermique Cp": f"{p['cp']:.3f} kJ/(kg·K)",
            "Fraction cible x₄": f"{p['x4']:.4f}",
            "Chaleur latente λv": f"{p['lambda_v']:.2f} kJ/kg"
        }
        results_pdf = {
            "matter": {
                "Débit après filtration m₁": f"{r['m1']:.2f} kg/h",
                "Débit du mélange m₂": f"{r['m2']:.2f} kg/h",
                "Concentration x₂": f"{r['x2']*100:.2f} %",
                "Débit final m₄": f"{r['m4']:.2f} kg/h",
                "Débit évaporé mv": f"{r['mv']:.2f} kg/h",
                "Total des entrées": f"{r['feed']:.2f} kg/h",
                "Total des sorties": f"{r['output']:.2f} kg/h",
                "Écart calculé": f"{r['error']:.6f} kg/h"
            },
            "energy": {
                "Puissance de chauffage Q₃": f"{r['Q3']:.2f} kW",
                "Puissance d'évaporation Q₄": f"{r['Q4']:.2f} kW",
                "Puissance de refroidissement Q₅": f"{r['Q5']:.2f} kW"
            }
        }
        pdf_bytes = create_pdf_report(
            params_pdf, results_pdf, conclusions,
            st.session_state.get("username", "Utilisateur")
        )
        st.download_button(
            t("export_pdf"), data=pdf_bytes,
            file_name="rapport_simulateur_pro_v2.pdf",
            mime="application/pdf", use_container_width=True
        )
        st.caption("Le rapport contient les paramètres opératoires, les tableaux des bilans matière et énergétique ainsi que les recommandations.")

    with tab_chat:
        st.subheader(t("chat_title"))
        if "messages" not in st.session_state:
            st.session_state.messages = [{
                "role": "assistant",
                "content": "Bonjour ! Je peux expliquer les calculs de filtration, de chauffage, d'évaporation et les bilans."
            }]
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        prompt = st.chat_input(t("chat_placeholder"))
        if prompt:
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            response = generate_bot_response(prompt)
            st.session_state.messages.append({"role": "assistant", "content": response})
            with st.chat_message("assistant"):
                st.markdown(response)

    st.markdown(
        f"<p style='text-align:center;color:{MUTED};margin-top:35px'>Simulateur Pro V2 • Génie des procédés</p>",
        unsafe_allow_html=True
    )

# =========================================================
# 10. ROUTAGE
# =========================================================
if st.session_state.logged_in and st.session_state.page == "app":
    simulator_page()
elif st.session_state.page == "auth":
    auth_page()
else:
    landing_page()
