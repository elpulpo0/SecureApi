import streamlit as st
from utils import get_users


def users_page():
    """Affiche la liste des utilisateurs si admin."""
    st.title("Gestion des utilisateurs 👥")

    users = get_users(st.session_state["token"])

    if not users:
        st.warning("Aucun utilisateur trouvé.")
        return

    for user in users:
        with st.expander(user.get("full_name", "Utilisateur inconnu")):
            st.write(f"**Email** : {user.get('email', '-')}")
            st.write(f"**Rôle** : {user.get('role', '-')}")