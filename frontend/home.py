
import streamlit as st
import datetime
from utils import get_user_count


def home_page():
    """Affiche la page principale après connexion."""
    st.title("🏠 Bienvenue sur FastAPI Xtrem")

    # Message personnalisé
    user = st.session_state.get("user", "utilisateur")
    st.write(f"👋 Bonjour, **{user}** ! Ravi de vous retrouver.")

    # Image illustrative
    st.image("./assets/logo.png", width=400)

    st.write("🔹 Sélectionnez une section dans la barre latérale pour commencer.")

    if st.session_state["role"] == "admin":
        st.markdown("---")
        st.subheader(" Espace Administrateur")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("👥 Voir tous les utilisateurs"):
                st.session_state["__page_override__"] = "👥 Utilisateurs"
                st.rerun()

        with col2:
            st.markdown("#### 📊 Statistiques (live)")

            # Nombre d'utilisateurs depuis l'API
            user_count = get_user_count(st.session_state["token"])

            # À compléter plus tard avec un vrai appel backend pour les tokens
            token_count = 18  # ou 0 par défaut en attendant

            st.metric("Utilisateurs inscrits", user_count)
            st.metric("Tokens actifs", token_count)
            st.metric("Dernière connexion", datetime.datetime.now().strftime("%d/%m/%Y à %H:%M"))

            st.caption("Le nombre d'utilisateurs est à jour, les autres stats arrivent !")