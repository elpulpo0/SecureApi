## Créer un environement virtuel

```python -m venv .venv```

## Activer l'environement virtuel (avec Bash)

```source .venv/Scripts/activate```

## Installer les dépendances

```pip install --upgrade pip```

```pip install -r requirements.txt```

### Si le fichier requirements n'est pas disponible:

```pip install fastapi uvicorn pydantic loguru bcrypt openpyxl python-jose python-dotenv SQLAlchemy python-multipart pydantic[email] pytest flake8, Streamlit, Requests```

```pip freeze > requirements.txt```

### Copier et éditer le fichier .env_example en .env

```sh
SECRET_KEY= # Clé pour hasher les mots de passe

ADMIN_EMAIL=
ADMIN_PASSWORD=
```

### Mettre à jour le template pour ajouter une base de donnée (Optionnel)

Dans `backend\modules\database\config.py`, `backend\modules\database\dependancies.py` et `backend\modules\database\session.py`, ajoutez la deuxième base de donnée pour correspondre au projet actuel, créez un dossier dédié à cette base de donnée en parralèle du dossier users et ensuite ajustez les imports correspondants dans `backend\modules\api\main.py`

## Lancer l'application

Ouvrez 2 terminaux:

Terminal 1 : ```cd backend && uvicorn modules.api.main:app --reload```
Terminal 2 : ```cd frontend && streamlit run main.py```
