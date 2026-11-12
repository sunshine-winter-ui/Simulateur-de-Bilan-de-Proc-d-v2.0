# ==============================================================================
# IMPORTATION DES BIBLIOTHÈQUES
# ==============================================================================
import streamlit as st
import sqlite3
import bcrypt
import re
import pandas as pd

st.set_page_config(page_title="Simulateur Pro", layout="wide", page_icon="🧪")

# ==============================================================================
# 1. DICTIONNAIRE DE TRADUCTION (FR / EN)
# ==============================================================================
TRANSLATIONS = {
    "FR": {
        "app_title": "🧪 Simulateur Pro",
        "app_subtitle": "Filtration • Chauffage • Évaporation",
        "theme_btn": "🌙 Sombre" if st.session_state.get('theme_mode') != 'dark' else "☀️ Clair",
        "lang_btn": "🇬🇧 English",
        "login_tab": "🔑 Se connecter",
        "signup_tab": "📝 Créer un compte",
        "email": "📧 Email",
        "password": "🔒 Mot de passe",
        "confirm_pass": "🔒 Confirmer",
        "username": "👤 Nom d'utilisateur",
        "login_btn": "Se connecter →",
        "signup_btn": "Créer mon compte ✨",
        "sidebar_welcome": "Bonjour",
        "logout": "🚪 Se déconnecter",
        "info_msg": "💡 Modifiez les paramètres puis allez dans Résultats.",
        "sim_title": "🧪 Simulateur de Bilan",
        "sim_caption": "Ajustez les paramètres pour voir les résultats évoluer en temps réel.",
        "tab_params": "⚙️ Paramètres",
        "tab_results": "📊 Résultats & Graphiques",
        "tab_conclusion": "📝 Conclusion",
        "tab_chat": "🤖 Assistant",
        "m0": "Débit initial m0 (kg/h)",
        "x0": "Fraction solubles x0 (0-1)",
        "residus": "Résidus filtrés (kg/h)",
        "mR": "Apport jus concentré mR (kg/h)",
        "xR": "Concentration apport xR (0-1)",
        "T2": "Température entrée T2 (°C)",
        "T3": "Température chauffage T3 (°C)",
        "cp": "Cp [kJ/(kg·K)]",
        "x4": "Concentration finale visée x4 (0-1)",
        "lambda_v": "Chaleur latente [kJ/kg]",
        "res_real_time": "Résultats en temps réel",
        "metric_m1": "Débit après filtration",
        "metric_x2": "Concentration mélange",
        "metric_m4": "Débit final",
        "metric_mv": "Eau évaporée",
        "metric_Q3": "Puissance chauffage",
        "metric_Q4": "Puissance évaporation",
        "metric_Q5": "Puissance refroidissement",
        "metric_err": "Erreur bilan",
        "graphs": "📈 Graphiques",
        "obj_reach": "**Atteinte de l'objectif**",
        "obj_text": "Objectif",
        "concl_title": "📝 Conclusion & Recommandations",
        "summary": "En résumé",
        "chat_title": "🤖 Assistant Virtuel",
        "chat_placeholder": "Posez votre question...",
        "err_fill": "Veuillez remplir tous les champs.",
        "err_auth": "Email ou mot de passe incorrect.",
        "err_req": "Tous les champs sont obligatoires.",
        "err_email": "Email invalide.",
        "err_pass": "Mots de passe différents.",
        "err_len": "Min. 8 caractères.",
        "err_exist": "Email déjà utilisé.",
        "succ_create": "Compte créé !",
        "err_create": "Erreur création."
    },
    "EN": {
        "app_title": "🧪 Pro Simulator",
        "app_subtitle": "Filtration • Heating • Evaporation",
        "theme_btn": "🌙 Dark" if st.session_state.get('theme_mode') != 'dark' else "☀️ Light",
        "lang_btn": "🇫🇷 Français",
        "login_tab": "🔑 Login",
        "signup_tab": "📝 Sign Up",
        "email": "📧 Email",
        "password": "🔒 Password",
        "confirm_pass": "🔒 Confirm",
        "username": "👤 Username",
        "login_btn": "Login →",
        "signup_btn": "Create Account ✨",
        "sidebar_welcome": "Hello",
        "logout": "🚪 Logout",
        "info_msg": "💡 Modify parameters then check Results.",
        "sim_title": "🧪 Mass & Energy Balance Simulator",
        "sim_caption": "Adjust parameters to see results update in real-time.",
        "tab_params": "⚙️ Parameters",
        "tab_results": "📊 Results & Graphs",
        "tab_conclusion": "📝 Conclusion",
        "tab_chat": "🤖 Assistant",
        "m0": "Initial flow m0 (kg/h)",
        "x0": "Soluble fraction x0 (0-1)",
        "residus": "Filtered residues (kg/h)",
        "mR": "Concentrated juice input mR (kg/h)",
        "xR": "Input concentration xR (0-1)",
        "T2": "Inlet temperature T2 (°C)",
        "T3": "Heating temperature T3 (°C)",
        "cp": "Cp [kJ/(kg·K)]",
        "x4": "Target final concentration x4 (0-1)",
        "lambda_v": "Latent heat [kJ/kg]",
        "res_real_time": "Real-time Results",
        "metric_m1": "Flow after filtration",
        "metric_x2": "Mixture concentration",
        "metric_m4": "Final flow",
        "metric_mv": "Evaporated water",
        "metric_Q3": "Heating power",
        "metric_Q4": "Evaporation power",
        "metric_Q5": "Cooling power",
        "metric_err": "Balance error",
        "graphs": "📈 Graphs",
        "obj_reach": "**Objective Achievement**",
        "obj_text": "Target",
        "concl_title": "📝 Conclusion & Recommendations",
        "summary": "In summary",
        "chat_title": "🤖 Virtual Assistant",
        "chat_placeholder": "Ask your question...",
        "err_fill": "Please fill all fields.",
        "err_auth": "Incorrect email or password.",
        "err_req": "All fields are required.",
        "err_email": "Invalid email.",
        "err_pass": "Passwords do not match.",
        "err_len": "Min. 8 characters.",
        "err_exist": "Email already used.",
        "succ_create": "Account created!",
        "err_create": "Creation error."
    }
}

# Fonction de traduction globale
def t(key):
    return TRANSLATIONS[st.session_state.lang].get(key, key)

# ==============================================================================
# 2. INITIALISATION DE LA SESSION ET BASE DE DONNÉES
# ==============================================================================
if 'theme_mode' not in st.session_state: st.session_state.theme_mode = 'light'
if 'lang' not in st.session_state: st.session_state.lang = 'FR'

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

# ==============================================================================
# 3. GESTION DU THÈME (CSS)
# ==============================================================================
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
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 4. LOGIQUE DU CHATBOT INTELLIGENT (SCORING PAR MOTS-CLÉS)
# ==============================================================================
def generate_bot_response(user_input):
    """Analyse la question et retourne la meilleure réponse basée sur un score de mots-clés."""
    u = user_input.lower()
    lang = st.session_state.lang
    
    # Dictionnaire d'intentions avec liste de mots-clés (FR/EN) et réponses
    intents = {
        "filtration": {
            "keywords": ["filtr", "tamis", "résidu", "residu", "solide", "particule", "m1", "m0", "filter", "residue", "solid"],
            "response": {
                "FR": "La filtration retire les particules solides. Formule : **m1 = m0 - résidus** (kg/h). Entrez la quantité de résidus dans les paramètres.",
                "EN": "Filtration removes solid particles. Formula: **m1 = m0 - residues** (kg/h). Enter the residue amount in the parameters."
            }
        },
        "chauffage": {
            "keywords": ["chauff", "temp", "cp", "t2", "t3", "q3", "heat", "cook", "chaleur", "puissance"],
            "response": {
                "FR": "Le chauffage élève la température du mélange. Formule : **Q3 = m2 × Cp × (T3 - T2) / 3600** (en kW).",
                "EN": "Heating raises the mixture temperature. Formula: **Q3 = m2 × Cp × (T3 - T2) / 3600** (in kW)."
            }
        },
        "evaporation": {
            "keywords": ["évap", "evap", "vapeur", "vapor", "q4", "latent", "lambda", "mv", "eau", "water", "bouillir", "boil"],
            "response": {
                "FR": "L'évaporation retire l'eau sous forme de vapeur. Formule : **Q4 = mv × λ / 3600**. Le débit d'eau évaporée est **mv = m2 - m4**.",
                "EN": "Evaporation removes water as vapor. Formula: **Q4 = mv × λ / 3600**. Evaporated water flow is **mv = m2 - m4**."
            }
        },
        "bilan": {
            "keywords": ["bilan", "erreur", "error", "masse", "mass", "balance", "entrée", "sortie", "input", "output"],
            "response": {
                "FR": "Le bilan matière vérifie que Entrées = Sorties. Si l'erreur est proche de 0, le système est équilibré. Formule : **(m0 + mR) - (résidus + mv + m4)**.",
                "EN": "Mass balance verifies Inputs = Outputs. If the error is close to 0, the system is balanced. Formula: **(m0 + mR) - (residues + mv + m4)**."
            }
        },
        "interface": {
            "keywords": ["lang", "langue", "theme", "sombre", "clair", "dark", "light", "onglet", "tab", "changer", "modifier", "interface", "navig"],
            "response": {
                "FR": "Pour changer la langue ou le thème, utilisez les boutons dans la barre latérale à gauche. Naviguez entre les onglets 'Paramètres', 'Résultats' et 'Conclusion' en haut de l'écran.",
                "EN": "To change language or theme, use the buttons in the left sidebar. Navigate between 'Parameters', 'Results', and 'Conclusion' tabs at the top of the screen."
            }
        },
        "salutation": {
            "keywords": ["bonjour", "salut", "hello", "hi", "hey", "coucou"],
            "response": {
                "FR": "Bonjour ! Je suis votre assistant. Posez-moi des questions sur les calculs (filtration, chauffage, évaporation), le bilan ou l'interface.",
                "EN": "Hello! I am your assistant. Ask me questions about calculations (filtration, heating, evaporation), balance, or the interface."
            }
        }
    }
    
    # Calcul du score pour chaque intention
    best_intent = None
    max_score = 0
    
    for intent, data in intents.items():
        score = sum(1 for kw in data["keywords"] if kw in u)
        if score > max_score:
            max_score = score
            best_intent = intent
            
    # Retour de la réponse si un mot-clé a été trouvé
    if best_intent:
        return intents[best_intent]["response"][lang]
        
    # Réponse par défaut si aucune correspondance
    return {
        "FR": "Je n'ai pas bien compris. Essayez de me parler de 'filtration', 'chauffage', 'évaporation', 'bilan' ou de l' 'interface'.",
        "EN": "I didn't quite understand. Try asking about 'filtration', 'heating', 'evaporation', 'balance', or the 'interface'."
    }[lang]

# ==============================================================================
# 5. GÉNÉRATION DES CONCLUSIONS
# ==============================================================================
def generate_conclusion(m1,m2,m4,mv,Q3,Q4,Q5,x2,x4,erreur):
    conclusions = []
    lang = st.session_state.lang
    
    # 1. Bilan matière
    if abs(erreur) > 1:
        conclusions.append({
            "FR": f"⚠️ **Bilan matière déséquilibré :** Erreur de {erreur:.2f} kg/h. Vérifiez vos saisies (m0, mR, résidus).",
            "EN": f"⚠️ **Unbalanced mass balance:** Error of {erreur:.2f} kg/h. Check your inputs (m0, mR, residues)."
        }[lang])
    else:
        conclusions.append({
            "FR": "✅ **Bilan matière équilibré :** Entrées = Sorties. Vos calculs sont cohérents.",
            "EN": "✅ **Balanced mass balance:** Inputs = Outputs. Your calculations are consistent."
        }[lang])

    # 2. Concentration
    taux = (x2 / x4 * 100) if x4>0 else 0
    if taux < 95:
        conclusions.append({
            "FR": f"🔴 **Concentration insuffisante :** Vous êtes à {x2*100:.1f}% au lieu de {x4*100:.0f}% visé. Augmentez l'évaporation (plus de vapeur) ou diminuez l'apport mR.",
            "EN": f"🔴 **Insufficient concentration:** You are at {x2*100:.1f}% instead of the targeted {x4*100:.0f}%. Increase evaporation (more vapor) or decrease the mR input."
        }[lang])
    elif taux < 100:
        conclusions.append({
            "FR": f"🟡 **Presque atteint :** Vous êtes à {taux:.0f}% de l'objectif. Augmentez légèrement la puissance d'évaporation Q4.",
            "EN": f"🟡 **Almost reached:** You are at {taux:.0f}% of the objective. Slightly increase the evaporation power Q4."
        }[lang])
    else:
        conclusions.append({
            "FR": f"✅ **Objectif atteint :** Concentration de {x2*100:.1f}% >= {x4*100:.0f}% visé. Le produit est conforme.",
            "EN": f"✅ **Objective reached:** Concentration of {x2*100:.1f}% >= {x4*100:.0f}% targeted. The product is compliant."
        }[lang])

    # 3. Énergie
    if Q4 > 200:
        conclusions.append({
            "FR": f"💡 **Énergie élevée :** Q4 = {Q4:.1f} kW est important. Vérifiez si vous pouvez récupérer la chaleur du refroidissement (Q5 = {Q5:.1f} kW).",
            "EN": f"💡 **High energy:** Q4 = {Q4:.1f} kW is significant. Check if you can recover the cooling heat (Q5 = {Q5:.1f} kW)."
        }[lang])
    if mv <= 0:
        conclusions.append({
            "FR": "⚠️ **Aucune évaporation :** mv = 0. Le mélange est déjà plus concentré que l'objectif. Diminuez xR ou augmentez x4.",
            "EN": "⚠️ **No evaporation:** mv = 0. The mixture is already more concentrated than the objective. Decrease xR or increase x4."
        }[lang])

    # 4. Action
    if abs(erreur) <= 1 and taux >= 100:
        conclusions.append({
            "FR": "🎯 **Action recommandée :** Procédé stable. Vous pouvez lancer la production.",
            "EN": "🎯 **Recommended action:** Process is stable. You can start production."
        }[lang])
    elif abs(erreur) <= 1:
        conclusions.append({
            "FR": "🎯 **Action recommandée :** Corrigez d'abord la concentration avant de lancer la production.",
            "EN": "🎯 **Recommended action:** Correct the concentration first before starting production."
        }[lang])
    
    return conclusions

# ==============================================================================
# 6. PAGE D'AUTHENTIFICATION
# ==============================================================================
def auth_page():
    c1,c2,c3 = st.columns([1,1.6,1])
    with c2:
        st.markdown(f"<h1 style='text-align:center; background: linear-gradient(135deg, {ACCENT}, {ACCENT2}); -webkit-background-clip:text; -webkit-text-fill-color:transparent;'>{t('app_title')}</h1><p style='text-align:center; color:{MUTED};'>{t('app_subtitle')}</p>", unsafe_allow_html=True)
        
        # Boutons de configuration (Langue et Thème)
        col_lang, col_theme = st.columns(2)
        with col_lang:
            if st.button(t("lang_btn")):
                st.session_state.lang = 'EN' if st.session_state.lang == 'FR' else 'FR'
                st.rerun()
        with col_theme:
            if st.button(t("theme_btn")):
                st.session_state.theme_mode = 'dark' if not is_dark else 'light'
                st.rerun()
                
        tab1, tab2 = st.tabs([t("login_tab"), t("signup_tab")])
        with tab1:
            with st.form("login_form"):
                email = st.text_input(t("email"), placeholder="exemple@email.com")
                password = st.text_input(t("password"), type="password")
                if st.form_submit_button(t("login_btn")):
                    if not email or not password: st.error(t("err_fill"))
                    else:
                        user = authenticate_user(email, password)
                        if user: st.session_state['logged_in']=True; st.session_state['username']=user; st.rerun()
                        else: st.error(t("err_auth"))
        with tab2:
            with st.form("signup_form"):
                nu = st.text_input(t("username")); ne = st.text_input(t("email")); npw = st.text_input(t("password"), type="password"); cpw = st.text_input(t("confirm_pass"), type="password")
                if st.form_submit_button(t("signup_btn")):
                    if not nu or not ne or not npw: st.error(t("err_req"))
                    elif not re.match(r"[^@]+@[^@]+\.[^@]+", ne): st.error(t("err_email"))
                    elif npw != cpw: st.error(t("err_pass"))
                    elif len(npw) < 8: st.error(t("err_len"))
                    elif email_exists(ne): st.warning(t("err_exist"))
                    else:
                        if create_user(nu, ne, npw): st.session_state['logged_in']=True; st.session_state['username']=nu; st.success(t("succ_create")); st.rerun()
                        else: st.error(t("err_create"))

# ==============================================================================
# 7. PAGE PRINCIPALE DU SIMULATEUR
# ==============================================================================
def simulator_page():
    with st.sidebar:
        st.markdown(f"### {t('app_title')}\n{t('sidebar_welcome')}, **{st.session_state.get('username')}**")
        
        col_lang, col_theme = st.columns(2)
        with col_lang:
            if st.button(t("lang_btn")):
                st.session_state.lang = 'EN' if st.session_state.lang == 'FR' else 'FR'
                st.rerun()
        with col_theme:
            if st.button(t("theme_btn")):
                st.session_state.theme_mode = 'dark' if not is_dark else 'light'
                st.rerun()
                
        st.info(t("info_msg"))
        if st.button(t("logout")):
            st.session_state['logged_in']=False; st.session_state['messages']=[]; st.rerun()

    st.title(t("sim_title"))
    st.caption(t("sim_caption"))
    
    tab_params, tab_results, tab_conclusion, tab_chat = st.tabs([
        t("tab_params"), t("tab_results"), t("tab_conclusion"), t("tab_chat")
    ])

    # --- ONGLET PARAMÈTRES ---
    with tab_params:
        col1, col2 = st.columns(2)
        with col1:
            m0 = st.number_input(t("m0"), value=1000.0)
            x0_sol = st.number_input(t("x0"), value=0.10)
            residus = st.number_input(t("residus"), value=20.0)
            mR = st.number_input(t("mR"), value=100.0)
            xR = st.number_input(t("xR"), value=0.40)
        with col2:
            T2 = st.number_input(t("T2"), value=20.0)
            T3 = st.number_input(t("T3"), value=80.0)
            cp = st.number_input(t("cp"), value=3.8)
            x4 = st.number_input(t("x4"), value=0.40)
            lambda_v = st.number_input(t("lambda_v"), value=2300.0)
        st.session_state.params = dict(m0=m0,x0_sol=x0_sol,residus=residus,mR=mR,xR=xR,T2=T2,T3=T3,cp=cp,x4=x4,lambda_v=lambda_v)

    # --- CALCULS ---
    p = st.session_state.get('params', dict(m0=1000.0,x0_sol=0.10,residus=20.0,mR=100.0,xR=0.40,T2=20.0,T3=80.0,cp=3.8,x4=0.40,lambda_v=2300.0))
    m1 = p['m0']-p['residus']; x1 = (p['m0']*p['x0_sol'])/m1 if m1>0 else 0
    m2 = m1+p['mR']; x2 = (m1*x1+p['mR']*p['xR'])/m2 if m2>0 else 0
    Q3 = m2*p['cp']*(p['T3']-p['T2'])/3600
    m4 = m2*x2/p['x4'] if p['x4']>0 else 0; mv = m2-m4; Q4 = mv*p['lambda_v']/3600
    Q5 = m4*p['cp']*(80-25)/3600
    erreur = (p['m0']+p['mR'])-(p['residus']+mv+m4)

    # --- ONGLET RÉSULTATS ---
    with tab_results:
        st.subheader(t("res_real_time"))
        r1,r2,r3 = st.columns(3)
        r1.metric(t("metric_m1"), f"{m1:,.2f} kg/h"); r2.metric(t("metric_x2"), f"{x2*100:.2f} %"); r3.metric(t("metric_m4"), f"{m4:,.2f} kg/h")
        r4,r5,r6 = st.columns(3)
        r4.metric(t("metric_mv"), f"{mv:,.2f} kg/h"); r5.metric(t("metric_Q3"), f"{Q3:,.2f} kW"); r6.metric(t("metric_Q4"), f"{Q4:,.2f} kW")
        r7,r8 = st.columns(2)
        r7.metric(t("metric_Q5"), f"{Q5:,.2f} kW"); r8.metric(t("metric_err"), f"{erreur:,.2f} kg/h", delta=f"{erreur:,.2f}", delta_color="inverse")

        st.divider()
        st.subheader(t("graphs"))
        gc1, gc2 = st.columns(2)
        
        with gc1:
            df_debit = pd.DataFrame({"Étape/Step": ["Initial","Filtré/Filtered","Mélangé/Mixed","Final"], "Débit/Flow":[p['m0'],m1,m2,m4]})
            st.bar_chart(df_debit, x="Étape/Step", y="Débit/Flow", color=ACCENT)
        with gc2:
            df_puissance = pd.DataFrame({"Opération/Operation":["Chauffage/Heat","Évaporation/Evap","Refroidissement/Cool"], "Puissance/Power":[Q3,Q4,Q5]})
            st.bar_chart(df_puissance, x="Opération/Operation", y="Puissance/Power", color="#e74c3c")
            
        st.write(t("obj_reach"))
        st.progress(min(x2/p['x4'] if p['x4']>0 else 1.0, 1.0))
        st.caption(f"{t('obj_text')} : {p['x4']*100}% | Actuel/Current : {x2*100:.2f}%")

    # --- ONGLET CONCLUSION ---
    with tab_conclusion:
        st.subheader(t("concl_title"))
        
        for c in generate_conclusion(m1,m2,m4,mv,Q3,Q4,Q5,x2,p['x4'],erreur):
            st.markdown(f"- {c}")
            
        st.divider()
        
        if abs(erreur)<=1 and x2>=p['x4']:
            st.success(f"✅ {t('summary')} : " + ("Le procédé est valide." if st.session_state.lang=='FR' else "The process is valid."))
        else:
            st.warning(f"⚠️ {t('summary')} : " + ("Corrigez les points ci-dessus." if st.session_state.lang=='FR' else "Fix the points above."))

    # --- ONGLET ASSISTANT ---
    with tab_chat:
        st.subheader(t("chat_title"))
        if "messages" not in st.session_state: 
            welcome_msg = "Bonjour ! Une question ?" if st.session_state.lang == 'FR' else "Hello! Any questions?"
            st.session_state.messages=[{"role":"assistant","content":welcome_msg}]
            
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"])
            
        if prompt := st.chat_input(t("chat_placeholder")):
            st.session_state.messages.append({"role":"user","content":prompt})
            with st.chat_message("user"): st.markdown(prompt)
            resp = generate_bot_response(prompt)
            st.session_state.messages.append({"role":"assistant","content":resp})
            with st.chat_message("assistant"): st.markdown(resp)

# ==============================================================================
# 8. LANCEMENT DE L'APPLICATION
# ==============================================================================
if 'logged_in' not in st.session_state: st.session_state['logged_in']=False

if not st.session_state['logged_in']: 
    auth_page()
else: 
    simulator_page()
