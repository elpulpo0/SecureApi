import streamlit as st
from login import login_page
from home import home_page
from users import users_page
from edit_user import edit_user_page
from delete_user import delete_user_page
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
    # 🔹 Déconnexion
    if st.sidebar.button("🚪 Se déconnecter", key="logout"):
        logout()

    # 🔹 Déclaration des pages disponibles
    PAGES = {
        "🏠 Accueil": home_page,
    }

    if st.session_state["role"] == "admin":
        PAGES.update({
            "👥 Utilisateurs": users_page,
            "✏️ Modifier utilisateur": edit_user_page,
            "❌ Supprimer utilisateur": delete_user_page,
        })

    # 🔹 Navigation
    selection = st.sidebar.radio("📍 Navigation", list(PAGES.keys()))

    # 🔁 Redirection prioritaire
    if "__page_override__" in st.session_state:
        selection = st.session_state["__page_override__"]
        print("🔁 Redirection forcée vers :", selection)  # DEBUG ICI ✅
        del st.session_state["__page_override__"]

    # 🔹 Affichage de la page
    PAGES[selection]()
    st.write("🔍 Page en cours :", selection)