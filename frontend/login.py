import streamlit as st
from utils import authenticate_user, create_user


def login_page():
    st.title("Bienvenue sur FastAPI Xtrem")
    tab1, tab2 = st.tabs(["Connexion", "Créer un compte"])

    with tab1:
        st.subheader("Connexion")
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Mot de passe", type="password", key="login_password")
        if st.button("Se connecter"):
            user = authenticate_user(email, password)
            if user:
                st.session_state["authenticated"] = True
                st.session_state["role"] = user["role"]
                st.session_state["token"] = user["token"]
                st.session_state["user"] = user.get("name", email)
                st.rerun()
            else:
                st.error("Identifiants incorrects")

    with tab2:
        st.subheader("Créer un compte")
        name = st.text_input("Nom ou Pseudo", key="signup_name")
        signup_email = st.text_input("Email", key="signup_email")
        signup_password = st.text_input("Mot de passe", type="password", key="signup_password")
        confirm_password = st.text_input("Confirmer le mot de passe", type="password", key="confirm_password")
        if st.button("S'inscrire"):
            if signup_password != confirm_password:
                st.error("❌ Les mots de passe ne correspondent pas.")
            else:
                success, message = create_user(name, signup_email, signup_password)
                if success:
                    st.success("✅ Compte créé avec succès ! Vous pouvez maintenant vous connecter.")
                else:
                    st.error(f"❌ Erreur : {message}")