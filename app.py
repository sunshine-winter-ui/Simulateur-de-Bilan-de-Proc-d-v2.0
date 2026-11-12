import streamlit as st
import sqlite3, bcrypt, re, pandas as pd, unicodedata
from io import BytesIO

st.set_page_config(page_title="Simulateur Pro", layout="wide", page_icon="🧪", initial_sidebar_state="collapsed")

# --- TRADUCTION ---
TRANSLATIONS = {
    "FR": {
        "app_subtitle": "Filtration • Chauffage • Évaporation",
        "theme_btn": "🌙 Sombre" if st.session_state.get('theme_mode') != 'dark' else "☀️ Clair",
        "lang_btn": "🇬🇧 English", "login_tab": "🔑 Se connecter", "signup_tab": "📝 Créer un compte",
        "email": "📧 Email", "password": "🔒 Mot de passe", "confirm_pass": "🔒 Confirmer",
        "username": "👤 Nom d'utilisateur", "login_btn": "Se connecter →", "signup_btn": "Créer mon compte ✨",
        "sidebar_welcome": "Bonjour", "logout": "🚪 Se déconnecter",
        "info_msg": "💡 Modifiez les paramètres puis allez dans Résultats.",
        "sim_title": "Simulateur de Bilan 🧪", "sim_caption": "Ajustez les paramètres pour voir les résultats évoluer en temps réel.",
        "tab_params": "⚙️ Paramètres", "tab_results": "📊 Résultats", "tab_conclusion": "📝 Conclusion", "tab_chat": "🤖 Assistant",
        "m0": "Débit initial m0 (kg/h)", "x0": "Fraction solubles x0 (0-1)", "residus": "Résidus filtrés (kg/h)",
        "mR": "Apport jus mR (kg/h)", "xR": "Concentration apport xR (0-1)",
        "T2": "Température entrée T2 (°C)", "T3": "Température chauffage T3 (°C)", "cp": "Cp [kJ/(kg·K)]",
        "x4": "Concentration finale visée x4 (0-1)", "lambda_v": "Chaleur latente [kJ/kg]",
        "res_real_time": "Résultats en temps réel", "metric_m1": "Débit après filtration", "metric_x2": "Concentration mélange",
        "metric_m4": "Débit final", "metric_mv": "Eau évaporée", "metric_Q3": "Puissance chauffage",
        "metric_Q4": "Puissance évaporation", "metric_Q5": "Puissance refroidissement", "metric_err": "Erreur bilan",
        "graphs": "📈 Graphiques", "obj_reach": "**Atteinte de l'objectif**", "obj_text": "Objectif",
        "concl_title": "📝 Conclusion & Recommandations", "summary": "En résumé",
        "chat_title": "🤖 Assistant Virtuel", "chat_placeholder": "Posez votre question...",
        "err_fill": "Veuillez remplir tous les champs.", "err_auth": "Email ou mot de passe incorrect.",
        "err_req": "Tous les champs sont obligatoires.", "err_email": "Email invalide.", "err_pass": "Mots de passe différents.",
        "err_len": "Min. 8 caractères.", "err_exist": "Email déjà utilisé.", "succ_create": "Compte créé !", "err_create": "Erreur création.",
        "landing_title": "Simulez votre procédé industriel en 1 minute",
        "landing_sub": "Calculez filtration, chauffage et évaporation. Obtenez graphiques, bilan et conclusion automatique.",
        "cta_start": "🚀 Commencer gratuitement", "cta_login": "Déjà un compte ? Se connecter",
        "feat1": "⚡ Calcul instantané", "feat1_d": "Résultats en temps réel dès que vous changez une valeur.",
        "feat2": "📊 Graphiques clairs", "feat2_d": "Visualisez débits et puissances énergétiques.",
        "feat3": "🤖 Assistant intelligent", "feat3_d": "Posez n'importe quelle question sur vos calculs.",
        "feat4": "📄 Export PDF", "feat4_d": "Téléchargez votre rapport complet en 1 clic.",
        "how_title": "Comment ça marche ?", "step1": "1. Créez un compte", "step1_d": "30 secondes, gratuit.",
        "step2": "2. Entrez vos paramètres", "step2_d": "m0, T2, T3, Cp...",
        "step3": "3. Obtenez votre rapport", "step3_d": "Conclusion + PDF.",
        "export_pdf": "📄 Télécharger le rapport PDF", "back_home": "← Retour à l'accueil",
    },
    "EN": {
        "app_subtitle": "Filtration • Heating • Evaporation",
        "theme_btn": "🌙 Dark" if st.session_state.get('theme_mode') != 'dark' else "☀️ Light",
        "lang_btn": "🇫🇷 Français", "login_tab": "🔑 Login", "signup_tab": "📝 Sign Up",
        "email": "📧 Email", "password": "🔒 Password", "confirm_pass": "🔒 Confirm",
        "username": "👤 Username", "login_btn": "Login →", "signup_btn": "Create Account ✨",
        "sidebar_welcome": "Hello", "logout": "🚪 Logout",
        "info_msg": "💡 Modify parameters then check Results.",
        "sim_title": "🧪 Balance Simulator", "sim_caption": "Adjust parameters to see results update in real-time.",
        "tab_params": "⚙️ Parameters", "tab_results": "📊 Results", "tab_conclusion": "📝 Conclusion", "tab_chat": "🤖 Assistant",
        "m0": "Initial flow m0 (kg/h)", "x0": "Soluble fraction x0 (0-1)", "residus": "Filtered residues (kg/h)",
        "mR": "Concentrated juice mR (kg/h)", "xR": "Input concentration xR (0-1)",
        "T2": "Inlet temp T2 (°C)", "T3": "Heating temp T3 (°C)", "cp": "Cp [kJ/(kg·K)]",
        "x4": "Target final concentration x4 (0-1)", "lambda_v": "Latent heat [kJ/kg]",
        "res_real_time": "Real-time Results", "metric_m1": "Flow after filtration", "metric_x2": "Mixture concentration",
        "metric_m4": "Final flow", "metric_mv": "Evaporated water", "metric_Q3": "Heating power",
        "metric_Q4": "Evaporation power", "metric_Q5": "Cooling power", "metric_err": "Balance error",
        "graphs": "📈 Graphs", "obj_reach": "**Objective Achievement**", "obj_text": "Target",
        "concl_title": "📝 Conclusion & Recommendations", "summary": "In summary",
        "chat_title": "🤖 Virtual Assistant", "chat_placeholder": "Ask your question...",
        "err_fill": "Please fill all fields.", "err_auth": "Incorrect email or password.",
        "err_req": "All fields are required.", "err_email": "Invalid email.", "err_pass": "Passwords do not match.",
        "err_len": "Min. 8 characters.", "err_exist": "Email already used.", "succ_create": "Account created!", "err_create": "Creation error.",
        "landing_title": "Simulate your industrial process in 1 minute",
        "landing_sub": "Calculate filtration, heating and evaporation. Get graphs, balance and automatic conclusion.",
        "cta_start": "🚀 Start for free", "cta_login": "Already have an account? Login",
        "feat1": "⚡ Instant calculation", "feat1_d": "Real-time results as you change a value.",
        "feat2": "📊 Clear graphs", "feat2_d": "Visualize flows and energy powers.",
        "feat3": "🤖 Smart assistant", "feat3_d": "Ask any question about your calculations.",
        "feat4": "📄 PDF Export", "feat4_d": "Download your full report in 1 click.",
        "how_title": "How it works?", "step1": "1. Create account", "step1_d": "30 seconds, free.",
        "step2": "2. Enter parameters", "step2_d": "m0, T2, T3, Cp...",
        "step3": "3. Get your report", "step3_d": "Conclusion + PDF.",
        "export_pdf": "📄 Download PDF Report", "back_home": "← Back to home",
    }
}
def t(k): return TRANSLATIONS[st.session_state.lang].get(k,k)

if 'theme_mode' not in st.session_state: st.session_state.theme_mode='light'
if 'lang' not in st.session_state: st.session_state.lang='FR'
if 'page' not in st.session_state: st.session_state.page='landing'  # landing / auth / app
if 'logged_in' not in st.session_state: st.session_state.logged_in=False

# --- DB ---
def init_db():
    conn=sqlite3.connect('users.db'); c=conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL, email TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL)''')
    conn.commit(); conn.close()
init_db()
def hash_password(p): return bcrypt.hashpw(p.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
def verify_password(p,h): return bcrypt.checkpw(p.encode('utf-8'), h.encode('utf-8'))
def email_exists(e):
    conn=sqlite3.connect('users.db'); c=conn.cursor(); c.execute("SELECT 1 FROM users WHERE email=?", (e,)); r=c.fetchone(); conn.close(); return r is not None
def create_user(u,e,p):
    conn=sqlite3.connect('users.db'); c=conn.cursor()
    try: c.execute("INSERT INTO users (username,email,password_hash) VALUES (?,?,?)",(u,e,hash_password(p))); conn.commit(); return True
    except: return False
    finally: conn.close()
def authenticate_user(e,p):
    conn=sqlite3.connect('users.db'); c=conn.cursor(); c.execute("SELECT username,password_hash FROM users WHERE email=?", (e,)); r=c.fetchone(); conn.close()
    return r[0] if r and verify_password(p,r[1]) else None

# --- DESIGN ATTRACTIF + MOBILE ---
is_dark = st.session_state.theme_mode=='dark'
if is_dark:
    BG="#0b1023"; CARD="rgba(255,255,255,0.06)"; CARD_SOLID="#1a213f"; TEXT="#f8fafc"; MUTED="#a5b4fc"
    INPUT_BG="#151c3a"; INPUT_BORDER="rgba(255,255,255,0.12)"; ACCENT="#a78bfa"; ACCENT2="#38bdf8"; ACCENT3="#f472b6"; SHADOW="0 20px 40px rgba(0,0,0,0.35)"
    GRAD="radial-gradient(800px at 10% 0%, #7c3aed33, transparent), radial-gradient(800px at 90% 100%, #0ea5e933, transparent)"
else:
    BG="#eef2ff"; CARD="rgba(255,255,255,0.85)"; CARD_SOLID="#ffffff"; TEXT="#1e1b4b"; MUTED="#6366f1"
    INPUT_BG="#ffffff"; INPUT_BORDER="#e0e7ff"; ACCENT="#7c3aed"; ACCENT2="#2563eb"; ACCENT3="#ec4899"; SHADOW="0 20px 40px rgba(124,58,237,0.12)"
    GRAD="radial-gradient(700px at 0% 0%, #c7d2fe, transparent), radial-gradient(700px at 100% 100%, #fbcfe8, transparent)"

st.markdown(f"""
<style>
    .stApp {{ background:{BG}; }}
    .stApp::before {{ content:""; position:fixed; inset:0; z-index:-1; background:{GRAD}; }}
    h1,h2,h3 {{ font-weight:800 !important; color:{TEXT} !important; letter-spacing:-0.5px; }}
    p,span,label,div {{ color:{TEXT} !important; }}
    .glass {{ background:{CARD}; backdrop-filter:blur(16px); border:1px solid {INPUT_BORDER}; border-radius:22px; padding:22px; box-shadow:{SHADOW}; }}
    .hero {{ background: linear-gradient(135deg, {ACCENT} 0%, {ACCENT2} 55%, {ACCENT3} 100%); padding:32px 26px; border-radius:26px; color:white !important; box-shadow:0 20px 40px {ACCENT}55; }}
    .hero h1, .hero p, .hero span {{ color:white !important; }}
    .hero-badge {{ background:rgba(255,255,255,0.22); padding:6px 14px; border-radius:100px; font-size:13px; font-weight:700; color:white !important; display:inline-block; }}
    .feature {{ background:{CARD}; border:1px solid {INPUT_BORDER}; border-radius:18px; padding:18px; text-align:center; box-shadow:{SHADOW}; transition:.2s; }}
    .feature:hover {{ transform:translateY(-4px); border-color:{ACCENT}; }}
    div[data-testid="stTextInput"] input, div[data-testid="stNumberInput"] input {{ background:{INPUT_BG} !important; color:{TEXT} !important; border:1.5px solid {INPUT_BORDER} !important; border-radius:14px !important; padding:12px !important; }}
    .stButton>button {{ background:linear-gradient(135deg,{ACCENT},{ACCENT2}) !important; color:white !important; border:none !important; border-radius:14px !important; padding:12px 18px !important; font-weight:800 !important; box-shadow:0 10px 20px {ACCENT}44 !important; }}
    .stButton>button:hover {{ transform:translateY(-2px); }}
    .stDownloadButton>button {{ background: linear-gradient(135deg,#10b981,#059669) !important; color:white !important; border:none !important; border-radius:14px !important; font-weight:800 !important; }}
    div[data-testid="stMetric"] {{ background:{CARD} !important; border:1px solid {INPUT_BORDER} !important; border-radius:18px !important; padding:16px !important; box-shadow:{SHADOW} !important; }}
    div[data-testid="stMetricValue"] {{ color:{ACCENT2} !important; font-weight:800 !important; }}
    button[data-baseweb="tab"][aria-selected="true"] {{ background:linear-gradient(135deg,{ACCENT},{ACCENT2}) !important; color:white !important; }}
    button[data-baseweb="tab"] {{ background:{CARD_SOLID} !important; color:{TEXT} !important; border:1px solid {INPUT_BORDER} !important; border-radius:100px !important; }}
    section[data-testid="stSidebar"] {{ background:{CARD_SOLID} !important; }}
    #MainMenu {{visibility:hidden;}} header {{background:transparent !important;}}

    /* 📱 MOBILE : tout s'adapte */
    @media (max-width: 768px) {{
        .hero {{ padding:20px 16px !important; border-radius:18px !important; }}
        .hero h1 {{ font-size:24px !important; line-height:1.2 !important; }}
        .glass {{ padding:14px !important; border-radius:16px !important; }}
        .feature {{ padding:12px !important; }}
        div[data-testid="stMetricValue"] {{ font-size:20px !important; }}
        div[data-testid="stMetric"] {{ padding:12px !important; }}
        .stButton>button {{ padding:10px !important; font-size:13px !important; }}
        h1 {{ font-size:24px !important; }} h2 {{ font-size:19px !important; }} h3 {{ font-size:16px !important; }}
        [data-testid="column"] {{ min-width:100% !important; }}
    }}
</style>
""", unsafe_allow_html=True)

def get_logo(w=250,h=80):
    return f"""<div style="display:flex;justify-content:center;"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 100" width="{w}" height="{h}">
    <defs><linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" style="stop-color:{ACCENT}"/><stop offset="100%" style="stop-color:{ACCENT2}"/></linearGradient></defs>
    <path d="M30 20 L30 80 C30 85 35 90 40 90 L70 90 C75 90 80 85 80 80 L80 20 Z" fill="url(#g)" opacity="0.2" stroke="url(#g)" stroke-width="4"/>
    <path d="M45 45 L45 80 C45 83 47 85 50 85 L60 85 C63 85 65 83 65 80 L65 45 Z" fill="url(#g)"/>
    <text x="100" y="55" font-family="Arial" font-size="36" font-weight="900" fill="url(#g)">Simulateur</text>
    <text x="100" y="85" font-family="Arial" font-size="24" font-weight="bold" fill="{MUTED}" letter-spacing="4">PRO</text></svg></div>"""

# --- PDF EXPORT ---
def create_pdf_report(params, results, conclusions, username):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import mm
        buf = BytesIO(); c = canvas.Canvas(buf, pagesize=A4); w,h = A4
        # Header
        c.setFillColorRGB(0.48,0.23,0.92); c.rect(0,h-55,w,55,fill=1,stroke=0)
        c.setFillColorRGB(1,1,1); c.setFont("Helvetica-Bold",20); c.drawString(20*mm,h-32,"SIMULATEUR PRO - Rapport")
        c.setFont("Helvetica",10); c.drawString(20*mm,h-45,f"Utilisateur: {username}  |  Filtration - Chauffage - Evaporation")
        y=h-75; c.setFillColorRGB(0.12,0.11,0.29)
        c.setFont("Helvetica-Bold",14); c.drawString(20*mm,y,"1. Parametres d'entree"); y-=18
        c.setFont("Helvetica",11)
        for k,v in params.items(): c.drawString(25*mm,y,f"- {k} : {v}"); y-=14
        y-=8; c.setFont("Helvetica-Bold",14); c.drawString(20*mm,y,"2. Resultats"); y-=18; c.setFont("Helvetica",11)
        for k,v in results.items(): c.drawString(25*mm,y,f"- {k} : {v}"); y-=14
        y-=8; c.setFont("Helvetica-Bold",14); c.drawString(20*mm,y,"3. Conclusion"); y-=18; c.setFont("Helvetica",11)
        for concl in conclusions:
            txt = re.sub(r'[^a-zA-Z0-9 .,%:()/-]','', concl)
            # wrap simple
            while len(txt)>85:
                c.drawString(25*mm,y,txt[:85]); y-=14; txt=txt[85:]
            c.drawString(25*mm,y,txt); y-=16
            if y<40: c.showPage(); y=h-40
        c.setFont("Helvetica-Oblique",9); c.drawString(20*mm,20,"Genere par Simulateur Pro - Merci d'utiliser l'application.")
        c.save(); buf.seek(0); return buf.getvalue()
    except Exception as e:
        # Fallback TXT si reportlab absent
        txt = f"SIMULATEUR PRO\nUtilisateur: {username}\n\nPARAMETRES:\n{params}\n\nRESULTATS:\n{results}\n\nCONCLUSION:\n{conclusions}"
        return txt.encode('utf-8')

# --- CHATBOT ---
def clean_text(t):
    t=t.lower(); t=''.join(c for c in unicodedata.normalize('NFD',t) if unicodedata.category(c)!='Mn'); t=re.sub(r"[^a-z0-9\s]"," ",t); return re.sub(r"\s+"," ",t)
def generate_bot_response(q):
    p=st.session_state.get('params',dict(m0=1000.0,x0_sol=0.10,residus=20.0,mR=100.0,xR=0.40,T2=20.0,T3=80.0,cp=3.8,x4=0.40,lambda_v=2300.0))
    m1=p['m0']-p['residus']; x1=(p['m0']*p['x0_sol'])/m1 if m1>0 else 0; m2=m1+p['mR']; x2=(m1*x1+p['mR']*p['xR'])/m2 if m2>0 else 0
    Q3=m2*p['cp']*(p['T3']-p['T2'])/3600; m4=m2*x2/p['x4'] if p['x4']>0 else 0; mv=m2-m4; Q4=mv*p['lambda_v']/3600; Q5=m4*p['cp']*55/3600; err=(p['m0']+p['mR'])-(p['residus']+mv+m4)
    qq=clean_text(q); lang=st.session_state.lang
    def has(*m): return any(x in qq for x in m)
    if has("bonjour","salut","salam","hello","hi"): return "Salut ! 👋 Demande-moi : 'C'est quoi m1 ?' ou 'Pourquoi mon bilan est faux ?'" if lang=='FR' else "Hi! Ask me anything."
    if has("filtr","m1","m0","residu"): return f"Filtration : m1 = {p['m0']:.0f} - {p['residus']:.0f} = **{m1:.2f} kg/h**"
    if has("chauff","q3","cp","t2","t3"): return f"Chauffage : Q3 = **{Q3:.2f} kW** (de {p['T2']:.0f}°C à {p['T3']:.0f}°C)"
    if has("evap","vapeur","q4","mv","m4"): return f"Évaporation : m4={m4:.2f}, mv={mv:.2f} kg/h, Q4={Q4:.2f} kW | {x2*100:.1f}% vs {p['x4']*100:.0f}%"
    if has("bilan","erreur"): return f"Erreur bilan = **{err:.2f} kg/h**. " + ("✅ Parfait." if abs(err)<=1 else "⚠️ Vérifie m0, mR, résidus.")
    if has("conclusion","que faire","conseil"): return "Regarde l'onglet 📝 Conclusion, tout est détaillé."
    if has("graphique","graph"): return "Graphiques dans 📊 Résultats."
    if has("pdf","export","telecharger","download"): return "Pour télécharger le PDF, va dans l'onglet 📝 Conclusion et clique sur **📄 Télécharger le rapport PDF**."
    return "Essaie : 'C'est quoi Q4 ?', 'Pourquoi mon bilan est faux ?', 'Où changer T3 ?'" if lang=='FR' else "Try: 'What is Q4?'"

def generate_conclusion(m1,m2,m4,mv,Q3,Q4,Q5,x2,x4,erreur):
    lang=st.session_state.lang; out=[]
    out.append(f"⚠️ Bilan déséquilibré : Erreur {erreur:.2f} kg/h." if abs(erreur)>1 else "✅ Bilan équilibré : Entrées = Sorties.")
    taux=(x2/x4*100) if x4>0 else 0
    if taux<95: out.append(f"🔴 Concentration insuffisante : {x2*100:.1f}% au lieu de {x4*100:.0f}%. Augmente l'évaporation.")
    elif taux<100: out.append(f"🟡 Presque : {taux:.0f}% de l'objectif. Augmente Q4.")
    else: out.append(f"✅ Objectif atteint : {x2*100:.1f}% >= {x4*100:.0f}%.")
    if Q4>200: out.append(f"💡 Énergie élevée : Q4={Q4:.1f} kW. Récupère chaleur de Q5 ({Q5:.1f} kW).")
    if abs(erreur)<=1 and taux>=100: out.append("🎯 Action : Procédé stable. Lance la production.")
    elif abs(erreur)<=1: out.append("🎯 Action : Corrige d'abord la concentration.")
    return out

# --- 1. PAGE D'ACCUEIL ---
def landing_page():
    col_lang, col_theme = st.columns([1,1])
    with col_lang:
        if st.button(t("lang_btn")): st.session_state.lang='EN' if st.session_state.lang=='FR' else 'FR'; st.rerun()
    with col_theme:
        if st.button(t("theme_btn")): st.session_state.theme_mode='dark' if not is_dark else 'light'; st.rerun()
    st.markdown(get_logo(300,100), unsafe_allow_html=True)
    st.markdown(f"<p style='text-align:center; font-weight:700; color:{MUTED};'>{t('app_subtitle')}</p>", unsafe_allow_html=True)
    # HERO
    st.markdown(f"""<div class="hero"><span class="hero-badge">✨ NOUVEAU • V3 • GRATUIT</span>
    <h1 style="font-size:36px; margin:14px 0 8px 0; line-height:1.1;">{t('landing_title')}</h1>
    <p style="font-size:16px; opacity:0.95; margin:0;">{t('landing_sub')}</p>
    <div style="margin-top:16px;"><span class="hero-badge">🧪 Filtration</span> <span class="hero-badge">🔥 Chauffage</span> <span class="hero-badge">💨 Évaporation</span></div></div>""", unsafe_allow_html=True)
    st.write("")
    c1,c2 = st.columns(2)
    with c1:
        if st.button(t("cta_start"), use_container_width=True): st.session_state.page='auth'; st.rerun()
    with c2:
        if st.button(t("cta_login"), use_container_width=True): st.session_state.page='auth'; st.rerun()
    st.write("")
    # FEATURES - 2x2 sur mobile, 4 en ligne sur PC
    f1,f2,f3,f4 = st.columns(4)
    with f1: st.markdown(f"<div class='feature'><h3>{t('feat1')}</h3><p>{t('feat1_d')}</p></div>", unsafe_allow_html=True)
    with f2: st.markdown(f"<div class='feature'><h3>{t('feat2')}</h3><p>{t('feat2_d')}</p></div>", unsafe_allow_html=True)
    with f3: st.markdown(f"<div class='feature'><h3>{t('feat3')}</h3><p>{t('feat3_d')}</p></div>", unsafe_allow_html=True)
    with f4: st.markdown(f"<div class='feature'><h3>{t('feat4')}</h3><p>{t('feat4_d')}</p></div>", unsafe_allow_html=True)
    st.write("")
    st.markdown(f"<div class='glass'><h2 style='text-align:center;'>{t('how_title')}</h2></div>", unsafe_allow_html=True)
    s1,s2,s3 = st.columns(3)
    with s1: st.markdown(f"<div class='feature'><h3>{t('step1')}</h3><p>{t('step1_d')}</p></div>", unsafe_allow_html=True)
    with s2: st.markdown(f"<div class='feature'><h3>{t('step2')}</h3><p>{t('step2_d')}</p></div>", unsafe_allow_html=True)
    with s3: st.markdown(f"<div class='feature'><h3>{t('step3')}</h3><p>{t('feat4_d')}</p></div>", unsafe_allow_html=True)
    st.write("")
    st.image("https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?auto=format&fit=crop&q=80&w=1200", caption="Laboratoire • Procédés industriels", use_container_width=True)
    st.caption("Simulateur Pro • Conçu pour les étudiants et ingénieurs en génie des procédés")

# --- 2. AUTH ---
def auth_page():
    if st.button(t("back_home")): st.session_state.page='landing'; st.rerun()
    c1,c2,c3 = st.columns([1,1.7,1])
    with c2:
        st.markdown(get_logo(300,100), unsafe_allow_html=True)
        st.markdown(f"<p style='text-align:center; font-weight:700;'>{t('app_subtitle')}</p>", unsafe_allow_html=True)
        col_lang, col_theme = st.columns(2)
        with col_lang:
            if st.button(t("lang_btn")): st.session_state.lang='EN' if st.session_state.lang=='FR' else 'FR'; st.rerun()
        with col_theme:
            if st.button(t("theme_btn")): st.session_state.theme_mode='dark' if not is_dark else 'light'; st.rerun()
        tab1, tab2 = st.tabs([t("login_tab"), t("signup_tab")])
        with tab1:
            with st.form("login_form"):
                email=st.text_input(t("email"), placeholder="exemple@email.com"); password=st.text_input(t("password"), type="password")
                if st.form_submit_button(t("login_btn")):
                    if not email or not password: st.error(t("err_fill"))
                    else:
                        user=authenticate_user(email,password)
                        if user: st.session_state.logged_in=True; st.session_state.username=user; st.session_state.page='app'; st.rerun()
                        else: st.error(t("err_auth"))
        with tab2:
            with st.form("signup_form"):
                nu=st.text_input(t("username")); ne=st.text_input(t("email")); npw=st.text_input(t("password"), type="password"); cpw=st.text_input(t("confirm_pass"), type="password")
                if st.form_submit_button(t("signup_btn")):
                    if not nu or not ne or not npw: st.error(t("err_req"))
                    elif not re.match(r"[^@]+@[^@]+\.[^@]+", ne): st.error(t("err_email"))
                    elif npw!=cpw: st.error(t("err_pass"))
                    elif len(npw)<8: st.error(t("err_len"))
                    elif email_exists(ne): st.warning(t("err_exist"))
                    else:
                        if create_user(nu,ne,npw): st.session_state.logged_in=True; st.session_state.username=nu; st.session_state.page='app'; st.success(t("succ_create")); st.rerun()
                        else: st.error(t("err_create"))

# --- 3. SIMULATEUR ---
def simulator_page():
    with st.sidebar:
        st.markdown(get_logo(180,60), unsafe_allow_html=True)
        st.markdown(f"👤 **{t('sidebar_welcome')}, {st.session_state.get('username')}**")
        col_lang, col_theme = st.columns(2)
        with col_lang:
            if st.button(t("lang_btn")): st.session_state.lang='EN' if st.session_state.lang=='FR' else 'FR'; st.rerun()
        with col_theme:
            if st.button(t("theme_btn")): st.session_state.theme_mode='dark' if not is_dark else 'light'; st.rerun()
        st.info(t("info_msg"))
        if st.button(t("logout")): st.session_state.logged_in=False; st.session_state.messages=[]; st.session_state.page='landing'; st.rerun()
    st.markdown(f"""<div class="hero"><span class="hero-badge">✨ SIMULATEUR • V3</span><h1 style="margin:10px 0 6px 0;">{t('sim_title')}</h1><p style="opacity:0.9; margin:0;">{t('sim_caption')}</p></div>""", unsafe_allow_html=True)
    tab_params, tab_results, tab_conclusion, tab_chat = st.tabs([t("tab_params"), t("tab_results"), t("tab_conclusion"), t("tab_chat")])
    with tab_params:
        st.markdown('<div class="glass">', unsafe_allow_html=True)
        col1,col2=st.columns(2)
        with col1:
            m0=st.number_input(t("m0"), value=1000.0); x0_sol=st.number_input(t("x0"), value=0.10); residus=st.number_input(t("residus"), value=20.0); mR=st.number_input(t("mR"), value=100.0); xR=st.number_input(t("xR"), value=0.40)
        with col2:
            T2=st.number_input(t("T2"), value=20.0); T3=st.number_input(t("T3"), value=80.0); cp=st.number_input(t("cp"), value=3.8); x4=st.number_input(t("x4"), value=0.40); lambda_v=st.number_input(t("lambda_v"), value=2300.0)
        st.markdown('</div>', unsafe_allow_html=True)
        st.session_state.params=dict(m0=m0,x0_sol=x0_sol,residus=residus,mR=mR,xR=xR,T2=T2,T3=T3,cp=cp,x4=x4,lambda_v=lambda_v)
    p=st.session_state.get('params',dict(m0=1000.0,x0_sol=0.10,residus=20.0,mR=100.0,xR=0.40,T2=20.0,T3=80.0,cp=3.8,x4=0.40,lambda_v=2300.0))
    m1=p['m0']-p['residus']; x1=(p['m0']*p['x0_sol'])/m1 if m1>0 else 0; m2=m1+p['mR']; x2=(m1*x1+p['mR']*p['xR'])/m2 if m2>0 else 0
    Q3=m2*p['cp']*(p['T3']-p['T2'])/3600; m4=m2*x2/p['x4'] if p['x4']>0 else 0; mv=m2-m4; Q4=mv*p['lambda_v']/3600; Q5=m4*p['cp']*55/3600; erreur=(p['m0']+p['mR'])-(p['residus']+mv+m4)
    with tab_results:
        st.markdown(f"### {t('res_real_time')}")
        r1,r2,r3=st.columns(3); r1.metric(t("metric_m1"), f"{m1:,.2f} kg/h"); r2.metric(t("metric_x2"), f"{x2*100:.2f} %"); r3.metric(t("metric_m4"), f"{m4:,.2f} kg/h")
        r4,r5,r6=st.columns(3); r4.metric(t("metric_mv"), f"{mv:,.2f} kg/h"); r5.metric(t("metric_Q3"), f"{Q3:,.2f} kW"); r6.metric(t("metric_Q4"), f"{Q4:,.2f} kW")
        r7,r8=st.columns(2); r7.metric(t("metric_Q5"), f"{Q5:,.2f} kW"); r8.metric(t("metric_err"), f"{erreur:,.2f} kg/h", delta=f"{erreur:,.2f}", delta_color="inverse")
        st.write(""); st.markdown(f'<div class="glass"><h3>{t("graphs")}</h3>', unsafe_allow_html=True)
        gc1,gc2=st.columns(2)
        with gc1: st.bar_chart(pd.DataFrame({"Etape":["Initial","Filtre","Melange","Final"],"Debit":[p['m0'],m1,m2,m4]}), x="Etape", y="Debit", color=ACCENT)
        with gc2: st.bar_chart(pd.DataFrame({"Operation":["Chauffage","Evaporation","Refroidissement"],"Puissance":[Q3,Q4,Q5]}), x="Operation", y="Puissance", color="#e74c3c")
        st.write(t("obj_reach")); st.progress(min(x2/p['x4'] if p['x4']>0 else 1.0,1.0)); st.caption(f"{t('obj_text')} : {p['x4']*100}% | Actuel : {x2*100:.2f}%")
        st.markdown('</div>', unsafe_allow_html=True)
    with tab_conclusion:
        concls = generate_conclusion(m1,m2,m4,mv,Q3,Q4,Q5,x2,p['x4'],erreur)
        st.markdown(f'<div class="glass"><h3>{t("concl_title")}</h3>', unsafe_allow_html=True)
        for c in concls: st.markdown(f"- {c}")
        st.markdown('</div>', unsafe_allow_html=True); st.write("")
        if abs(erreur)<=1 and x2>=p['x4']: st.success(f"✅ {t('summary')} : " + ("Le procédé est valide." if st.session_state.lang=='FR' else "Process is valid."))
        else: st.warning(f"⚠️ {t('summary')} : " + ("Corrigez les points ci-dessus." if st.session_state.lang=='FR' else "Fix points above."))
        st.write("")
        # EXPORT PDF
        params_dict = {"m0":f"{p['m0']} kg/h","x0":p['x0_sol'],"residus":f"{p['residus']} kg/h","mR":f"{p['mR']} kg/h","xR":p['xR'],"T2":f"{p['T2']} C","T3":f"{p['T3']} C","Cp":p['cp'],"x4":p['x4'],"lambda":p['lambda_v']}
        results_dict = {"m1":f"{m1:.2f} kg/h","m2":f"{m2:.2f} kg/h","x2":f"{x2*100:.2f} %","m4":f"{m4:.2f} kg/h","mv":f"{mv:.2f} kg/h","Q3":f"{Q3:.2f} kW","Q4":f"{Q4:.2f} kW","Q5":f"{Q5:.2f} kW","erreur":f"{erreur:.2f} kg/h"}
        pdf_bytes = create_pdf_report(params_dict, results_dict, concls, st.session_state.get('username','Utilisateur'))
        st.download_button(t("export_pdf"), data=pdf_bytes, file_name=f"rapport_simulateur_{st.session_state.get('username','user')}.pdf", mime="application/pdf", use_container_width=True)
        st.caption("Le PDF contient : paramètres + résultats + conclusion. Parfait pour ton rapport / PFE.")
    with tab_chat:
        st.subheader(t("chat_title"))
        if "messages" not in st.session_state: st.session_state.messages=[{"role":"assistant","content":"Bonjour ! Une question ?" if st.session_state.lang=='FR' else "Hello! Any questions?"}]
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"])
        if prompt:=st.chat_input(t("chat_placeholder")):
            st.session_state.messages.append({"role":"user","content":prompt})
            with st.chat_message("user"): st.markdown(prompt)
            resp=generate_bot_response(prompt); st.session_state.messages.append({"role":"assistant","content":resp})
            with st.chat_message("assistant"): st.markdown(resp)

# --- ROUTAGE ---
if st.session_state.logged_in and st.session_state.page=='app':
    simulator_page()
elif st.session_state.page=='auth':
    auth_page()
else:
    landing_page()
