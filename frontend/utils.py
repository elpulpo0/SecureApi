import requests
import streamlit as st
from dotenv import load_dotenv
import os

from pathlib import Path
env_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=env_path)

# DEBUG 🔍
print("✅ Chargement de .env depuis :", env_path)
print("✅ Fichier .env existe ? :", env_path.exists())
print("✅ BACKEND_URL =", os.getenv("BACKEND_URL"))

BACKEND_URL = os.getenv("BACKEND_URL") or "http://localhost:8000"


def authenticate_user(email, password):
    response = requests.post(f"{BACKEND_URL}/auth/login", data={"username": email, "password": password})
    if response.status_code == 200:
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        user_response = requests.get(f"{BACKEND_URL}/auth/users/me", headers=headers)
        if user_response.status_code == 200:
            user_data = user_response.json()
            return {"role": user_data["role"], "token": token}
    return None


def create_user(name, email, password):
    response = requests.post(f"{BACKEND_URL}/auth/users/", json={"name": name, "email": email, "password": password})
    if response.status_code == 201:
        return True, "Compte créé"
    elif response.status_code == 400:
        return False, response.json().get("detail", "Erreur 400")
    return False, "Erreur inconnue"


def get_users(token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BACKEND_URL}/auth/users/", headers=headers)
    return response.json() if response.status_code == 200 else []


def delete_user(user_id, token):
    headers = {"Authorization": f"Bearer {token}"}
    return requests.delete(f"{BACKEND_URL}/auth/users/{user_id}", headers=headers)


def update_user(user_id, name, role, is_active, token):
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "name": name,
        "role": role,
        "is_active": is_active
    }
    return requests.put(f"{BACKEND_URL}/auth/users/{user_id}", json=data, headers=headers)


def get_user_count(token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BACKEND_URL}/auth/users/", headers=headers)
    if response.status_code == 200:
        return len(response.json())
    return 0


def logout():
    st.session_state.clear()
    st.success("Déconnexion réussie !")
    st.rerun()