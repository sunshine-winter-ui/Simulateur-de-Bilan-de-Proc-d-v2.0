import streamlit as st
import sqlite3
import bcrypt
import re

# --- 1. CONFIG ---
st.set_page_config(page_title="Simulateur Pro", layout="wide", page_icon="🧪")

# --- 2. BASE DE DONNÉES ---
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL)''')
    conn.commit()
    conn.close()
init_db()

def hash_password(p): return bcrypt.hashpw(p.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
def verify_password(p, h): return bcrypt.checkpw(p.encode('utf-8'), h.encode('utf-8'))

def email_exists(email):
    conn = sqlite3.connect('users.db'); c = conn.cursor()
    c.execute("SELECT 1 FROM users WHERE email = ?", (email,)); r = c.fetchone(); conn.close()
    return r is not None

def create_user(username, email, password):
    conn = sqlite3.connect('users.db'); c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)", (username, email, hash_password(password)))
        conn.commit(); return True
    except sqlite3.IntegrityError: return False
    finally: conn.close()

def authenticate_user(email, password):
    conn = sqlite3.connect('users.db'); c = conn.cursor()
    c.execute("SELECT username, password_hash FROM users WHERE email = ?", (email,))
    r = c.fetchone(); conn.close()
    if r and verify_password(password, r[1]): return r[0]
    return None

# --- 3. THEME DYNAMIQUE ELEGANT ---
if 'theme_mode' not in st.session_state:
    st.session_state.theme_mode = 'light'

is_dark = st.session_state.theme_mode == 'dark'

# Variables selon le thème
if is_dark:
    BG = "#0f172a"; CARD = "rgba(30,41,59,0.85)"; TEXT = "#f1f5f9"; MUTED = "#94a3b8"
    INPUT_BG = "#1e293b"; INPUT_BORDER = "#334155"; ACCENT = "#38bdf8"; ACCENT2 = "#818cf8"
    SHADOW = "0 10px 30px rgba(0,0,0,0.4)"
else:
    BG = "#eef2f7"; CARD = "rgba(255,255,255,0.95)"; TEXT = "#1e293b"; MUTED = "#64748b"
    INPUT_BG = "#ffffff"; INPUT_BORDER = "#e2e8f0"; ACCENT = "#2563eb"; ACCENT2 = "#7c3aed"
    SHADOW = "0 10px 30px rgba(0,0,0,0.08)"

st.markdown(f"""
<style>
    .stApp {{ background: {BG}; color: {TEXT}; transition: all 0.3s ease; }}
    .stApp::before {{
        content:""; position:fixed; inset:0; z-index:-1;
        background: radial-gradient(600px at 10% 10%, {ACCENT}22, transparent),
                    radial-gradient(600px at 90% 90%, {ACCENT2}22, transparent);
    }}
    h1,h2,h3,p,span,label,div {{ color: {TEXT} !important; }}
    .muted {{ color: {MUTED} !important; }}

    /* --- Carte Glass --- */
    .glass {{
        background: {CARD}; backdrop-filter: blur(12px);
        border-radius: 20px; padding: 28px;
        box-shadow: {SHADOW}; border: 1px solid {INPUT_BORDER};
        animation: fadeUp 0.5s ease;
    }}
    @keyframes fadeUp {{ from {{ opacity:0; transform: translateY(12px); }} to {{ opacity:1; transform: translateY(0); }} }}

    /* --- Inputs --- */
    div[data-testid="stTextInput"] input, div[data-testid="stNumberInput"] input {{
        background: {INPUT_BG} !important; color: {TEXT} !important;
        border: 1px solid {INPUT_BORDER} !important; border-radius: 12px !important;
        padding: 12px !important;
    }}
    div[data-testid="stTextInput"] input:focus, div[data-testid="stNumberInput"] input:focus {{
        border-color: {ACCENT} !important; box-shadow: 0 0 0 3px {ACCENT}33 !important;
    }}
    label {{ font-weight: 600 !important; font-size: 14px !important; }}

    /* --- Boutons --- */
    .stButton>button {{
        background: linear-gradient(135deg, {ACCENT}, {ACCENT2}) !important;
        color: white !important; border: none !important; border-radius: 12px !important;
        padding: 12px 20px !important; font-weight: 700 !important; font-size: 15px !important;
        box-shadow: 0 6px 20px {ACCENT}44; transition: 0.2s;
    }}
    .stButton>button:hover {{ transform: translateY(-2px); box-shadow: 0 10px 25px {ACCENT}55; color:white !important; }}

    /* --- Metrics --- */
    div[data-testid="stMetric"] {{
        background: {CARD} !important; border: 1px solid {INPUT_BORDER} !important;
        border-radius: 16px !important; padding: 18px !important;
        box-shadow: {SHADOW} !important; transition: 0.2s;
    }}
    div[data-testid="stMetric"]:hover {{ transform: translateY(-3px); }}
    div[data-testid="stMetricValue"] {{ color: {ACCENT} !important; font-size: 26px !important; }}
    div[data-testid="stMetricLabel"] {{ color: {MUTED} !important; font-weight: 600 !important; }}

    /* --- Tabs --- */
    button[data-baseweb="tab"] {{ color: {MUTED} !important; font-weight: 600 !important; }}
    button[data-baseweb="tab"][aria-selected="true"] {{
        color: {ACCENT} !important; border-bottom: 3px solid {ACCENT} !important;
        background: {CARD} !important; border-radius: 12px 12px 0 0;
    }}

    /* --- Sidebar --- */
    section[data-testid="stSidebar"] {{ background: {CARD} !important; border-right: 1px solid {INPUT_BORDER}; }}
    section[data-testid="stSidebar"] * {{ color: {TEXT} !important; }}

    /* --- Chat --- */
    div[data-testid="stChatMessage"] {{ background: {CARD} !important; border: 1px solid {INPUT_BORDER} !important; border-radius: 16px !important; }}
    div[data-testid="stChatInput"] textarea {{ background: {INPUT_BG} !important; color: {TEXT} !important; }}

    /* --- Alertes --- */
    div[data-testid="stAlert"] {{ border-radius: 12px !important; background: {CARD} !important; color: {TEXT} !important; border: 1px solid {INPUT_BORDER} !important; }}

    #MainMenu {{visibility: hidden;}}
    header {{ background: transparent !important; }}
</style>
""", unsafe_allow_html=True)

# --- 4. CHATBOT ---
def generate_bot_response(user_input):
    u = user_input.lower()
    if "bonjour" in u or "salut" in u: return "Bonjour ! Je suis votre assistant. Posez-moi des questions sur la filtration, le chauffage ou l'évaporation."
    elif "aide" in u or "comment" in u: return "Modifiez les valeurs dans l'onglet 'Paramètres', puis allez dans 'Résultats' pour voir les calculs et les graphiques."
    elif "filtration" in u: return "La filtration retire les particules insolubles. Le débit final est m1 = m0 - résidus."
    elif "chauffage" in u: return "Le chauffage sert à augmenter la température. La puissance dépend de la capacité calorifique (Cp)."
    elif "évaporation" in u or "vapeur" in u: return "L'évaporation retire de l'eau. La puissance Q4 est calculée avec la chaleur latente (lambda_v)."
    elif "graphique" in u or "courbe" in u: return "Les graphiques dans l'onglet Résultats vous montrent l'évolution des débits et la répartition des puissances."
    else: return "Je n'ai pas compris. Essayez 'Comment ça marche ?' ou demandez-moi des détails sur la 'filtration'."

# --- 5. AUTH PAGE REDESIGNÉE ---
def auth_page():
    c1, c2, c3 = st.columns([1, 1.6, 1])
    with c2:
        st.markdown(f"""
        <div class="glass" style="text-align:center; margin-top:20px;">
            <div style="font-size:52px;">🧪</div>
            <h1 style="margin:0; font-size:28px; background: linear-gradient(135deg, {ACCENT}, {ACCENT2}); -webkit-background-clip:text; -webkit-text-fill-color:transparent;">Simulateur Pro</h1>
            <p class="muted" style="margin-top:6px;">Simulateur de procédés industriels • Filtration • Chauffage • Évaporation</p>
        </div>
        """, unsafe_allow_html=True)
        st.write("")
        # Toggle thème sur auth aussi
        col_t1, col_t2 = st.columns([3,1])
        with col_t2:
            if st.button("🌙 Sombre" if not is_dark else "☀️ Clair", key="theme_auth"):
                st.session_state.theme_mode = 'dark' if not is_dark else 'light'
                st.rerun()

        tab1, tab2 = st.tabs(["🔑  Se connecter", "📝  Créer un compte"])
        with tab1:
            st.markdown('<div class="glass">', unsafe_allow_html=True)
            with st.form("login_form", clear_on_submit=False):
                email = st.text_input("📧 Email", placeholder="exemple@email.com")
                password = st.text_input("🔒 Mot de passe", type="password", placeholder="••••••••")
                if st.form_submit_button("Se connecter →"):
                    if not email or not password: st.error("Veuillez remplir tous les champs.")
                    else:
                        user = authenticate_user(email, password)
                        if user:
                            st.session_state['logged_in'] = True; st.session_state['username'] = user; st.rerun()
                        else: st.error("Email ou mot de passe incorrect.")
            st.markdown('</div>', unsafe_allow_html=True)
        with tab2:
            st.markdown('<div class="glass">', unsafe_allow_html=True)
            with st.form("signup_form"):
                new_username = st.text_input("👤 Nom d'utilisateur", placeholder="Votre pseudo")
                new_email = st.text_input("📧 Email", placeholder="exemple@email.com")
                new_password = st.text_input("🔒 Mot de passe (min. 8 carac.)", type="password")
                confirm_password = st.text_input("🔒 Confirmer le mot de passe", type="password")
                if st.form_submit_button("Créer mon compte ✨"):
                    if not new_username or not new_email or not new_password: st.error("Tous les champs sont obligatoires.")
                    elif not re.match(r"[^@]+@[^@]+\.[^@]+", new_email): st.error("Format d'email invalide.")
                    elif new_password != confirm_password: st.error("Les mots de passe ne correspondent pas.")
                    elif len(new_password) < 8: st.error("Le mot de passe doit contenir au moins 8 caractères.")
                    elif email_exists(new_email): st.warning("Cet email est déjà utilisé.")
                    else:
                        if create_user(new_username, new_email, new_password):
                            st.session_state['logged_in'] = True; st.session_state['username'] = new_username
                            st.success("Compte créé !"); st.rerun()
                        else: st.error("Erreur lors de la création.")
            st.markdown('</div>', unsafe_allow_html=True)

# --- 6. SIMULATEUR ---
def simulator_page():
    with st.sidebar:
        st.markdown(f"<h2>🧪 Simulateur Pro</h2><p class='muted'>Bonjour, <b>{st.session_state.get('username')}</b></p>", unsafe_allow_html=True)
        st.write("---")
        st.subheader("🎨 Apparence")
        # Bouton toggle élégant
        if st.button("🌙 Passer en Sombre" if not is_dark else "☀️ Passer en Clair"):
            st.session_state.theme_mode = 'dark' if not is_dark else 'light'
            st.rerun()
        st.caption("Le thème s'applique à toute l'interface instantanément.")
        st.write("---")
        st.info("💡 Modifiez les paramètres puis consultez l'onglet Résultats.")

    st.markdown(f"""
    <div style="display:flex; justify-content:space-between; align-items:center;">
        <div><h1 style="margin:0;">🧪 Simulateur de Bilan</h1><p class="muted">Ajustez les paramètres pour voir les résultats évoluer en temps réel.</p></div>
        <div style="background:{CARD}; padding:10px 16px; border-radius:50px; border:1px solid {INPUT_BORDER};">👤 {st.session_state.get('username','Utilisateur')} • {'🌙 Dark' if is_dark else '☀️ Light'}</div>
    </div>
    """, unsafe_allow_html=True)
    st.write("")

    tab_params, tab_results, tab_chat = st.tabs(["⚙️ Paramètres d'entrée", "📊 Résultats & Graphiques", "🤖 Assistant Virtuel"])

    with tab_params:
        st.markdown('<div class="glass">', unsafe_allow_html=True)
        st.subheader("Réglages du procédé")
        col1, col2 = st.columns(2)
        with col1:
            m0 = st.number_input("Débit massique initial (kg/h)", value=1000.0)
            x0_sol = st.number_input("Fraction massique solubles (0-1)", value=0.10)
            residus = st.number_input("Résidus filtrés (kg/h)", value=20.0)
            mR = st.number_input("Apport de jus concentré (kg/h)", value=100.0)
            xR = st.number_input("Concentration de l'apport (0-1)", value=0.40)
        with col2:
            T2 = st.number_input("Température d'entrée (°C)", value=20.0)
            T3 = st.number_input("Température après chauffage (°C)", value=80.0)
            cp = st.number_input("Capacité calorifique Cp [kJ/(kg·K)]", value=3.8)
            x4 = st.number_input("Concentration finale visée (0-1)", value=0.40)
            lambda_v = st.number_input("Chaleur latente [kJ/kg]", value=2300.0)
        st.markdown('</div>', unsafe_allow_html=True)
        # On sauvegarde pour l'onglet résultats
        st.session_state.params = dict(m0=m0, x0_sol=x0_sol, residus=residus, mR=mR, xR=xR, T2=T2, T3=T3, cp=cp, x4=x4, lambda_v=lambda_v)

    # Récupération params (par défaut si jamais)
    p = st.session_state.get('params', dict(m0=1000.0, x0_sol=0.10, residus=20.0, mR=100.0, xR=0.40, T2=20.0, T3=80.0, cp=3.8, x4=0.40, lambda_v=2300.0))
    m1 = p['m0'] - p['residus']; x1 = (p['m0']*p['x0_sol'])/m1 if m1>0 else 0
    m2 = m1 + p['mR']; x2 = (m1*x1 + p['mR']*p['xR'])/m2 if m2>0 else 0
    Q3 = m2 * p['cp'] * (p['T3']-p['T2'])/3600
    m4 = m2*x2/p['x4'] if p['x4']>0 else 0; mv = m2-m4; Q4 = mv*p['lambda_v']/3600
    T4,T5 = 80,25; Q5 = m4*p['cp']*(T4-T5)/3600
    erreur = (p['m0']+p['mR']) - (p['residus']+mv+m4)

    with tab_results:
        st.subheader("Résultats en temps réel")
        r1,r2,r3 = st.columns(3)
        r1.metric("Débit après filtration", f"{m1:,.2f} kg/h"); r2.metric("Concentration mélange", f"{x2*100:.2f} %"); r3.metric("Débit concentré final", f"{m4:,.2f} kg/h")
        r4,r5,r6 = st.columns(3)
        r4.metric("Eau évaporée", f"{mv:,.2f} kg/h"); r5.metric("Puissance chauffage", f"{Q3:,.2f} kW"); r6.metric("Puissance évaporation", f"{Q4:,.2f} kW")
        r7,r8 = st.columns(2)
        r7.metric("Puissance refroidissement", f"{Q5:,.2f} kW"); r8.metric("Erreur bilan global", f"{erreur:,.2f} kg/h", delta=f"{erreur:,.2f}", delta_color="inverse")
        st.write("")
        st.markdown('<div class="glass">', unsafe_allow_html=True)
        st.subheader("📈 Visualisation")
        gc1, gc2 = st.columns(2)
        with gc1:
            st.write("**Évolution des débits (kg/h)**")
            st.bar_chart({"Étape": ["Initial (m0)","Filtré (m1)","Mélangé (m2)","Final (m4)"], "Débit":[p['m0'],m1,m2,m4]}, x="Étape", y="Débit", color=ACCENT)
        with gc2:
            st.write("**Besoins énergétiques (kW)**")
            st.bar_chart({"Opération":["Chauffage (Q3)","Évaporation (Q4)","Refroidissement (Q5)"], "Puissance":[Q3,Q4,Q5]}, x="Opération", y="Puissance", color="#e74c3c")
        st.write("**Atteinte de l'objectif de concentration**")
        st.progress(min(x2/p['x4'] if p['x4']>0 else 1.0, 1.0))
        st.caption(f"Objectif visé : {p['x4']*100}% | Actuel : {x2*100:.2f}%")
        st.markdown('</div>', unsafe_allow_html=True)

    with tab_chat:
        st.markdown('<div class="glass">', unsafe_allow_html=True)
        st.subheader("🤖 Assistant Virtuel")
        if "messages" not in st.session_state: st.session_state.messages = [{"role":"assistant","content":"Bonjour ! Une question sur les calculs ou les graphiques ?"}]
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"])
        if prompt := st.chat_input("Posez votre question ici..."):
            st.session_state.messages.append({"role":"user","content":prompt})
            with st.chat_message("user"): st.markdown(prompt)
            resp = generate_bot_response(prompt)
            st.session_state.messages.append({"role":"assistant","content":resp})
            with st.chat_message("assistant"): st.markdown(resp)
        st.markdown('</div>', unsafe_allow_html=True)

# --- 7. MAIN ---
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if not st.session_state['logged_in']:
    auth_page()
else:
    if st.sidebar.button("🚪 Se déconnecter"):
        st.session_state['logged_in'] = False; st.session_state['messages'] = []; st.rerun()
    simulator_page()
