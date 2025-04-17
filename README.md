# SecureAPI - Authentification Avancée avec FastAPI & Streamlit

**SecureAPI** est une application modulaire construite avec **FastAPI** pour le backend et **Streamlit** pour le frontend, intégrant un système complet d’authentification avec tokens JWT, stockage sécurisé des refresh tokens, gestion des rôles et des scopes, et une structure professionnelle pensée pour la scalabilité, les tests et la maintenabilité.

---

## Fonctionnalités principales

- Authentification sécurisée avec **bcrypt** & JWT
- **Rotation des refresh tokens** avec stockage en base
- Gestion des rôles & scopes pour autorisation fine (en cours)
- Swagger /docs auto-généré avec FastAPI
- Tests unitaires & intégration avec **pytest**
- Fixtures personnalisées pour tests avec BDD isolée
- Architecture modulaire par domaines fonctionnels
- Frontend léger avec **Streamlit**

---

## Arborescence du projet

```bash
SecureAPI/
├── backend/
│   ├── db/                    # Données / fichiers SQLite
│   ├── logs/                  # Logs applicatifs
│   ├── modules/               # Code métier organisé (auth, users, etc.)
│   ├── tests/                 # Tous les tests Pytest
│   ├── utils/                 # Utilitaires transverses
│   ├── Dockerfile             # Image Docker du backend
│   └── requirements_backend.txt
├── frontend/
│   ├── home.py / login.py     # Pages Streamlit
│   ├── main.py                # Entrée de l'app Streamlit
│   ├── Dockerfile             # Image Docker du frontend
│   └── requirements_frontend.txt
├── docker-compose.yml         # Orchestration backend + frontend
├── .env / .env_example        # Variables d’environnement
├── requirements.txt           # Toutes les dépendances
└── README.md                  # Ce fichier
```

## Démarrage rapide

1. Cloner le projet
```bash
git clone https://github.com/<votre-org>/SecureAPI.git
cd SecureAPI
```

2. Créer un environnement virtuel
```bash
python -m venv .venv
source .venv/bin/activate   # ou .venv/Scripts/activate sous Windows
```

3. Installer les dépendances
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Si le fichier requirements n'est pas disponible
```bash
pip install fastapi uvicorn pydantic loguru bcrypt openpyxl python-jose python-dotenv SQLAlchemy python-multipart pydantic[email] pytest flake8 httpx streamlit requests black
pip freeze > requirements.txt
```

4. Configurer l’environnement
Copier le fichier `.env_example` en `.env` et le remplir :
```env
SECRET_KEY= # Clé pour hasher les tokens
ADMIN_NAME=example
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=password123
PORT_BACK=8000
PORT_FRONT=8501
```

## Lancer l'application

- Terminal 1 :
```bash
cd backend && uvicorn modules.api.main:app --reload
```
- Terminal 2 :
```bash
cd frontend && streamlit run main.py
```

## Ajouter une base de donnée supplémentaire (optionnel)

Dans `backend/modules/database/config.py`, `dependancies.py` et `session.py`, ajoutez la deuxième base pour correspondre au projet actuel. Créez un dossier dédié en parallèle du dossier `users` puis ajustez les imports correspondants dans `backend/modules/api/main.py`.

## Lancer avec Docker (recommandé)
```bash
docker-compose up --build
```

- Backend FastAPI : http://localhost:8000/docs
- Frontend Streamlit : http://localhost:8501

## Lancer les tests
```bash
cd backend
pytest -v -s
```
> ⚠️ Les tests créent une base isolée temporaire avec rollback automatique, incluant un test de la rotation de refresh token.

## Mise à jour des dépendances
```bash
pip freeze > requirements.txt
```

## Logique métier (authentification)

- L'utilisateur se connecte via le frontend.
- Un access token (15 min) et un refresh token (7 jours) sont générés.
- Le refresh token est hashé et stocké en BDD.
- Lors du refresh :
  - On vérifie l’existence et la validité du refresh token en base.
  - On le révoque puis on en crée un nouveau.
  - On retourne un nouveau couple access + refresh.

## Guide de contribution

- Préférer les branches `feature/` et `fix/` pour travailler.
- Suivre la convention de nommage `snake_case` pour les fonctions.
- Tester chaque nouvelle fonctionnalité.
- Lint avec `flake8` et formater avec `black`.

## 🌟 Équipe

- Mathieu – Développeur Backend / IA
- Chris – Développeur Backend / IA
- Bouchaib – Développeur Frontend / IA

## Stack technique

| Outil        | Rôle                    |
|--------------|--------------------------|
| FastAPI      | API backend REST         |
| Streamlit    | Interface utilisateur    |
| SQLAlchemy   | ORM pour les modèles     |
| SQLite       | Base de données légère     |
| Pytest       | Framework de test        |
| Docker       | Conteneurisation         |
| JWT / bcrypt | Authentification sécurisée |

## 🛡️ Sécurité

- Mots de passe hashés en bcrypt
- Refresh tokens stockés hashés
- Rotation automatique
- JWT avec signature HMAC256
- Rôles / scopes à granularité fine

## Licence

Ce projet est sous licence MIT. Utilisation libre à des fins pédagogiques, professionnelles ou personnelles.