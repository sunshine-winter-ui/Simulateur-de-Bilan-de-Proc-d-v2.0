import streamlit as st, sqlite3, bcrypt, re, pandas as pd, unicodedata
from io import BytesIO
from datetime import datetime

st.set_page_config(page_title="ProcessLab", layout="wide", page_icon="🧪", initial_sidebar_state="collapsed")

# ---------- ÉTAT ----------
DEFAULTS = {"theme_mode":"light","lang":"FR","page":"landing","logged_in":False,"messages":[],
    "params":{"m0":1000.0,"x0_sol":0.10,"residus":20.0,"mR":100.0,"xR":0.40,"T2":20.0,
              "T3":80.0,"cp":3.8,"x4":0.40,"lambda_v":2300.0}}
for k,v in DEFAULTS.items():
    st.session_state.setdefault(k, v.copy() if isinstance(v,dict) else v)

T = {
"FR":{"sub":"Filtration • Chauffage • Évaporation","theme":"☀️ Clair","lang":"🇬🇧 English",
  "login":"🔑 Se connecter","signup":"📝 Créer un compte","email":"📧 Email","pass":"🔒 Mot de passe",
  "confirm":"🔒 Confirmer","user":"👤 Nom d'utilisateur","login_b":"Se connecter →","signup_b":"Créer mon compte ✨",
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
  "cta":"🚀 Commencer","cta_l":"Déjà un compte ? Se connecter","f1":"⚡ Calculs rapides","f1_d":"Résultats instantanés.",
  "f2":"📊 Tableaux et graphiques","f2_d":"Suivez débits et puissances.","f3":"🤖 Assistant","f3_d":"Explications des calculs.",
  "f4":"📄 Rapport PDF","f4_d":"Export structuré.","how":"Comment ça marche ?","s1":"1. Créez un compte","s1_d":"Inscrivez-vous.",
  "s2":"2. Saisissez les paramètres","s2_d":"Débits, fractions, températures.","s3":"3. Consultez le rapport","s3_d":"Analysez et exportez.",
  "pdf":"📄 Télécharger le rapport PDF","back":"← Retour à l'accueil","proc":"Données d'entrée du procédé",
  "hyp":"Hypothèse : les résidus de filtration sont supposés exempts de soluté."},
"EN":{"sub":"Filtration • Heating • Evaporation","theme":"☀️ Light","lang":"🇫🇷 Français",
  "login":"🔑 Login","signup":"📝 Create account","email":"📧 Email","pass":"🔒 Password","confirm":"🔒 Confirm",
  "user":"👤 Username","login_b":"Login →","signup_b":"Create account ✨","hello":"Hello","logout":"🚪 Log out",
  "info":"Edit parameters and view results.","sim_t":"Material and energy balance simulator","sim_c":"Adjust parameters.",
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
  "cta":"🚀 Get started","cta_l":"Already have an account? Login","f1":"⚡ Fast calculations","f1_d":"Instant results.",
  "f2":"📊 Tables and charts","f2_d":"Track flows and power.","f3":"🤖 Assistant","f3_d":"Explanations of calculations.",
  "f4":"📄 PDF report","f4_d":"Structured export.","how":"How does it work?","s1":"1. Create account","s1_d":"Sign up.",
  "s2":"2. Enter parameters","s2_d":"Flows, fractions, temperatures.","s3":"3. View report","s3_d":"Analyze and export.",
  "pdf":"📄 Download PDF report","back":"← Back to home","proc":"Process input data",
  "hyp":"Assumption: filtration residues contain no solute."}}
def t(k): return T[st.session_state.lang].get(k,k)

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

# ---------- PALETTE THÉMÉE ----------
dk = st.session_state.theme_mode=="dark"
if dk:
    BG,CRD,TXT,MUT,INP,BRD=" #131A18","#1E2724","#F2F7F3","#A8B7B0","#26332E","#354540"
    ACC,ACC2,SOFT="#7FD9B8","#5FB89A","#26342E"
    SH="0 8px 28px rgba(0,0,0,.35)"; SYMO=".50"
    BGG=("radial-gradient(ellipse at 8% 12%,rgba(127,217,184,.20),transparent 32%),"
         "radial-gradient(ellipse at 92% 18%,rgba(181,165,240,.20),transparent 30%),"
         "radial-gradient(ellipse at 82% 88%,rgba(255,155,130,.15),transparent 32%),"
         "linear-gradient(135deg,#0F1614 0%,#131A18 48%,#1A1520 100%)")
    HBG="linear-gradient(118deg,rgba(32,41,39,.97) 0%,rgba(38,48,45,.96) 48%,rgba(42,36,54,.96) 100%)"
    FBG="linear-gradient(145deg,rgba(32,41,39,.98),rgba(30,40,36,.96))"; MBG="linear-gradient(145deg,#1E2724,#18201D)"
    CM,CL,CC,CG="#7FD9B8","#B5A5F0","#FF9B82","#F5C862"; HB="rgba(127,217,184,.22)"
    FSH="0 12px 30px rgba(0,0,0,.30)"; FSHH="0 17px 34px rgba(127,217,184,.22)"
else:
    BG,CRD,TXT,MUT,INP,BRD="#FAFAF7","#FFFFFF","#1E2D26","#6B7A72","#FFFFFF","#E4EAE5"
    ACC,ACC2,SOFT="#2F8B6F","#4FA383","#EAF4EE"
    SH="0 8px 28px rgba(39,65,50,.07)"; SYMO=".60"
    BGG=("radial-gradient(ellipse at 8% 12%,rgba(127,217,184,.32),transparent 32%),"
         "radial-gradient(ellipse at 92% 18%,rgba(181,165,240,.30),transparent 30%),"
         "radial-gradient(ellipse at 82% 88%,rgba(255,155,130,.24),transparent 32%),"
         "linear-gradient(135deg,#FBF9F4 0%,#EFF6F1 48%,#F4EFFB 100%)")
    HBG="linear-gradient(118deg,rgba(255,255,255,.98),rgba(245,250,247,.97) 48%,rgba(247,244,253,.97))"
    FBG="linear-gradient(145deg,rgba(255,255,255,.99),rgba(247,250,248,.97))"; MBG="linear-gradient(145deg,#FFFFFF,#F5F8F7)"
    CM,CL,CC,CG="#2F8B6F","#7B68B5","#D96B52","#B8860B"; HB="rgba(47,139,111,.22)"
    FSH="0 12px 30px rgba(55,82,69,.07)"; FSHH="0 17px 34px rgba(76,112,93,.14)"

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
.stButton>button,.stFormSubmitButton>button{{background:linear-gradient(110deg,{ACC},{ACC2} 58%,{CL})!important;color:#fff!important;border:0!important;border-radius:12px!important;padding:10px 18px;min-height:44px;font-weight:700;box-shadow:0 7px 18px rgba(83,139,116,.22)!important;transition:all .18s ease;}}
.stButton>button:hover,.stFormSubmitButton>button:hover{{background:linear-gradient(110deg,{ACC2},{ACC} 58%,{CL}cc)!important;box-shadow:0 10px 23px rgba(83,139,116,.32)!important;transform:translateY(-1px);}}
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
div[data-testid="stProgressBar"]>div>div{{background:{ACC}!important;border-radius:99px;}}
div[data-testid="stAlert"]{{border-radius:14px;}} #MainMenu{{visibility:hidden;}} footer{{visibility:hidden;}}
.floating-lab-art{{position:fixed;inset:0;overflow:hidden;pointer-events:none;z-index:0;}}
.lab-symbol{{position:absolute;display:block;user-select:none;font-weight:700;text-shadow:0 0 14px currentColor,0 6px 14px rgba(84,111,98,.18);filter:drop-shadow(0 5px 9px rgba(84,111,98,.15));animation:floatAround 14s ease-in-out infinite;will-change:transform;}}
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
@media(prefers-reduced-motion:reduce){{.lab-symbol,.lab-orb,.hero:before{{animation:none!important;}}}}
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
def logo(): return f'<div style="display:flex;align-items:center;gap:12px;padding:8px"><div style="width:46px;height:46px;border-radius:15px;background:{SOFT};display:grid;place-items:center;font-size:23px">⚗️</div><div style="line-height:1.12;text-align:left"><div style="font-family:Manrope,sans-serif;font-size:22px;font-weight:800;letter-spacing:-.7px;color:{TXT}">Process<span style="color:{ACC}">Lab</span></div><div style="font-size:10px;font-weight:700;letter-spacing:2.5px;color:{MUT};margin-top:4px">PROCESS LAB · INDUSTRIE</div></div></div>'

def toggle_lang(): st.session_state.lang="EN" if st.session_state.lang=="FR" else "FR"; st.rerun()
def toggle_theme(): st.session_state.theme_mode="light" if st.session_state.theme_mode=="dark" else "dark"; st.rerun()
def header_ctrl():
    c1,c2=st.columns(2)
    with c1:
        if st.button(t("lang"),use_container_width=True): toggle_lang()
    with c2:
        if st.button(t("theme"),use_container_width=True): toggle_theme()

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
def make_pdf(params, res, conc, user):
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from xml.sax.saxutils import escape
    buf=BytesIO(); doc=SimpleDocTemplate(buf,pagesize=A4,rightMargin=17*mm,leftMargin=17*mm,topMargin=25*mm,bottomMargin=18*mm)
    purple=colors.HexColor("#6941C6"); navy=colors.HexColor("#172554"); pale=colors.HexColor("#EEF2FF")
    grey=colors.HexColor("#64748B"); S=getSampleStyleSheet()
    S.add(ParagraphStyle(name="RT",parent=S["Title"],fontName="Helvetica-Bold",fontSize=19,leading=23,textColor=navy,alignment=TA_CENTER,spaceAfter=5))
    S.add(ParagraphStyle(name="ST",parent=S["Heading2"],fontName="Helvetica-Bold",fontSize=12,leading=15,textColor=purple,spaceBefore=12,spaceAfter=7))
    S.add(ParagraphStyle(name="SC",parent=S["BodyText"],fontName="Helvetica",fontSize=8.5,leading=11,textColor=navy))
    S.add(ParagraphStyle(name="SCH",parent=S["BodyText"],fontName="Helvetica-Bold",fontSize=8.5,leading=11,textColor=colors.white))
    S.add(ParagraphStyle(name="RB",parent=S["BodyText"],fontSize=9.5,leading=14,textColor=navy,spaceAfter=5))
    def cell(v,h=False): return Paragraph(escape(str(v)).replace("\n","<br/>"),S["SCH" if h else "SC"])
    def tbl(rows,w=None):
        data=[[cell(v,i==0) for v in row] for i,row in enumerate(rows)]
        tb=Table(data,colWidths=w,repeatRows=1,hAlign="LEFT")
        tb.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),purple),("TEXTCOLOR",(0,0),(-1,0),colors.white),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,pale]),("GRID",(0,0),(-1,-1),0.45,colors.HexColor("#D8DEEA")),
            ("VALIGN",(0,0),(-1,-1),"MIDDLE"),("LEFTPADDING",(0,0),(-1,-1),7),("RIGHTPADDING",(0,0),(-1,-1),7),
            ("TOPPADDING",(0,0),(-1,-1),6),("BOTTOMPADDING",(0,0),(-1,-1),6)]))
        return tb
    def deco(cv,d):
        cv.saveState(); w,h=A4
        cv.setFillColor(purple); cv.rect(0,h-13*mm,w,13*mm,fill=1,stroke=0)
        cv.setFillColor(colors.white); cv.setFont("Helvetica-Bold",9); cv.drawString(17*mm,h-8.5*mm,"SIMULATEUR PRO V2  |  RAPPORT DE PROCÉDÉ")
        cv.setStrokeColor(colors.HexColor("#D8DEEA")); cv.line(17*mm,13*mm,w-17*mm,13*mm)
        cv.setFillColor(grey); cv.setFont("Helvetica",7.5)
        cv.drawString(17*mm,8*mm,"Rapport généré automatiquement - Usage pédagogique")
        cv.drawRightString(w-17*mm,8*mm,f"Page {d.page}"); cv.restoreState()
    story=[Spacer(1,5*mm),Paragraph("RAPPORT DE SIMULATION",S["RT"]),
        Paragraph("Filtration • Mélange • Chauffage • Évaporation",S["RB"]),Spacer(1,3*mm),
        tbl([["Informations générales","Valeur"],["Utilisateur",user],["Date",datetime.now().strftime("%d/%m/%Y à %H:%M")],["Application","Simulateur Pro V2"]],[65*mm,105*mm]),
        Paragraph("1. Paramètres opératoires",S["ST"]),tbl([["Paramètre","Valeur"]]+[[k,v] for k,v in params.items()],[85*mm,85*mm]),
        Paragraph("2. Bilan matière",S["ST"]),tbl([["Grandeur","Résultat"]]+[[k,v] for k,v in res["matter"].items()],[85*mm,85*mm]),
        Paragraph("3. Bilan énergétique",S["ST"]),tbl([["Grandeur","Résultat"]]+[[k,v] for k,v in res["energy"].items()],[85*mm,85*mm]),
        Paragraph("4. Conclusions et recommandations",S["ST"])]
    for x in conc: story.append(Paragraph("• "+escape(str(x)),S["RB"]))
    story+=[Spacer(1,5*mm),Paragraph("<b>Note :</b> les résidus sont supposés exempts de soluté. Bilan calculé sur les mêmes relations de débit ; fermeture numérique ≠ validation expérimentale.",S["RB"])]
    doc.build(story,onFirstPage=deco,onLaterPages=deco); buf.seek(0); return buf.getvalue()

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
    header_ctrl(); st.markdown(logo(),unsafe_allow_html=True)
    st.markdown(f'<div class="hero"><span class="hero-badge">CHIMIE · GÉNIE DES PROCÉDÉS</span><h1 style="font-size:34px;margin:14px 0 8px">{t("l_t")}</h1><p>{t("l_s")}</p><div style="display:flex;flex-wrap:wrap;gap:8px;margin-top:22px;position:relative;z-index:1"><span class="hero-badge">01 · Filtration</span><span class="hero-badge">02 · Chauffage</span><span class="hero-badge">03 · Évaporation</span></div></div>',unsafe_allow_html=True)
    c1,c2=st.columns(2)
    with c1:
        if st.button(t("cta"),use_container_width=True): st.session_state.page="auth"; st.rerun()
    with c2:
        if st.button(t("cta_l"),use_container_width=True): st.session_state.page="auth"; st.rerun()
    st.write("")
    for col,(a,b) in zip(st.columns(4),[(t("f1"),t("f1_d")),(t("f2"),t("f2_d")),(t("f3"),t("f3_d")),(t("f4"),t("f4_d"))]):
        with col: st.markdown(f'<div class="feature"><h3>{a}</h3><p>{b}</p></div>',unsafe_allow_html=True)
    st.write(""); st.markdown(f"<h2 style='text-align:center'>{t('how')}</h2>",unsafe_allow_html=True)
    for col,(a,b) in zip(st.columns(3),[(t("s1"),t("s1_d")),(t("s2"),t("s2_d")),(t("s3"),t("s3_d"))]):
        with col: st.markdown(f'<div class="feature"><h3>{a}</h3><p>{b}</p></div>',unsafe_allow_html=True)
    st.markdown(f"<p style='text-align:center;color:{MUT};margin-top:35px'>Simulateur Pro V2 • Apprentissage du génie des procédés</p>",unsafe_allow_html=True)

def auth():
    if st.button(t("back")): st.session_state.page="landing"; st.rerun()
    _,mid,_=st.columns([1,1.6,1])
    with mid:
        st.markdown(logo(),unsafe_allow_html=True); header_ctrl()
        tl,ts=st.tabs([t("login"),t("signup")])
        with tl:
            with st.form("lf"):
                e=st.text_input(t("email"),placeholder="exemple@email.com")
                p=st.text_input(t("pass"),type="password")
                s=st.form_submit_button(t("login_b"),use_container_width=True)
            if s:
                if not e or not p: st.error(t("err_fill"))
                else:
                    u=auth_user(e.strip(),p)
                    if u: st.session_state.update(logged_in=True,username=u,page="app"); st.rerun()
                    else: st.error(t("err_auth"))
        with ts:
            with st.form("sf"):
                u=st.text_input(t("user"))
                e=st.text_input(t("email"),placeholder="exemple@email.com")
                p=st.text_input(t("pass"),type="password")
                c=st.text_input(t("confirm"),type="password")
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
        if st.button(t("lang"),use_container_width=True): toggle_lang()
        if st.button(t("theme"),use_container_width=True): toggle_theme()
        st.info(t("info"))
        if st.button(t("logout"),use_container_width=True):
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
        res_pdf={"matter":{"m₁":f"{r['m1']:.2f} kg/h","m₂":f"{r['m2']:.2f} kg/h","x₂":f"{r['x2']*100:.2f} %","m₄":f"{r['m4']:.2f} kg/h","mv":f"{r['mv']:.2f} kg/h","Entrées":f"{r['feed']:.2f} kg/h","Sorties":f"{r['output']:.2f} kg/h","Écart":f"{r['error']:.6f} kg/h"},"energy":{"Q₃":f"{r['Q3']:.2f} kW","Q₄":f"{r['Q4']:.2f} kW","Q₅":f"{r['Q5']:.2f} kW"}}
        st.download_button(t("pdf"),data=make_pdf(params_pdf,res_pdf,cs,st.session_state.get("username","User")),file_name="rapport.pdf",mime="application/pdf",use_container_width=True)
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
    st.markdown(f"<p style='text-align:center;color:{MUT};margin-top:35px'>Simulateur Pro V2 • Génie des procédés</p>",unsafe_allow_html=True)

# ---------- ROUTAGE ----------
if st.session_state.logged_in and st.session_state.page=="app": simulator()
elif st.session_state.page=="auth": auth()
else: landing()
