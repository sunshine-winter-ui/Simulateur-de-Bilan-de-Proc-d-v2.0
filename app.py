import streamlit as st
import sqlite3
import bcrypt
import re

# --- 1. CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Simulateur Pro", layout="wide")

# --- 2. STYLE CSS PERSONNALISÉ ---
st.markdown("""
<style>
    /* Style général de la page */
    .stApp {
        background-color: #f4f7f6;
    }
    /* Style des cartes de résultats (Métriques) */
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        border-left: 5px solid #1E88E5;
    }
    /* Style des boutons */
    .stButton>button {
        background-color: #1E88E5;
        color: white;
        border-radius: 8px;
        font-weight: bold;
    }
    /* Cacher le menu Streamlit en haut à droite */
    #MainMenu {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- 3. BASE DE DONNÉES ET SÉCURITÉ ---
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

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def email_exists(email):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = c.fetchone()
    conn.close()
    return user is not None

def create_user(username, email, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    hashed = hash_password(password)
    try:
        c.execute("INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)", (username, email, hashed))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def authenticate_user(email, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT username, password_hash FROM users WHERE email = ?", (email,))
    result = c.fetchone()
    conn.close()
    if result and verify_password(password, result[1]):
        return result[0]
    return None

# --- 4. INTERFACE DE CONNEXION / INSCRIPTION (Méthode 3) ---
def auth_page():
    st.title("🔐 Portail Sécurisé")
    st.write("Veuillez vous connecter pour accéder au simulateur.")
    
    # Onglets pour séparer Connexion et Inscription
    tab1, tab2 = st.tabs(["🔑 Se connecter", "📝 Créer un compte"])
    
    with tab1:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Mot de passe", type="password")
            submitted = st.form_submit_button("Se connecter")
            if submitted:
                if not email or not password:
                    st.error("Veuillez remplir tous les champs.")
                else:
                    user = authenticate_user(email, password)
                    if user:
                        st.session_state['logged_in'] = True
                        st.session_state['username'] = user
                        st.rerun()
                    else:
                        st.error("Email ou mot de passe incorrect.")
                        
    with tab2:
        with st.form("signup_form"):
            new_username = st.text_input("Nom d'utilisateur")
            new_email = st.text_input("Email")
            new_password = st.text_input("Mot de passe (min. 8 carac.)", type="password")
            confirm_password = st.text_input("Confirmer le mot de passe", type="password")
            submitted = st.form_submit_button("S'inscrire")
            if submitted:
                if not new_username or not new_email or not new_password:
                    st.error("Tous les champs sont obligatoires.")
                elif not re.match(r"[^@]+@[^@]+\.[^@]+", new_email):
                    st.error("Format d'email invalide.")
                elif new_password != confirm_password:
                    st.error("Les mots de passe ne correspondent pas.")
                elif len(new_password) < 8:
                    st.error("Le mot de passe doit contenir au moins 8 caractères.")
                elif email_exists(new_email):
                    st.warning("Cet email est déjà utilisé.")
                else:
                    if create_user(new_username, new_email, new_password):
                        st.success("Compte créé ! Connectez-vous dans l'onglet de gauche.")
                    else:
                        st.error("Erreur lors de la création.")

# --- 5. SIMULATEUR (Votre code d'origine + Méthode 3) ---
def simulator_page():
    st.title("🧪 Simulateur de Bilan de Procédé")
    st.markdown(f"Connecté en tant que : **{st.session_state.get('username', 'Utilisateur')}**")
    
    # Onglets pour séparer les paramètres et les résultats
    tab_params, tab_results = st.tabs(["⚙️ Paramètres d'entrée", "📊 Résultats du Bilan"])
    
    with tab_params:
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

    with tab_results:
        st.subheader("Résultats en temps réel")
        
        # --- CALCULS ---
        m1 = m0 - residus
        x1 = (m0 * x0_sol) / m1 if m1 > 0 else 0
        m2 = m1 + mR
        x2 = (m1 * x1 + mR * xR) / m2 if m2 > 0 else 0
        Q3 = m2 * cp * (T3 - T2) / 3600
        m4 = m2 * x2 / x4 if x4 > 0 else 0
        mv = m2 - m4
        Q4 = mv * lambda_v / 3600
        T4, T5 = 80, 25 # Valeurs fixes pour le refroidissement
        Q5 = m4 * cp * (T4 - T5) / 3600
        entrees = m0 + mR
        sorties = residus + mv + m4
        erreur = entrees - sorties

        # --- AFFICHAGE (Avec le design CSS appliqué) ---
        r1, r2, r3 = st.columns(3)
        r1.metric("Débit après filtration", f"{m1:,.2f} kg/h")
        r2.metric("Concentration mélange", f"{x2 * 100:.2f} %")
        r3.metric("Débit concentré final", f"{m4:,.2f} kg/h")
        
        st.write("---")
        
        r4, r5, r6 = st.columns(3)
        r4.metric("Eau évaporée", f"{mv:,.2f} kg/h")
        r5.metric("Puissance de chauffage", f"{Q3:,.2f} kW")
        r6.metric("Puissance d'évaporation", f"{Q4:,.2f} kW")
        
        st.write("---")
        
        r7, r8 = st.columns(2)
        r7.metric("Puissance de refroidissement", f"{Q5:,.2f} kW")
        r8.metric("Erreur bilan global", f"{erreur:,.2f} kg/h", delta=f"{erreur:,.2f}", delta_color="inverse")

        with st.expander("Voir le détail des calculs"):
            st.write(f"**Fraction de soluble après filtration (x1) :** {x1:.4f}")
            st.write(f"**Bilan total après mélange :** {m2:,.2f} kg/h")

# --- 6. LOGIQUE PRINCIPALE ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    auth_page()
else:
    if st.sidebar.button("🚪 Se déconnecter"):
        st.session_state['logged_in'] = False
        st.rerun()
    simulator_page()
