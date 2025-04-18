import streamlit as st
from utils import update_user


def edit_user_page():
    user = st.session_state.get("edit_user", None)
    if not user:
        st.warning("Aucun utilisateur sélectionné.")
        return

    st.title("✏️ Modifier un utilisateur")

    name = st.text_input("Nom", value=user["name"])
    role = st.selectbox("Rôle", ["admin", "reader"], index=0 if user["role"] == "admin" else 1)
    is_active = st.checkbox("Actif", value=user["is_active"])

    if st.button("✅ Enregistrer les modifications"):
        update_user(user["id"], name, role, is_active, st.session_state["token"])
        st.success("Utilisateur mis à jour avec succès.")
        del st.session_state["edit_user"]
        st.rerun()