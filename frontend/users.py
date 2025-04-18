import streamlit as st
from utils import get_users


def users_page():
    """Affiche la liste des utilisateurs pour l'admin."""
    st.title("👥 Gestion des utilisateurs")

    users = get_users(st.session_state["token"])

    if not users:
        st.warning("Aucun utilisateur trouvé.")
        return

    for user in users:
        with st.expander(user.get("name", "Utilisateur inconnu")):
            st.write(f"**Email** : {user.get('email', '-')}")
            st.write(f"**Rôle** : {user.get('role', '-')}")
            st.write(f"**Actif** : {'✅ Oui' if user.get('is_active') else '❌ Non'}")

            col1, col2 = st.columns(2)

            with col1:
                if st.button(f"✏️ Modifier {user['email']}"):
                    st.session_state["edit_user"] = user
                    st.session_state["__page_override__"] = "✏️ Modifier utilisateur"
                    st.rerun()

            with col2:
                with st.form(f"form_delete_{user['id']}"):
                    submitted = st.form_submit_button("🗑️ Supprimer")
                    if submitted:
                        st.session_state["delete_user_id"] = user["id"]
                        st.session_state["__page_override__"] = "❌ Supprimer utilisateur"
                        st.rerun()