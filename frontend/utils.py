# 📁 frontend/utils.py

import requests
import streamlit as st

API_URL = "http://backend:8000"

def authenticate_user(email, password):
    response = requests.post(f"{API_URL}/auth/login", data={"username": email, "password": password})
    if response.status_code == 200:
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        user_response = requests.get(f"{API_URL}/auth/users/me", headers=headers)
        if user_response.status_code == 200:
            user_data = user_response.json()
            return {"role": user_data["role"], "token": token}
    return None


def create_user(name, email, password):
    response = requests.post(f"{API_URL}/auth/users/", json={"name": name, "email": email, "password": password})
    if response.status_code == 201:
        return True, "Compte créé"
    elif response.status_code == 400:
        return False, response.json().get("detail", "Erreur 400")
    return False, "Erreur inconnue"


def get_users(token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_URL}/users/users/", headers=headers)
    return response.json() if response.status_code == 200 else []


def logout():
    st.session_state.clear()
    st.success("Déconnexion réussie !")
    st.rerun()