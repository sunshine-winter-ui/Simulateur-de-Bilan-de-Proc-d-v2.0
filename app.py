import streamlit as st
import sqlite3
import bcrypt
import re

st.set_page_config(page_title="Simulateur Pro", layout="wide", page_icon="🧪")

# --- DB ---
def init_db():
    conn = sqlite3.connect('users.db'); c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL, email TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL)''')
    conn.commit(); conn.close()
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

# --- THEME ---
if 'theme_mode' not in st.session_state: st.session_state.theme_mode = 'light'
is_dark = st.session_state.theme_mode == 'dark'
if is_dark:
    BG="#0f172a"; CARD="#1e293b"; TEXT="#f1f5f9"; MUTED="#94a3b8"; INPUT_BG="#1e293b"; INPUT_BORDER="#334155"; ACCENT="#38bdf8"; ACCENT2="#818cf8"
else:
    BG="#eef2f7"; CARD="#ffffff"; TEXT="#1e293b"; MUTED="#64748b"; INPUT_BG="#ffffff"; INPUT_BORDER="#e2e8f0"; ACCENT="#2563eb"; ACCENT2="#7c3aed"

st.markdown(f"""
<style>
    .stApp {{ background: {BG}; color: {TEXT}; }}
    h1,h2,h3,p,span,label,div {{ color: {TEXT} !important; }}
    div[data-testid="stTextInput"] input, div[data-testid="stNumberInput"] input {{
        background: {INPUT_BG} !important; color: {TEXT} !important;
        border: 1px solid {INPUT_BORDER} !important; border-radius: 12px !important;
    }}
    .stButton>button {{
        background: linear-gradient(135deg, {ACCENT}, {ACCENT2}) !important;
        color: white !important; border: none !important; border-radius: 12px !important;
        font-weight: 700 !important; width: 100%;
    }}
    div[data-testid="stMetric"] {{
        background: {CARD} !important; border: 1px solid {INPUT_BORDER} !important;
        border-radius: 16px !important; padding: 16px !important;
    }}
    div[data-testid="stMetricValue"] {{ color: {ACCENT} !important; }}
    div[data-testid="stMetricLabel"] {{ color: {MUTED} !important; }}
    section[data-testid="stSidebar"] {{ background: {CARD} !important; }}
    section[data-testid="stSidebar"] * {{ color: {TEXT} !important; }}
    #MainMenu {{visibility: hidden;}}
    /* Cacher les blocs vides */
    div[data-testid="stVerticalBlock"] > div:empty {{ display: none !important; }}
    div[data-testid="stMarkdownContainer"] > div:empty {{ display: none !important; }}
</style>
""", unsafe_allow_html=True)

def generate_bot_response(u):
    u = u.lower()
    if "bonjour" in u or "salut" in u: return "Bonjour ! Posez-moi des questions sur la filtration, le chauffage ou l'évaporation."
    elif "filtration" in u: return "La filtration retire les particules. m1 = m0 - résidus."
    elif "chauffage" in u: return "Le chauffage augmente la température. Q3 = m2 * Cp * (T3-T2) / 3600."
    elif "évaporation" in u or "vapeur" in u: return "L'évaporation retire de l'eau. Q4 = mv * lambda_v / 3600."
    else: return "Essayez 'Comment ça marche ?' ou demandez-moi la 'filtration'."

# --- NOUVELLE FONCTION CONCLUSION ---
def generate_conclusion(m1,m2,m4,mv,Q3,Q4,Q5,x2,x4,erreur):
    conclusions = []
    # 1. Bilan matière
    if abs(erreur) > 1:
        conclusions.append(f"⚠️ **Bilan matière déséquilibré :** Erreur de {erreur:.2f} kg/h. Vérifiez vos saisies (m0, mR, résidus). Un bilan doit être proche de 0.")
    else:
        conclusions.append("✅ **Bilan matière équilibré :** Entrées = Sorties. Vos calculs sont cohérents.")

    # 2. Concentration
    taux = (x2 / x4 * 100) if x4>0 else 0
    if taux < 95:
        conclusions.append(f"🔴 **Concentration insuffisante :** Vous êtes à {x2*100:.1f}% au lieu de {x4*100:.0f}% visé ({taux:.0f}% de l'objectif). **Que faire ?** Augmentez l'évaporation (plus de vapeur), ou augmentez T3, ou diminuez l'apport mR.")
    elif taux < 100:
        conclusions.append(f"🟡 **Presque atteint :** Vous êtes à {taux:.0f}% de l'objectif. Augmentez légèrement la puissance d'évaporation Q4.")
    else:
        conclusions.append(f"✅ **Objectif atteint :** Concentration de {x2*100:.1f}% >= {x4*100:.0f}% visé. Le produit est conforme.")

    # 3. Energie
    total_Q = Q3+Q4+Q5
    if Q4 > 200:
        conclusions.append(f"💡 **Énergie élevée :** Q4 = {Q4:.1f} kW est important. **Conseil :** Vérifiez si vous pouvez récupérer la chaleur du refroidissement (Q5 = {Q5:.1f} kW) pour préchauffer l'entrée et économiser.")
    if mv <= 0:
        conclusions.append("⚠️ **Aucune évaporation :** mv = 0. Le mélange est déjà plus concentré que l'objectif. Diminuez xR ou augmentez x4.")

    # 4. Recommandation finale
    if abs(erreur) <= 1 and taux >= 100:
        conclusions.append("🎯 **Action recommandée :** Procédé stable. Vous pouvez lancer la production et surveiller T3 et Q4 en continu.")
    elif abs(erreur) <= 1:
        conclusions.append("🎯 **Action recommandée :** Corrigez d'abord la concentration avant de lancer la production.")
    
    return conclusions

# --- AUTH ---
def auth_page():
    c1,c2,c3 = st.columns([1,1.6,1])
    with c2:
        st.markdown(f"<h1 style='text-align:center; background: linear-gradient(135deg, {ACCENT}, {ACCENT2}); -webkit-background-clip:text; -webkit-text-fill-color:transparent;'>🧪 Simulateur Pro</h1><p style='text-align:center; color:{MUTED};'>Filtration • Chauffage • Évaporation</p>", unsafe_allow_html=True)
        if st.button("🌙 Sombre" if not is_dark else "☀️ Clair"):
            st.session_state.theme_mode = 'dark' if not is_dark else 'light'; st.rerun()
        tab1, tab2 = st.tabs(["🔑 Se connecter", "📝 Créer un compte"])
        with tab1:
            with st.form("login_form"):
                email = st.text_input("📧 Email", placeholder="exemple@email.com")
                password = st.text_input("🔒 Mot de passe", type="password")
                if st.form_submit_button("Se connecter →"):
                    if not email or not password: st.error("Veuillez remplir tous les champs.")
                    else:
                        user = authenticate_user(email, password)
                        if user: st.session_state['logged_in']=True; st.session_state['username']=user; st.rerun()
                        else: st.error("Email ou mot de passe incorrect.")
        with tab2:
            with st.form("signup_form"):
                nu = st.text_input("👤 Nom d'utilisateur"); ne = st.text_input("📧 Email"); npw = st.text_input("🔒 Mot de passe", type="password"); cpw = st.text_input("🔒 Confirmer", type="password")
                if st.form_submit_button("Créer mon compte ✨"):
                    if not nu or not ne or not npw: st.error("Tous les champs sont obligatoires.")
                    elif not re.match(r"[^@]+@[^@]+\.[^@]+", ne): st.error("Email invalide.")
                    elif npw != cpw: st.error("Mots de passe différents.")
                    elif len(npw) < 8: st.error("Min. 8 caractères.")
                    elif email_exists(ne): st.warning("Email déjà utilisé.")
                    else:
                        if create_user(nu, ne, npw): st.session_state['logged_in']=True; st.session_state['username']=nu; st.success("Compte créé !"); st.rerun()
                        else: st.error("Erreur création.")

# --- SIMULATEUR ---
def simulator_page():
    with st.sidebar:
        st.markdown(f"### 🧪 Simulateur Pro\nBonjour, **{st.session_state.get('username')}**")
        if st.button("🌙 Sombre" if not is_dark else "☀️ Clair"):
            st.session_state.theme_mode = 'dark' if not is_dark else 'light'; st.rerun()
        st.info("💡 Modifiez les paramètres puis allez dans Résultats.")

    st.title("🧪 Simulateur de Bilan")
    st.caption("Ajustez les paramètres pour voir les résultats évoluer en temps réel.")
    tab_params, tab_results, tab_chat = st.tabs(["⚙️ Paramètres", "📊 Résultats & Graphiques", "🤖 Assistant"])

    with tab_params:
        col1, col2 = st.columns(2)
        with col1:
            m0 = st.number_input("Débit initial m0 (kg/h)", value=1000.0)
            x0_sol = st.number_input("Fraction solubles x0 (0-1)", value=0.10)
            residus = st.number_input("Résidus filtrés (kg/h)", value=20.0)
            mR = st.number_input("Apport jus concentré mR (kg/h)", value=100.0)
            xR = st.number_input("Concentration apport xR (0-1)", value=0.40)
        with col2:
            T2 = st.number_input("Température entrée T2 (°C)", value=20.0)
            T3 = st.number_input("Température chauffage T3 (°C)", value=80.0)
            cp = st.number_input("Cp [kJ/(kg·K)]", value=3.8)
            x4 = st.number_input("Concentration finale visée x4 (0-1)", value=0.40)
            lambda_v = st.number_input("Chaleur latente [kJ/kg]", value=2300.0)
        st.session_state.params = dict(m0=m0,x0_sol=x0_sol,residus=residus,mR=mR,xR=xR,T2=T2,T3=T3,cp=cp,x4=x4,lambda_v=lambda_v)

    p = st.session_state.get('params', dict(m0=1000.0,x0_sol=0.10,residus=20.0,mR=100.0,xR=0.40,T2=20.0,T3=80.0,cp=3.8,x4=0.40,lambda_v=2300.0))
    m1 = p['m0']-p['residus']; x1 = (p['m0']*p['x0_sol'])/m1 if m1>0 else 0
    m2 = m1+p['mR']; x2 = (m1*x1+p['mR']*p['xR'])/m2 if m2>0 else 0
    Q3 = m2*p['cp']*(p['T3']-p['T2'])/3600
    m4 = m2*x2/p['x4'] if p['x4']>0 else 0; mv = m2-m4; Q4 = mv*p['lambda_v']/3600
    Q5 = m4*p['cp']*(80-25)/3600
    erreur = (p['m0']+p['mR'])-(p['residus']+mv+m4)

    with tab_results:
        st.subheader("Résultats en temps réel")
        r1,r2,r3 = st.columns(3)
        r1.metric("Débit après filtration", f"{m1:,.2f} kg/h"); r2.metric("Concentration mélange", f"{x2*100:.2f} %"); r3.metric("Débit final", f"{m4:,.2f} kg/h")
        r4,r5,r6 = st.columns(3)
        r4.metric("Eau évaporée", f"{mv:,.2f} kg/h"); r5.metric("Puissance chauffage", f"{Q3:,.2f} kW"); r6.metric("Puissance évaporation", f"{Q4:,.2f} kW")
        r7,r8 = st.columns(2)
        r7.metric("Puissance refroidissement", f"{Q5:,.2f} kW"); r8.metric("Erreur bilan", f"{erreur:,.2f} kg/h", delta=f"{erreur:,.2f}", delta_color="inverse")

        st.divider()
        st.subheader("📈 Graphiques")
        gc1, gc2 = st.columns(2)
        with gc1:
            st.bar_chart({"Étape": ["Initial","Filtré","Mélangé","Final"], "Débit":[p['m0'],m1,m2,m4]}, x="Étape", y="Débit", color=ACCENT)
        with gc2:
            st.bar_chart({"Opération":["Chauffage","Évaporation","Refroidissement"], "Puissance":[Q3,Q4,Q5]}, x="Opération", y="Puissance", color="#e74c3c")
        st.write("**Atteinte de l'objectif**")
        st.progress(min(x2/p['x4'] if p['x4']>0 else 1.0, 1.0))
        st.caption(f"Objectif : {p['x4']*100}% | Actuel : {x2*100:.2f}%")

        # --- CONCLUSION ---
        st.divider()
        st.subheader("📝 Conclusion & Recommandations")
        for c in generate_conclusion(m1,m2,m4,mv,Q3,Q4,Q5,x2,p['x4'],erreur):
            st.markdown(f"- {c}")
        # Petite synthèse en une phrase
        if abs(erreur)<=1 and x2>=p['x4']:
            st.success("✅ En résumé : Le procédé est valide, vous pouvez passer à l'étape suivante.")
        else:
            st.warning("⚠️ En résumé : Corrigez les points ci-dessus avant de valider le procédé.")

    with tab_chat:
        st.subheader("🤖 Assistant Virtuel")
        if "messages" not in st.session_state: st.session_state.messages=[{"role":"assistant","content":"Bonjour ! Une question ?"}]
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"])
        if prompt := st.chat_input("Posez votre question..."):
            st.session_state.messages.append({"role":"user","content":prompt})
            with st.chat_message("user"): st.markdown(prompt)
            resp = generate_bot_response(prompt)
            st.session_state.messages.append({"role":"assistant","content":resp})
            with st.chat_message("assistant"): st.markdown(resp)

if 'logged_in' not in st.session_state: st.session_state['logged_in']=False
if not st.session_state['logged_in']: auth_page()
else:
    if st.sidebar.button("🚪 Se déconnecter"):
        st.session_state['logged_in']=False; st.session_state['messages']=[]; st.rerun()
    simulator_page()
