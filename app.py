import streamlit as st
import sqlite3
import bcrypt
import re

# --- 1. CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Simulateur Pro", layout="wide", page_icon="🧪")

# --- 2. STYLE CSS PERSONNALISÉ (Couleurs corrigées) ---
st.markdown("""
<style>
    /* Fond de l'application */
    .stApp {
        background-color: #f4f7f6;
    }
    /* Forcer la couleur du texte pour la lisibilité */
    html, body, [class*="css"] {
        color: #2c3e50; 
    }
    /* Style des cartes de résultats (Métriques) */
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        border-left: 5px solid #2980b9;
    }
    /* Couleur de la valeur dans les métriques */
    div[data-testid="stMetricValue"] {
        color: #2980b9 !important; 
    }
    /* Style des boutons */
    .stButton>button {
        background-color: #2980b9;
        color: white;
        border-radius: 8px;
        font-weight: bold;
        width: 100%;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #1c5980;
        color: white;
    }
    /* Cacher le menu Streamlit */
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

# --- 4. INTERFACE DE CONNEXION / INSCRIPTION ---
def auth_page():
    # Utilisation de colonnes pour centrer et ajouter une image
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.title("🔐 Portail Sécurisé")
        st.image("https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?auto=format&fit=crop&q=80&w=800", 
                 caption="Bienvenue sur le simulateur de procédés industriels")
        
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
                            # Connexion automatique après inscription
                            st.session_state['logged_in'] = True
                            st.session_state['username'] = new_username
                            st.success("Compte créé avec succès ! Redirection...")
                            st.rerun() # Force le rechargement pour passer au simulateur
                        else:
                            st.error("Erreur lors de la création.")

# --- 5. LOGIQUE DU CHATBOT ---
def generate_bot_response(user_input):
    user_input = user_input.lower()
    if "bonjour" in user_input or "salut" in user_input:
        return "Bonjour ! Je suis votre assistant. Posez-moi des questions sur la filtration, le chauffage ou l'évaporation."
    elif "aide" in user_input or "comment" in user_input:
        return "Modifiez les valeurs dans l'onglet 'Paramètres', puis allez dans 'Résultats' pour voir les calculs et les graphiques."
    elif "filtration" in user_input:
        return "La filtration retire les particules insolubles. Le débit final est m1 = m0 - résidus."
    elif "chauffage" in user_input:
        return "Le chauffage sert à augmenter la température. La puissance dépend de la capacité calorifique (Cp)."
    elif "évaporation" in user_input or "vapeur" in user_input:
        return "L'évaporation retire de l'eau. La puissance Q4 est calculée avec la chaleur latente (lambda_v)."
    elif "graphique" in user_input or "courbe" in user_input:
        return "Les graphiques dans l'onglet Résultats vous montrent l'évolution des débits et la répartition des puissances énergétiques."
    else:
        return "Je n'ai pas compris. Essayez de me demander 'Comment ça marche ?' ou des détails sur la 'filtration'."

# --- 6. SIMULATEUR + GRAPHIQUES + CHATBOT ---
def simulator_page():
    # En-tête avec le nom de l'utilisateur
    st.title("🧪 Simulateur de Bilan de Procédé")
    st.markdown(f"Bienvenue **{st.session_state.get('username', 'Utilisateur')}** ! Ajustez les paramètres pour voir les résultats évoluer.")
    
    tab_params, tab_results, tab_chat = st.tabs(["⚙️ Paramètres d'entrée", "📊 Résultats & Graphiques", "🤖 Assistant Virtuel"])
    
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
        
        st.info("💡 **Astuce** : Modifiez les valeurs ci-dessus, puis cliquez sur l'onglet '📊 Résultats & Graphiques' pour voir l'impact en temps réel.")

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
        T4, T5 = 80, 25 
        Q5 = m4 * cp * (T4 - T5) / 3600
        entrees = m0 + mR
        sorties = residus + mv + m4
        erreur = entrees - sorties

        # --- CARTES DE RÉSULTATS ---
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

        st.write("---")
        
        # --- GRAPHIQUES DYNAMIQUES ---
        st.subheader("📈 Visualisation Graphique")
        graph_col1, graph_col2 = st.columns(2)
        
        with graph_col1:
            st.write("**Évolution des débits (kg/h)**")
            # Graphique en barres des débits
            chart_data_debits = {
                "Étape": ["Initial (m0)", "Filtré (m1)", "Mélangé (m2)", "Final (m4)"],
                "Débit": [m0, m1, m2, m4]
            }
            st.bar_chart(chart_data_debits, x="Étape", y="Débit", color="#2980b9")
            
        with graph_col2:
            st.write("**Besoins énergétiques (kW)**")
            # Graphique en barres des puissances
            chart_data_puissance = {
                "Opération": ["Chauffage (Q3)", "Évaporation (Q4)", "Refroidissement (Q5)"],
                "Puissance": [Q3, Q4, Q5]
            }
            st.bar_chart(chart_data_puissance, x="Opération", y="Puissance", color="#e74c3c")

        # Barre de progression pour la concentration
        st.write("**Atteinte de l'objectif de concentration**")
        st.progress(min(x2 / x4 if x4 > 0 else 1.0, 1.0))
        st.caption(f"Objectif visé : {x4*100}% | Actuel : {x2*100:.2f}%")

    with tab_chat:
        st.subheader("🤖 Assistant Virtuel")
        
        if "messages" not in st.session_state:
            st.session_state.messages = [{"role": "assistant", "content": "Bonjour ! Une question sur les calculs ou les graphiques ?"}]
        
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        if prompt := st.chat_input("Posez votre question ici..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            response = generate_bot_response(prompt)
            st.session_state.messages.append({"role": "assistant", "content": response})
            with st.chat_message("assistant"):
                st.markdown(response)

# --- 7. LOGIQUE PRINCIPALE ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    auth_page()
else:
    if st.sidebar.button("🚪 Se déconnecter"):
        st.session_state['logged_in'] = False
        st.session_state['messages'] = [] 
        st.rerun()
    simulator_page()
