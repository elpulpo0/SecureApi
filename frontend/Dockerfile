# Utiliser une image Python de base plus récente
FROM python:3.13-slim

# Définir le répertoire de travail dans le conteneur
WORKDIR /app

# Copier les fichiers requirements.txt et installer les dépendances
COPY requirements_frontend.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements_frontend.txt

# Copier le reste du code de l'application dans le conteneur
COPY . .

# Commande d'exécution pour lancer l'application
CMD ["streamlit", "run", "main.py"]