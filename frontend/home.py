import streamlit as st


def home_page():
    """Affiche la page principale après connexion."""
    st.title("🏠 Bienvenue sur FastAPI Xtrem")
    st.write("🔹 Sélectionnez une section dans la barre latérale pour commencer.")

    if st.session_state["role"] == "admin":
        st.write("✅ Vous avez un accès administrateur.")
