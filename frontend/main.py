import streamlit as st
from login import login_page
from home import home_page
from users import users_page
from utils import logout

# 🔹 Initialisation de la session
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
    st.session_state["role"] = None
    st.session_state["token"] = None

# 🔹 Gestion de la connexion
if not st.session_state["authenticated"]:
    login_page()
else:
    if st.sidebar.button("🚪 Se déconnecter", key="logout"):
        logout()

    PAGES = {
        "🏠 Accueil": home_page,
    }

    if st.session_state["role"] == "admin":
        PAGES["👥 Utilisateurs"] = users_page

    selection = st.sidebar.radio("📍 Navigation", list(PAGES.keys()))
    PAGES[selection]()


# 📁 frontend/home.py

def home_page():
    st.title("🏠 Bienvenue sur FastAPI Xtrem")
    st.write("🔹 Sélectionnez une section dans la barre latérale pour commencer.")
    if st.session_state["role"] == "admin":
        st.write("✅ Vous avez un accès administrateur.")