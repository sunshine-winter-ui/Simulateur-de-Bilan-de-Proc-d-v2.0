import streamlit as st, sqlite3, bcrypt, re, pandas as pd, unicodedata
from io import BytesIO
from datetime import datetime

st.set_page_config(page_title="ProcessLab", layout="wide", page_icon="🧪", initial_sidebar_state="collapsed")

# ---------- ÉTAT ----------
DEFAULTS = {"theme_mode":"dark","lang":"FR","page":"landing","logged_in":False,"messages":[],"auth_tab":"login",
    "params":{"m0":1000.0,"x0_sol":0.10,"residus":20.0,"mR":100.0,"xR":0.40,"T2":20.0,
              "T3":80.0,"cp":3.8,"x4":0.40,"lambda_v":2300.0}}
for k,v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = dict(v) if isinstance(v,dict) else list(v) if isinstance(v,list) else v

T = {
"FR":{"sub":"Filtration • Chauffage • Évaporation","lang":"🇪🇬 English",
  "login":"Se connecter","signup":"Créer un compte","email":"📧 Email","pass":"🔒 Mot de passe",
  "confirm":"🔒 Confirmer","user":"👤 Nom d'utilisateur","login_b":"Se connecter →","signup_b":"Créer mon compte ✨",
  "login_tab":"🔑 Se connecter","signup_tab":"📝 Créer un compte",
  "hello":"Bonjour","logout":"🚪 Se déconnecter","info":"Modifiez les paramètres puis consultez les résultats.",
  "sim_t":"Simulateur de bilan matière et énergétique","sim_c":"Ajustez les paramètres pour visualiser les résultats.",
  "t_par":"⚙️ Paramètres","t_res":"📊 Résultats","t_con":"📝 Conclusion","t_chat":"🤖 Assistant",
  "m0":"Débit initial m₀ (kg/h)","x0":"Fraction x₀ (0–1)","res":"Résidus de filtration (kg/h)",
  "mR":"Débit d'apport mR (kg/h)","xR":"Fraction xR (0–1)","T2":"Température T₂ (°C)","T3":"Température T₃ (°C)",
  "cp":"Capacité thermique Cp (kJ/kg·K)","x4":"Fraction finale visée x₄ (0–1)","lam":"Chaleur latente λv (kJ/kg)",
  "r_t":"Résultats","m_m1":"Débit après filtration","m_x2":"Concentration mélange","m_m4":"Débit final",
  "m_mv":"Débit évaporé","m_Q3":"Puissance chauffage","m_Q4":"Puissance évaporation","m_Q5":"Puissance refroidissement",
  "m_err":"Écart bilan","graphs":"Graphiques","obj":"Atteinte concentration cible","obj_t":"Cible",
  "concl":"Conclusion et recommandations","chat_t":"Assistant virtuel","chat_p":"Posez une question...",
  "err_fill":"Remplissez tous les champs.","err_auth":"Email ou mot de passe incorrect.","err_req":"Tous les champs requis.",
  "err_email":"Email invalide.","err_pass":"Mots de passe différents.","err_len":"Minimum 8 caractères.",
  "err_exist":"Email déjà utilisé.","succ":"Compte créé !","err_c":"Erreur de création.",
  "l_t":"Simulez votre procédé industriel","l_s":"Calculez filtration, chauffage, évaporation. Bilans, graphiques, recommandations.",
  "cta":"Commencer","cta_l":"Se connecter","f1":"⚡ Calculs rapides","f1_d":"Résultats instantanés.",
  "f2":"📊 Tableaux et graphiques","f2_d":"Suivez débits et puissances.","f3":"🤖 Assistant","f3_d":"Explications des calculs.",
  "f4":"📄 Rapport PDF","f4_d":"Export structuré.","how":"Comment ça marche ?","s1":"1. Créez un compte","s1_d":"Inscrivez-vous.",
  "s2":"2. Saisissez les paramètres","s2_d":"Débits, fractions, températures.","s3":"3. Consultez le rapport","s3_d":"Analysez et exportez.",
  "pdf":"📄 Télécharger le rapport PDF","back":"← Retour à l'accueil","proc":"Données d'entrée du procédé",
  "hyp":"Hypothèse : les résidus de filtration sont supposés exempts de soluté."},
"EN":{"sub":"Filtration • Heating • Evaporation","lang":"🇫🇷 Français",
  "login":"Login","signup":"Sign up","email":"📧 Email","pass":"🔒 Password","confirm":"🔒 Confirm",
  "user":"👤 Username","login_b":"Login →","signup_b":"Create account ✨",
  "login_tab":"🔑 Login","signup_tab":"📝 Sign up",
  "hello":"Hello","logout":"🚪 Log out","info":"Edit parameters and view results.",
  "sim_t":"Material and energy balance simulator","sim_c":"Adjust parameters.",
  "t_par":"⚙️ Parameters","t_res":"📊 Results","t_con":"📝 Conclusion","t_chat":"🤖 Assistant",
  "m0":"Initial flow m₀ (kg/h)","x0":"Fraction x₀ (0–1)","res":"Filtration residues (kg/h)","mR":"Added flow mR (kg/h)",
  "xR":"Fraction xR (0–1)","T2":"Inlet temperature T₂ (°C)","T3":"Temperature after heating T₃ (°C)",
  "cp":"Heat capacity Cp (kJ/kg·K)","x4":"Target fraction x₄ (0–1)","lam":"Latent heat λv (kJ/kg)",
  "r_t":"Results","m_m1":"Flow after filtration","m_x2":"Mixture concentration","m_m4":"Final flow",
  "m_mv":"Evaporated flow","m_Q3":"Heating power","m_Q4":"Evaporation power","m_Q5":"Cooling power",
  "m_err":"Balance deviation","graphs":"Charts","obj":"Target concentration achievement","obj_t":"Target",
  "concl":"Conclusion and recommendations","chat_t":"Virtual assistant","chat_p":"Ask a question...",
  "err_fill":"Fill all fields.","err_auth":"Incorrect email or password.","err_req":"All fields required.",
  "err_email":"Invalid email.","err_pass":"Passwords don't match.","err_len":"Min 8 characters.",
  "err_exist":"Email already in use.","succ":"Account created!","err_c":"Creation error.",
  "l_t":"Simulate your industrial process","l_s":"Calculate filtration, heating, evaporation. Balances, charts, recommendations.",
  "cta":"Get started","cta_l":"Login","f1":"⚡ Fast calculations","f1_d":"Instant results.",
  "f2":"📊 Tables and charts","f2_d":"Track flows and power.","f3":"🤖 Assistant","f3_d":"Explanations of calculations.",
  "f4":"📄 PDF report","f4_d":"Structured export.","how":"How does it work?","s1":"1. Create account","s1_d":"Sign up.",
  "s2":"2. Enter parameters","s2_d":"Flows, fractions, temperatures.","s3":"3. View report","s3_d":"Analyze and export.",
  "pdf":"📄 Download PDF report","back":"← Back to home","proc":"Process input data",
  "hyp":"Assumption: filtration residues contain no solute."}}

def theme_label():
    dk = st.session_state.theme_mode == "dark"
    if st.session_state.lang == "FR": return "☀️ Clair" if dk else "🌙 Sombre"
    return "☀️ Light" if dk else "🌙 Dark"

def t(k):
    if k == "theme": return theme_label()
    return T[st.session_state.lang].get(k,k)

# ---------- DB ----------
def init_db():
    with sqlite3.connect("users.db") as c:
        c.execute("CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT,username TEXT NOT NULL,email TEXT UNIQUE NOT NULL,password_hash TEXT NOT NULL)")
def hp(p): return bcrypt.hashpw(p.encode(),bcrypt.gensalt()).decode()
def vp(p,h):
    try: return bcrypt.checkpw(p.encode(),h.encode())
    except: return False
def create_user(u,e,p):
    try:
        with sqlite3.connect("users.db") as c: c.execute("INSERT INTO users(username,email,password_hash)VALUES(?,?,?)",(u,e.lower(),hp(p)))
        return True
    except sqlite3.IntegrityError: return False
def auth_user(e,p):
    with sqlite3.connect("users.db") as c: r=c.execute("SELECT username,password_hash FROM users WHERE email=?",(e.lower(),)).fetchone()
    return r[0] if r and vp(p,r[1]) else None
init_db()

# ---------- PALETTE ----------
dk = st.session_state.theme_mode=="dark"
if dk:
    BG,CRD,TXT,MUT,INP,BRD="#1A1120","#251A2E","#F5EEF7","#B5A0BE","#2D2036","#3D2D47"
    ACC,ACC2,SOFT="#C99FE0","#B886D0","#2A1F2E"
    SH="0 8px 28px rgba(0,0,0,.40)"; SYMO=".55"
    BGG=("radial-gradient(ellipse at 8% 12%,rgba(201,159,224,.22),transparent 32%),"
         "radial-gradient(ellipse at 92% 18%,rgba(244,184,208,.20),transparent 30%),"
         "radial-gradient(ellipse at 82% 88%,rgba(232,198,107,.16),transparent 32%),"
         "linear-gradient(135deg,#1A1120 0%,#1E1526 48%,#241A1A 100%)")
    HBG="linear-gradient(118deg,rgba(37,26,46,.97),rgba(42,30,52,.96) 48%,rgba(50,36,60,.96))"
    FBG="linear-gradient(145deg,rgba(37,26,46,.98),rgba(35,24,44,.96))"; MBG="linear-gradient(145deg,#251A2E,#1E1526)"
    CM,CL,CC,CG="#C99FE0","#F4B8D0","#E8A0BF","#E8C66B"; HB="rgba(201,159,224,.25)"
    FSH="0 12px 30px rgba(0,0,0,.35)"; FSHH="0 17px 34px rgba(201,159,224,.28)"
else:
    BG,CRD,TXT,MUT,INP,BRD="#FDF6FA","#FFFFFF","#2D1B33","#7A6480","#FFFFFF","#EBDBEB"
    ACC,ACC2,SOFT="#8B5A9E","#A972BE","#F5EBF5"
    SH="0 8px 28px rgba(90,40,120,.08)"; SYMO=".65"
    BGG=("radial-gradient(ellipse at 8% 12%,rgba(155,111,191,.28),transparent 32%),"
         "radial-gradient(ellipse at 92% 18%,rgba(232,160,191,.28),transparent 30%),"
         "radial-gradient(ellipse at 82% 88%,rgba(212,162,76,.22),transparent 32%),"
         "linear-gradient(135deg,#FDF6FA 0%,#F5EFF9 48%,#FBF4E8 100%)")
    HBG="linear-gradient(118deg,rgba(255,255,255,.98),rgba(253,246,250,.97) 48%,rgba(251,244,232,.97))"
    FBG="linear-gradient(145deg,rgba(255,255,255,.99),rgba(253,246,250,.97))"; MBG="linear-gradient(145deg,#FFFFFF,#F9EEF5)"
    CM,CL,CC,CG="#9B6FBF","#E8A0BF","#C97B9E","#D4A24C"; HB="rgba(155,111,191,.25)"
    FSH="0 12px 30px rgba(90,40,120,.08)"; FSHH="0 17px 34px rgba(155,111,191,.18)"

st.markdown(f"""<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;600;800&display=swap');
.stApp{{background:{BGG}!important;background-attachment:fixed!important;font-family:'DM Sans',sans-serif;color:{TXT};}}
.block-container{{max-width:1180px;padding-top:2rem;padding-bottom:4rem;position:relative;z-index:1;}}
h1,h2,h3,h4{{color:{TXT}!important;font-family:'Manrope',sans-serif!important;letter-spacing:-.035em;}}
h1{{font-weight:800!important;}} p,label,span,li{{color:{TXT};}}
small,[data-testid="stCaptionContainer"]{{color:{MUT}!important;}}
hr{{border-color:{BRD}!important;}} header[data-testid="stHeader"]{{background:transparent;}}
section[data-testid="stSidebar"]{{background:{CRD};border-right:1px solid {BRD};}}
.hero,.feature{{background:{CRD};border:1px solid {BRD};border-radius:22px;box-shadow:{SH};}}
.hero{{padding:clamp(26px,4vw,46px);margin:18px 0 24px;position:relative;overflow:hidden;background:{HBG}!important;border:1px solid {HB}!important;}}
.hero:before{{content:"✧";position:absolute;right:19%;top:20px;font-size:35px;color:{CG};opacity:.75;animation:twinkle 4s ease-in-out infinite;}}
.hero:after{{content:"";position:absolute;width:260px;height:260px;right:-85px;top:-110px;border-radius:50%;background:radial-gradient(circle at 35% 35%,{CL}33,{CM}22 58%,transparent 70%);}}
.hero h1{{font-size:clamp(30px,4vw,44px)!important;line-height:1.12;margin:14px 0 12px;max-width:760px;position:relative;z-index:1;}}
.hero p{{color:{MUT}!important;font-size:16px;line-height:1.7;max-width:720px;margin-bottom:0;position:relative;z-index:1;}}
.hero-badge{{display:inline-flex;background:{SOFT};color:{ACC}!important;border:1px solid {HB};padding:7px 12px;border-radius:999px;font-size:11px;font-weight:700;letter-spacing:.09em;box-shadow:0 0 0 3px {SOFT}55;}}
.feature{{height:100%;min-height:145px;padding:22px;transition:transform .2s ease;position:relative;overflow:hidden;background:{FBG}!important;box-shadow:{FSH}!important;}}
.feature:hover{{transform:translateY(-3px);box-shadow:{FSHH}!important;}}
.feature:after{{content:"";position:absolute;width:90px;height:90px;right:-38px;bottom:-43px;border-radius:50%;background:linear-gradient(135deg,{CL}24,{CC}20);}}
.feature h3{{font-size:16px;margin:0 0 7px;}} .feature p{{color:{MUT}!important;font-size:13px;line-height:1.6;}}
div[data-testid="stTextInput"] input,div[data-testid="stNumberInput"] input{{background:{INP}!important;color:{TXT}!important;border:1px solid {BRD}!important;border-radius:12px!important;min-height:44px;}}
div[data-testid="stTextInput"] input:focus,div[data-testid="stNumberInput"] input:focus{{border-color:{CL}!important;box-shadow:0 0 0 3px {CL}22!important;}}
div[data-testid="stTextInput"] label,div[data-testid="stNumberInput"] label{{color:{TXT}!important;font-weight:600;font-size:13px;}}

/* Boutons normaux (Violet) */
.stButton>button, .stFormSubmitButton>button{{background:linear-gradient(110deg,{ACC},{ACC2} 58%,{CL})!important;color:#fff!important;border:0!important;border-radius:12px!important;padding:10px 18px;min-height:44px;font-weight:700;box-shadow:0 7px 18px rgba(155,111,191,.32)!important;transition:all .18s ease;}}
.stButton>button:hover, .stFormSubmitButton>button:hover{{background:linear-gradient(110deg,{ACC2},{ACC} 58%,{CL}cc)!important;box-shadow:0 10px 23px rgba(155,111,191,.45)!important;transform:translateY(-1px);}}

/* ⭐ Boutons Spéciaux (Doré) sans utiliser type="primary" */
div[data-testid="stHorizontalBlock"] > div:nth-child(4) .stButton>button,
div[data-testid="stForm"] button {{
    background:linear-gradient(110deg,{CG},{CC} 55%,{CL})!important;
    color:#2D1B33!important;border:0!important;font-weight:800!important;
    box-shadow:0 7px 18px rgba(212,162,76,.4),0 0 0 0 rgba(212,162,76,.5)!important;
    animation:pulseGold 2.5s ease-in-out infinite;
}}
div[data-testid="stHorizontalBlock"] > div:nth-child(4) .stButton>button:hover,
div[data-testid="stForm"] button:hover {{
    animation:none;background:linear-gradient(110deg,{CC},{CG} 55%,{CL})!important;
    box-shadow:0 10px 26px rgba(212,162,76,.55)!important;transform:translateY(-1px);
}}

section[data-testid="stSidebar"] .stButton>button{{background:linear-gradient(110deg,{ACC},{CL})!important;}}
.stDownloadButton>button{{background:{SOFT}!important;color:{ACC}!important;border:1px solid {BRD}!important;border-radius:12px!important;min-height:44px;font-weight:700;}}
button[data-baseweb="tab"]{{color:{MUT}!important;font-weight:600;padding:12px 16px!important;}}
button[data-baseweb="tab"][aria-selected="true"]{{color:{ACC}!important;border-bottom:2px solid {ACC}!important;background:transparent!important;}}
div[data-testid="stMetric"]{{background:{MBG}!important;border:1px solid {HB}!important;border-radius:17px;padding:17px 18px;box-shadow:{SH};}}
div[data-testid="stMetric"]:nth-of-type(3n+1){{border-top:3px solid {CM}!important;}}
div[data-testid="stMetric"]:nth-of-type(3n+2){{border-top:3px solid {CL}!important;}}
div[data-testid="stMetric"]:nth-of-type(3n){{border-top:3px solid {CC}!important;}}
div[data-testid="stMetricLabel"]{{color:{MUT}!important;font-size:12px;font-weight:600;}}
div[data-testid="stMetricValue"]{{color:{ACC}!important;font-family:'Manrope',sans-serif;font-weight:800;}}
div[data-testid="stDataFrame"]{{border:1px solid {BRD};border-radius:14px;overflow:hidden;}}
div[data-testid="stChatMessage"]{{background:{CRD};border:1px solid {BRD};border-radius:16px;padding:12px 16px;margin-bottom:10px;}}
div[data-testid="stProgressBar"]>div>div{{background:linear-gradient(90deg,{ACC},{CL},{CG})!important;border-radius:99px;}}
div[data-testid="stAlert"]{{border-radius:14px;}} #MainMenu{{visibility:hidden;}} footer{{visibility:hidden;}}

.floating-lab-art{{position:fixed;inset:0;overflow:hidden;pointer-events:none;z-index:0;}}
.lab-symbol{{position:absolute;display:block;user-select:none;font-weight:700;text-shadow:0 0 14px currentColor,0 6px 14px rgba(120,60,150,.18);filter:drop-shadow(0 5px 9px rgba(120,60,150,.15));animation:floatAround 14s ease-in-out infinite;will-change:transform;}}
.lab-symbol.s1{{top:12%;left:3%;font-size:38px;color:{CM};opacity:{SYMO};animation-delay:-2s;animation-duration:13s;}}
.lab-symbol.s2{{top:22%;right:4%;font-size:42px;color:{CL};opacity:{SYMO};animation-delay:-6s;animation-duration:16s;}}
.lab-symbol.s3{{top:68%;left:4%;font-size:34px;color:{CC};opacity:{SYMO};animation-delay:-9s;animation-duration:15s;}}
.lab-symbol.s4{{top:80%;right:6%;font-size:40px;color:{CG};opacity:{SYMO};animation-delay:-4s;animation-duration:17s;}}
.lab-symbol.s5{{top:46%;right:2%;font-size:26px;color:{CM};opacity:{SYMO};animation-delay:-7s;animation-duration:11s;}}
.lab-symbol.s6{{top:5%;right:30%;font-size:24px;color:{CL};opacity:{SYMO};animation-delay:-1s;animation-duration:14s;}}
.lab-symbol.s7{{top:34%;left:12%;font-size:22px;color:{CC};opacity:{SYMO};animation-delay:-11s;animation-duration:12s;}}
.lab-symbol.s8{{top:56%;right:14%;font-size:30px;color:{CG};opacity:{SYMO};animation-delay:-3s;animation-duration:18s;}}
.lab-symbol.s9{{top:90%;left:22%;font-size:20px;color:{CM};opacity:{SYMO};animation-delay:-8s;animation-duration:15s;}}
.lab-symbol.s10{{top:18%;left:38%;font-size:18px;color:{CL};opacity:{SYMO};animation-delay:-5s;animation-duration:13s;}}
.lab-orb{{position:absolute;border-radius:50%;background:linear-gradient(135deg,{CM},{CL});box-shadow:0 0 22px {CL}88,0 0 8px {CM}aa;animation:orbDrift 12s ease-in-out infinite;}}
.lab-orb.o1{{top:38%;left:10%;width:11px;height:11px;}}
.lab-orb.o2{{top:83%;left:43%;width:8px;height:8px;animation-delay:-5s;}}
.lab-orb.o3{{top:15%;right:15%;width:9px;height:9px;animation-delay:-3s;}}
.lab-orb.o4{{top:64%;left:28%;width:6px;height:6px;animation-delay:-8s;background:linear-gradient(135deg,{CC},{CG});box-shadow:0 0 18px {CC}88;}}
.lab-orb.o5{{top:50%;right:33%;width:7px;height:7px;animation-delay:-6s;background:linear-gradient(135deg,{CM},{CG});box-shadow:0 0 18px {CM}88;}}
@keyframes floatAround{{0%,100%{{transform:translate3d(0,0,0) rotate(-8deg) scale(1);}}50%{{transform:translate3d(12px,-24px,0) rotate(12deg) scale(1.08);}}}}
@keyframes orbDrift{{0%,100%{{transform:translateY(0) scale(.85);opacity:.55;}}50%{{transform:translateY(-26px) scale(1.4);opacity:1;}}}}
@keyframes twinkle{{0%,100%{{transform:scale(.8);opacity:.45;}}50%{{transform:scale(1.2) rotate(18deg);opacity:1;}}}}
@keyframes pulseGold{{0%,100%{{box-shadow:0 7px 18px rgba(212,162,76,.4),0 0 0 0 rgba(212,162,76,.5);}}50%{{box-shadow:0 7px 22px rgba(212,162,76,.55),0 0 0 10px rgba(212,162,76,0);}}}}
@media(prefers-reduced-motion:reduce){{.lab-symbol,.lab-orb,.hero:before,.stButton>button[kind="primary"]{{animation:none!important;}}}}
@media(max-width:700px){{.lab-symbol{{opacity:.18!important;}} .lab-symbol.s1,.lab-symbol.s3,.lab-symbol.s5,.lab-symbol.s9{{display:none;}}}}
</style>
<div class="floating-lab-art" aria-hidden="true">
<span class="lab-symbol s1">⚗</span><span class="lab-symbol s2">✧</span><span class="lab-symbol s3">⌬</span>
<span class="lab-symbol s4">❋</span><span class="lab-symbol s5">⚛</span><span class="lab-symbol s6">∿</span>
<span class="lab-symbol s7">✦</span><span class="lab-symbol s8">◈</span><span class="lab-symbol s9">⋆</span>
<span class="lab-symbol s10">⚛</span>
<i class="lab-orb o1"></i><i class="lab-orb o2"></i><i class="lab-orb o3"></i><i class="lab-orb o4"></i><i class="lab-orb o5"></i>
</div>""", unsafe_allow_html=True)

# ---------- UI HELPERS ----------
def logo(): return f'<div style="display:flex;align-items:center;gap:12px;padding:4px"><div style="width:46px;height:46px;border-radius:15px;background:{SOFT};display:grid;place-items:center;font-size:23px">⚗️</div><div style="line-height:1.12;text-align:left"><div style="font-family:Manrope,sans-serif;font-size:22px;font-weight:800;letter-spacing:-.7px;color:{TXT}">Process<span style="color:{ACC}">Lab</span></div><div style="font-size:10px;font-weight:700;letter-spacing:2.5px;color:{MUT};margin-top:4px">PROCESS LAB · INDUSTRIE</div></div></div>'

def toggle_lang(): st.session_state.lang="EN" if st.session_state.lang=="FR" else "FR"; st.rerun()
def toggle_theme(): st.session_state.theme_mode="light" if st.session_state.theme_mode=="dark" else "dark"; st.rerun()

def top_bar():
    # Colonnes en nombres entiers pour compatibilité maximale
    c1,c2,c3,c4 = st.columns([4,1,1,2])
    with c1: st.markdown(logo(), unsafe_allow_html=True)
    with c2:
        if st.button(t("theme"), key="tb_th", use_container_width=True): toggle_theme()
    with c3:
        if st.button(t("lang"), key="tb_lg", use_container_width=True): toggle_lang()
    with c4:
        if st.button(f"🔑 {t('login')}", key="tb_li", use_container_width=True):
            st.session_state.auth_tab = "login"
            st.session_state.page = "auth"
            st.rerun()

# ---------- CALCULS ----------
def calc(p):
    m1=p["m0"]-p["residus"]; sol=p["m0"]*p["x0_sol"]
    x1=sol/m1 if m1>0 else 0
    m2=m1+p["mR"]; sol2=sol+p["mR"]*p["xR"]; x2=sol2/m2 if m2>0 else 0
    Q3=m2*p["cp"]*(p["T3"]-p["T2"])/3600
    m4=sol2/p["x4"] if p["x4"]>0 else 0; mv=m2-m4
    Q4=mv*p["lambda_v"]/3600; Q5=m4*p["cp"]*55/3600
    feed=p["m0"]+p["mR"]; out=p["residus"]+mv+m4
    return {"m1":m1,"x1":x1,"m2":m2,"x2":x2,"m4":m4,"mv":mv,"Q3":Q3,"Q4":Q4,"Q5":Q5,"feed":feed,"output":out,"error":feed-out}

def validate(p):
    e=[]
    if p["m0"]<=0: e.append("m₀ doit être > 0.")
    if p["mR"]<0: e.append("mR ne peut pas être négatif.")
    if not 0<=p["x0_sol"]<=1: e.append("x₀ doit être dans [0,1].")
    if not 0<=p["xR"]<=1: e.append("xR doit être dans [0,1].")
    if not 0<p["x4"]<=1: e.append("x₄ doit être dans ]0,1].")
    if not 0<=p["residus"]<p["m0"]: e.append("Résidus doivent être < m₀.")
    if p["cp"]<=0: e.append("Cp doit être > 0.")
    if p["lambda_v"]<=0: e.append("λv doit être > 0.")
    if p["T3"]<p["T2"]: e.append("T₃ doit être ≥ T₂.")
    return e

def concl(r,p):
    c=[]
    if r["mv"]<-1e-9: c.append("Concentration mélange déjà > cible : dilution nécessaire.")
    else:
        c.append(f"Après filtration, débit = {r['m1']:.2f} kg/h. Après mélange, débit = {r['m2']:.2f} kg/h.")
        c.append(f"Concentration mélange : {r['x2']*100:.2f} % ; cible : {p['x4']*100:.2f} %.")
        c.append(f"Débit final : {r['m4']:.2f} kg/h ; débit évaporé : {r['mv']:.2f} kg/h.")
    c.append("Bilan matière numériquement fermé." if abs(r["error"])<=1e-6 else f"Écart de bilan : {r['error']:.4f} kg/h.")
    if r["Q4"]>200: c.append(f"Puissance d'évaporation élevée ({r['Q4']:.2f} kW) : récupération thermique à étudier.")
    if r["Q3"]>=0: c.append(f"Puissance thermique de chauffage : {r['Q3']:.2f} kW.")
    return c

# ---------- PDF ----------
def make_pdf(params, res, conc, user, raw):
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from xml.sax.saxutils import escape
    p = raw["p"]; r = raw["r"]
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, rightMargin=17*mm, leftMargin=17*mm, topMargin=25*mm, bottomMargin=22*mm,
        title="Rapport de simulation - ProcessLab", author="ProcessLab")
    purple=colors.HexColor("#8B5A9E"); violet2=colors.HexColor("#A972BE")
    rose=colors.HexColor("#E8A0BF"); rose_gold=colors.HexColor("#C97B9E")
    gold=colors.HexColor("#D4A24C"); navy=colors.HexColor("#2D1B33")
    pale=colors.HexColor("#F5EBF5"); grey=colors.HexColor("#7A6480")
    S = getSampleStyleSheet()
    S.add(ParagraphStyle(name="RT", parent=S["Title"], fontName="Helvetica-Bold", fontSize=20, leading=24, textColor=navy, alignment=TA_CENTER, spaceAfter=5))
    S.add(ParagraphStyle(name="ST", parent=S["Heading2"], fontName="Helvetica-Bold", fontSize=12, leading=15, textColor=purple, spaceBefore=14, spaceAfter=8))
    S.add(ParagraphStyle(name="SUB", parent=S["BodyText"], fontSize=9, leading=12, textColor=grey, alignment=TA_CENTER, spaceAfter=10))
    S.add(ParagraphStyle(name="SC", parent=S["BodyText"], fontName="Helvetica", fontSize=8.5, leading=11, textColor=navy))
    S.add(ParagraphStyle(name="SCH", parent=S["BodyText"], fontName="Helvetica-Bold", fontSize=8.5, leading=11, textColor=colors.white))
    S.add(ParagraphStyle(name="SCB", parent=S["BodyText"], fontName="Helvetica-Bold", fontSize=9, leading=12, textColor=navy))
    S.add(ParagraphStyle(name="RB", parent=S["BodyText"], fontSize=9.5, leading=14, textColor=navy, spaceAfter=5))
    def cell(v,h=False): return Paragraph(escape(str(v)).replace("\n","<br/>"), S["SCH" if h else "SC"])
    def tbl(rows, widths=None, header_color=purple):
        data = [[cell(v, i==0) for v in row] for i, row in enumerate(rows)]
        tb = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
        tb.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,0),header_color),("TEXTCOLOR",(0,0),(-1,0),colors.white),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,pale]),
            ("GRID",(0,0),(-1,-1),0.45,colors.HexColor("#EBDBEB")),
            ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
            ("LEFTPADDING",(0,0),(-1,-1),7),("RIGHTPADDING",(0,0),(-1,-1),7),
            ("TOPPADDING",(0,0),(-1,-1),6),("BOTTOMPADDING",(0,0),(-1,-1),6),
        ]))
        return tb
    def deco(cv,d):
        cv.saveState(); w,h=A4
        cv.setFillColor(purple); cv.rect(0,h-13*mm,w,13*mm,fill=1,stroke=0)
        cv.setFillColor(gold); cv.rect(0,h-14*mm,w,1*mm,fill=1,stroke=0)
        cv.setFillColor(colors.white); cv.setFont("Helvetica-Bold",9)
        cv.drawString(17*mm,h-8.5*mm,"PROCESSLAB  |  RAPPORT DE PROCÉDÉ")
        cv.drawRightString(w-17*mm,h-8.5*mm,"SIMULATEUR PRO V2")
        cv.setStrokeColor(rose); cv.setLineWidth(0.5); cv.line(17*mm,15*mm,w-17*mm,15*mm)
        cv.setFillColor(grey); cv.setFont("Helvetica",7.5)
        cv.drawString(17*mm,10*mm,"Document généré automatiquement - Usage pédagogique")
        cv.drawRightString(w-17*mm,10*mm,f"Page {d.page}")
        cv.restoreState()
    story=[
        Spacer(1,5*mm),
        Paragraph("RAPPORT DE SIMULATION", S["RT"]),
        Paragraph("Filtration • Mélange • Chauffage • Évaporation", S["SUB"]),
        Spacer(1,3*mm),
        tbl([["Informations générales","Valeur"],["Utilisateur",user],
             ["Date de génération",datetime.now().strftime("%d/%m/%Y à %H:%M")],
             ["Application","ProcessLab - Simulateur Pro V2"],
             ["Statut","Simulation valide" if abs(r["error"])<1e-6 else "Écart détecté"]],[65*mm,105*mm]),
    ]
    story.append(Spacer(1,4*mm)); story.append(Paragraph("Résultats clés", S["ST"]))
    kpi = Table([
        [cell("m₄ final",True),cell("x₂ concentration",True),cell("mv évaporé",True)],
        [cell(f"{r['m4']:.1f} kg/h"),cell(f"{r['x2']*100:.1f} %"),cell(f"{r['mv']:.1f} kg/h")],
        [cell("Q₃ chauffage",True),cell("Q₄ évaporation",True),cell("Écart bilan",True)],
        [cell(f"{r['Q3']:.1f} kW"),cell(f"{r['Q4']:.1f} kW"),cell(f"{r['error']:.4f} kg/h")],
    ], colWidths=[56*mm]*3)
    kpi.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(0,0),purple),("BACKGROUND",(1,0),(1,0),violet2),("BACKGROUND",(2,0),(2,0),rose_gold),
        ("BACKGROUND",(0,2),(0,2),purple),("BACKGROUND",(1,2),(1,2),violet2),("BACKGROUND",(2,2),(2,2),rose_gold),
        ("BACKGROUND",(0,1),(-1,1),colors.white),("BACKGROUND",(0,3),(-1,3),colors.white),
        ("GRID",(0,0),(-1,-1),0.45,colors.HexColor("#EBDBEB")),
        ("ALIGN",(0,0),(-1,-1),"CENTER"),("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
    ]))
    story.append(kpi)
    story.append(Paragraph("1. Paramètres opératoires", S["ST"]))
    story.append(tbl([["Paramètre","Valeur"]]+[[k,v] for k,v in params.items()],[85*mm,85*mm]))
    story.append(Paragraph("2. Bilan matière", S["ST"]))
    story.append(tbl([["Grandeur","Résultat"]]+[[k,v] for k,v in res["matter"].items()],[85*mm,85*mm]))
    story.append(Paragraph("3. Bilan énergétique", S["ST"]))
    story.append(tbl([["Grandeur","Résultat"]]+[[k,v] for k,v in res["energy"].items()],[85*mm,85*mm],header_color=rose_gold))
    if "flow" in res:
        story.append(Paragraph("4. Schéma du procédé", S["ST"]))
        story.append(tbl(res["flow"]))
    if "formulas" in res:
        story.append(Paragraph("5. Formules utilisées", S["ST"]))
        story.append(tbl(res["formulas"], header_color=rose_gold))
    story.append(Paragraph("6. Conclusions et recommandations", S["ST"]))
    for x in conc: story.append(Paragraph("• " + escape(str(x)), S["RB"]))
    story.append(Paragraph("7. Validation du rapport", S["ST"]))
    sig = Table([
        [cell("Rédigé par",True),cell("Vérifié par",True),cell("Approuvé par",True)],
        [cell(user),cell("________________"),cell("________________")],
        [cell("Date : "+datetime.now().strftime("%d/%m/%Y")),cell("Date : ________"),cell("Date : ________")],
    ], colWidths=[56*mm]*3)
    sig.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),purple),("GRID",(0,0),(-1,-1),0.45,colors.HexColor("#EBDBEB")),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),("TOPPADDING",(0,0),(-1,-1),8),("BOTTOMPADDING",(0,0),(-1,-1),8),
    ]))
    story.append(sig)
    story.append(Spacer(1,5*mm))
    story.append(Paragraph("<b>Note méthodologique :</b> les résidus sont supposés exempts de soluté. Le bilan est calculé sur les mêmes relations de débit ; la fermeture numérique ne constitue pas une validation expérimentale indépendante.", S["RB"]))
    doc.build(story, onFirstPage=deco, onLaterPages=deco)
    buf.seek(0); return buf.getvalue()

# ---------- CHATBOT ----------
def clean(s): return re.sub(r"\s+"," ",re.sub(r"[^a-z0-9\s]"," ",unicodedata.normalize("NFD",s.lower()).encode("ascii","ignore").decode())).strip()
def bot(q):
    p=st.session_state.params; e=validate(p)
    if e: return "Corrigez d'abord : "+" ".join(e)
    r=calc(p); q=clean(q)
    if any(x in q for x in["bonjour","salut","hello","hi"]): return "Bonjour ! Demandez-moi m1, x2, Q3, Q4, bilan ou hypothèses."
    if any(x in q for x in["filtration","m1","residu"]): return f"m1 = m0 − résidus = {p['m0']:.2f} − {p['residus']:.2f} = **{r['m1']:.2f} kg/h**."
    if any(x in q for x in["concentration","x2","melange"]): return f"x2 = **{r['x2']*100:.2f} %**."
    if any(x in q for x in["chauffage","q3","temperature"]): return f"Q3 = **{r['Q3']:.2f} kW**."
    if any(x in q for x in["evaporation","evaporer","q4","mv","m4"]): return f"m4 = **{r['m4']:.2f} kg/h**, mv = **{r['mv']:.2f} kg/h**, Q4 = **{r['Q4']:.2f} kW**."
    if any(x in q for x in["bilan","erreur"]): return f"Entrées = {r['feed']:.2f} ; sorties = {r['output']:.2f} ; écart = **{r['error']:.6f} kg/h**."
    if any(x in q for x in["hypothese","hypotheses","solute"]): return "Résidus sans soluté ; soluté non volatil."
    if any(x in q for x in["pdf","rapport"]): return "Ouvrez l'onglet Conclusion pour télécharger le PDF."
    return "Posez une question sur filtration, concentration, chauffage, évaporation ou bilan."

# ---------- PAGES ----------
def landing():
    top_bar()
    st.markdown(f'<div class="hero"><span class="hero-badge">CHIMIE · GÉNIE DES PROCÉDÉS</span><h1 style="font-size:34px;margin:14px 0 8px">{t("l_t")}</h1><p>{t("l_s")}</p><div style="display:flex;flex-wrap:wrap;gap:8px;margin-top:22px;position:relative;z-index:1"><span class="hero-badge">01 · Filtration</span><span class="hero-badge">02 · Chauffage</span><span class="hero-badge">03 · Évaporation</span></div></div>',unsafe_allow_html=True)
    c1,c2=st.columns(2)
    with c1:
        if st.button(f"🚀 {t('cta')}", key="cta_start", use_container_width=True):
            st.session_state.auth_tab="signup"; st.session_state.page="auth"; st.rerun()
    with c2:
        if st.button(f"🔑 {t('cta_l')}", key="cta_login", use_container_width=True):
            st.session_state.auth_tab="login"; st.session_state.page="auth"; st.rerun()
    st.write("")
    for col,(a,b) in zip(st.columns(4),[(t("f1"),t("f1_d")),(t("f2"),t("f2_d")),(t("f3"),t("f3_d")),(t("f4"),t("f4_d"))]):
        with col: st.markdown(f'<div class="feature"><h3>{a}</h3><p>{b}</p></div>',unsafe_allow_html=True)
    st.write(""); st.markdown(f"<h2 style='text-align:center'>{t('how')}</h2>",unsafe_allow_html=True)
    for col,(a,b) in zip(st.columns(3),[(t("s1"),t("s1_d")),(t("s2"),t("s2_d")),(t("s3"),t("s3_d"))]):
        with col: st.markdown(f'<div class="feature"><h3>{a}</h3><p>{b}</p></div>',unsafe_allow_html=True)
    st.markdown(f"<p style='text-align:center;color:{MUT};margin-top:35px'>ProcessLab • Apprentissage du génie des procédés</p>",unsafe_allow_html=True)

def auth():
    top_bar()
    if st.button(t("back"), key="back_btn"): st.session_state.page="landing"; st.rerun()
    _,mid,_=st.columns([1,2,1])
    with mid:
        st.markdown(logo(),unsafe_allow_html=True)
        tl,ts=st.tabs([t("login_tab"),t("signup_tab")])
        with tl:
            if st.session_state.get("auth_tab")=="signup": st.caption(f"👆 Onglet 📝 {t('signup_tab')} pour créer un compte")
            with st.form("lf"):
                e=st.text_input(t("email"),placeholder="exemple@email.com",key="lf_email")
                p=st.text_input(t("pass"),type="password",key="lf_pass")
                s=st.form_submit_button(t("login_b"),use_container_width=True)
            if s:
                if not e or not p: st.error(t("err_fill"))
                else:
                    u=auth_user(e.strip(),p)
                    if u: st.session_state.update(logged_in=True,username=u,page="app"); st.rerun()
                    else: st.error(t("err_auth"))
        with ts:
            if st.session_state.get("auth_tab")=="login": st.caption(f"👆 Onglet 🔑 {t('login_tab')} pour se connecter")
            with st.form("sf"):
                u=st.text_input(t("user"),key="sf_user")
                e=st.text_input(t("email"),placeholder="exemple@email.com",key="sf_email")
                p=st.text_input(t("pass"),type="password",key="sf_pass")
                c=st.text_input(t("confirm"),type="password",key="sf_conf")
                s=st.form_submit_button(t("signup_b"),use_container_width=True)
            if s:
                if not all([u,e,p,c]): st.error(t("err_req"))
                elif not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+",e.strip()): st.error(t("err_email"))
                elif p!=c: st.error(t("err_pass"))
                elif len(p)<8: st.error(t("err_len"))
                elif create_user(u.strip(),e.strip(),p): st.session_state.update(logged_in=True,username=u.strip(),page="app"); st.success(t("succ")); st.rerun()
                else: st.error(t("err_exist"))

def simulator():
    with st.sidebar:
        st.markdown(logo(),unsafe_allow_html=True)
        st.markdown(f"**{t('hello')}, {st.session_state.get('username','User')}**")
        if st.button(t("lang"),key="sb_lg",use_container_width=True): toggle_lang()
        if st.button(t("theme"),key="sb_th",use_container_width=True): toggle_theme()
        st.info(t("info"))
        if st.button(t("logout"),key="sb_lo",use_container_width=True):
            st.session_state.update(logged_in=False,page="landing",messages=[]); st.rerun()
    st.markdown(f'<div class="hero"><span class="hero-badge">ESPACE DE SIMULATION</span><h1 style="margin:10px 0 6px">{t("sim_t")}</h1><p>{t("sim_c")}</p><div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:20px;position:relative;z-index:1"><span class="hero-badge">Filtration</span><span class="hero-badge">Mélange</span><span class="hero-badge">Chauffage</span><span class="hero-badge">Évaporation</span></div></div>',unsafe_allow_html=True)
    tp,tr,tc,tch=st.tabs([t("t_par"),t("t_res"),t("t_con"),t("t_chat")])
    with tp:
        st.subheader(t("proc")); c1,c2=st.columns(2); p0=st.session_state.params
        with c1:
            m0=st.number_input(t("m0"),min_value=0.001,value=float(p0["m0"]),step=10.0)
            x0=st.number_input(t("x0"),min_value=0.0,max_value=1.0,value=float(p0["x0_sol"]),step=0.01,format="%.3f")
            rs=st.number_input(t("res"),min_value=0.0,value=float(p0["residus"]),step=1.0)
            mR=st.number_input(t("mR"),min_value=0.0,value=float(p0["mR"]),step=10.0)
            xR=st.number_input(t("xR"),min_value=0.0,max_value=1.0,value=float(p0["xR"]),step=0.01,format="%.3f")
        with c2:
            T2=st.number_input(t("T2"),value=float(p0["T2"]),step=1.0)
            T3=st.number_input(t("T3"),value=float(p0["T3"]),step=1.0)
            cp=st.number_input(t("cp"),min_value=0.001,value=float(p0["cp"]),step=0.1)
            x4=st.number_input(t("x4"),min_value=0.001,max_value=1.0,value=float(p0["x4"]),step=0.01,format="%.3f")
            lam=st.number_input(t("lam"),min_value=0.001,value=float(p0["lambda_v"]),step=10.0)
        st.session_state.params={"m0":m0,"x0_sol":x0,"residus":rs,"mR":mR,"xR":xR,"T2":T2,"T3":T3,"cp":cp,"x4":x4,"lambda_v":lam}
        st.caption(t("hyp"))
    p=st.session_state.params; errs=validate(p)
    if errs:
        with tr:
            st.error("Simulation impossible :")
            for e in errs: st.write("• "+e)
        with tc: st.warning("Corrigez les paramètres dans l'onglet Paramètres.")
        with tch: st.info("Assistant indisponible jusqu'à correction.")
        return
    r=calc(p); cs=concl(r,p)
    warn="Concentration initiale > cible : mv négatif, dilution nécessaire." if r["mv"]<-1e-9 else None
    with tr:
        st.subheader(t("r_t"))
        if warn: st.warning(warn)
        M=[(t("m_m1"),f"{r['m1']:,.2f} kg/h"),(t("m_x2"),f"{r['x2']*100:.2f} %"),(t("m_m4"),f"{r['m4']:,.2f} kg/h"),(t("m_mv"),f"{r['mv']:,.2f} kg/h"),(t("m_Q3"),f"{r['Q3']:,.2f} kW"),(t("m_Q4"),f"{r['Q4']:,.2f} kW"),(t("m_Q5"),f"{r['Q5']:,.2f} kW"),(t("m_err"),f"{r['error']:,.6f} kg/h")]
        for s in (0,4):
            for col,(l,v) in zip(st.columns(4),M[s:s+4]):
                with col: st.metric(l,v)
        st.divider(); st.markdown("### Tableau 1 — Paramètres"); st.dataframe(pd.DataFrame([["Débit initial m₀",p["m0"],"kg/h"],["Fraction x₀",p["x0_sol"],"—"],["Résidus",p["residus"],"kg/h"],["Débit mR",p["mR"],"kg/h"],["Fraction xR",p["xR"],"—"],["T₂",p["T2"],"°C"],["T₃",p["T3"],"°C"],["Cp",p["cp"],"kJ/(kg·K)"],["Fraction x₄",p["x4"],"—"],["λv",p["lambda_v"],"kJ/kg"]],columns=["Paramètre","Valeur","Unité"]),use_container_width=True,hide_index=True)
        st.markdown("### Tableau 2 — Bilan matière"); st.dataframe(pd.DataFrame([["m₀",p["m0"],"kg/h"],["Résidus",p["residus"],"kg/h"],["m₁",r["m1"],"kg/h"],["mR",p["mR"],"kg/h"],["m₂",r["m2"],"kg/h"],["x₂",r["x2"]*100,"%"],["m₄",r["m4"],"kg/h"],["mv",r["mv"],"kg/h"],["Entrées",r["feed"],"kg/h"],["Sorties",r["output"],"kg/h"],["Écart",r["error"],"kg/h"]],columns=["Grandeur","Valeur","Unité"]),use_container_width=True,hide_index=True)
        st.markdown("### Tableau 3 — Bilan énergétique"); st.dataframe(pd.DataFrame([["Q₃ chauffage",r["Q3"],"kW"],["Q₄ évaporation",r["Q4"],"kW"],["Q₅ refroidissement",r["Q5"],"kW"]],columns=["Opération","Puissance","Unité"]),use_container_width=True,hide_index=True)
        st.divider(); st.markdown(f"### {t('graphs')}")
        g1,g2=st.columns(2)
        with g1:
            st.caption("Débits massiques"); st.bar_chart(pd.DataFrame({"Étape":["Initial","Après filtration","Après mélange","Final"],"Débit (kg/h)":[p["m0"],r["m1"],r["m2"],r["m4"]]}).set_index("Étape"))
        with g2:
            st.caption("Puissances thermiques"); st.bar_chart(pd.DataFrame({"Opération":["Chauffage","Évaporation","Refroidissement"],"Puissance (kW)":[r["Q3"],r["Q4"],r["Q5"]]}).set_index("Opération"))
        st.markdown(f"**{t('obj')}**"); st.progress(max(0.0,min(r["x2"]/p["x4"],1.0)))
        st.caption(f"{t('obj_t')} : {p['x4']*100:.2f} % | Obtenue : {r['x2']*100:.2f} %")
        st.info("Écart calculé via m₄ et mv issus des mêmes équations. Nul = cohérence arithmétique, pas validation expérimentale.")
    with tc:
        st.subheader(t("concl"))
        if warn: st.warning(warn)
        for x in cs: st.markdown(f"- {x}")
        if not warn and r["x2"]>=p["x4"]: st.success("Cible atteinte ou dépassée.")
        elif not warn: st.warning("Cible non atteinte.")
        params_pdf={"m₀":f"{p['m0']:.2f} kg/h","x₀":f"{p['x0_sol']:.4f}","Résidus":f"{p['residus']:.2f} kg/h","mR":f"{p['mR']:.2f} kg/h","xR":f"{p['xR']:.4f}","T₂":f"{p['T2']:.2f} °C","T₃":f"{p['T3']:.2f} °C","Cp":f"{p['cp']:.3f} kJ/(kg·K)","x₄":f"{p['x4']:.4f}","λv":f"{p['lambda_v']:.2f} kJ/kg"}
        res_pdf={
            "matter":{"m₁":f"{r['m1']:.2f} kg/h","m₂":f"{r['m2']:.2f} kg/h","x₂":f"{r['x2']*100:.2f} %","m₄":f"{r['m4']:.2f} kg/h","mv":f"{r['mv']:.2f} kg/h","Entrées":f"{r['feed']:.2f} kg/h","Sorties":f"{r['output']:.2f} kg/h","Écart":f"{r['error']:.6f} kg/h"},
            "energy":{"Q₃":f"{r['Q3']:.2f} kW","Q₄":f"{r['Q4']:.2f} kW","Q₅":f"{r['Q5']:.2f} kW"},
            "flow":[
                ["Étape","Entrée","Sortie"],
                ["Alimentation",f"m₀ = {p['m0']:.1f} kg/h (x₀ = {p['x0_sol']:.3f})","—"],
                ["Filtration",f"m₀ = {p['m0']:.1f} kg/h",f"m₁ = {r['m1']:.1f} kg/h + résidus = {p['residus']:.1f} kg/h"],
                ["Mélange + mR",f"m₁ = {r['m1']:.1f} + mR = {p['mR']:.1f} kg/h",f"m₂ = {r['m2']:.1f} kg/h"],
                ["Chauffage",f"T₂ = {p['T2']:.0f}°C → T₃ = {p['T3']:.0f}°C",f"Q₃ = {r['Q3']:.1f} kW"],
                ["Évaporation",f"Q₄ = {r['Q4']:.1f} kW",f"mv = {r['mv']:.1f} kg/h"],
                ["Produit final","—",f"m₄ = {r['m4']:.1f} kg/h (x₄ = {p['x4']:.3f})"]
            ],
            "formulas":[
                ["Grandeur","Formule"],
                ["m₁ (après filtration)","m₀ − résidus"],
                ["x₂ (concentration mélange)","(m₀·x₀ + mR·xR) / (m₀ − résidus + mR)"],
                ["Q₃ (chauffage)","m₂ · Cp · (T₃ − T₂) / 3600"],
                ["m₄ (produit final)","(m₀·x₀ + mR·xR) / x₄"],
                ["mv (eau évaporée)","m₂ − m₄"],
                ["Q₄ (évaporation)","mv · λv / 3600"],
                ["Q₅ (refroidissement)","m₄ · Cp · 55 / 3600"]
            ]
        }
        st.download_button(t("pdf"),data=make_pdf(params_pdf,res_pdf,cs,st.session_state.get("username","User"),{"p":p,"r":r}),file_name="rapport_processlab.pdf",mime="application/pdf",use_container_width=True)
        st.caption("Le rapport contient : KPI, paramètres, bilans, schéma du procédé, formules et validation.")
    with tch:
        st.subheader(t("chat_t"))
        if not st.session_state.messages: st.session_state.messages=[{"role":"assistant","content":"Bonjour ! Je peux expliquer filtration, chauffage, évaporation et bilans."}]
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"])
        if pr:=st.chat_input(t("chat_p")):
            st.session_state.messages.append({"role":"user","content":pr})
            with st.chat_message("user"): st.markdown(pr)
            rep=bot(pr); st.session_state.messages.append({"role":"assistant","content":rep})
            with st.chat_message("assistant"): st.markdown(rep)
    st.markdown(f"<p style='text-align:center;color:{MUT};margin-top:35px'>ProcessLab • Génie des procédés</p>",unsafe_allow_html=True)

# ---------- ROUTAGE AVEC GESTION D'ERREUR ----------
try:
    if st.session_state.logged_in and st.session_state.page=="app": simulator()
    elif st.session_state.page=="auth": auth()
    else: landing()
except Exception as e:
    st.error(f"⚠️ Une erreur d'affichage est survenue : {e}")
    st.exception(e)
