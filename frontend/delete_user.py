import streamlit as st
from utils import delete_user


def delete_user_page():
    user_id = st.session_state.get("delete_user_id", None)
    st.write(f"🔍 ID récupéré depuis session : {user_id}")  # debug
    if not user_id:
        st.warning("Aucun utilisateur à supprimer.")
        return

    st.title("🗑️ Supprimer un utilisateur")

    if st.button("❌ Confirmer la suppression"):
        delete_user(user_id, st.session_state["token"])
        st.success("Utilisateur supprimé.")
        del st.session_state["delete_user_id"]
        st.session_state["__page_override__"] = "👥 Utilisateurs"
        st.rerun()

    if st.button("↩️ Annuler"):
        del st.session_state["delete_user_id"]
        st.session_state["__page_override__"] = "👥 Utilisateurs"
        st.rerun()