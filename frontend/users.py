import streamlit as st
from utils import get_users


def users_page():
    """Affiche la liste des utilisateurs pour l'admin."""
    st.title("👥 Gestion des utilisateurs")

    if st.button("⬅️ Retour à l’accueil"):
        st.session_state["__page_override__"] = "🏠 Accueil"
        st.rerun()

    users = get_users(st.session_state["token"])

    if not users:
        st.warning("Aucun utilisateur trouvé.")
        return

    for user in users:
        with st.expander(user.get("name", "Utilisateur inconnu")):
            st.write(f"**Email** : {user.get('email', '-')}")
            st.write(f"**Rôle** : {user.get('role', '-')}")
            st.write(f"**Actif** : {'✅ Oui' if user.get('is_active') else '❌ Non'}")
