from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from modules.api.users.routes import users_router
from modules.api.users.create_db import init_users_db

# Initialisation de la base de données utilisateurs
init_users_db()

app = FastAPI(
    title="SecureAPI",
    description="Cours Simplon: Fast API Sécurité",
    version="1.0.0",
)

# Ajout du middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Port par défaut pour VueJs
        "http://localhost:8501",  # Port par défaut pour Streamlit
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Autoriser toutes les méthodes (GET, POST, etc.)
    allow_headers=["*"],  # Autoriser tous les headers
)

router = APIRouter()

# Ajout de la route /hello pour vérifier que l'API fonctionne
@router.get("/hello", tags=["Hello API"])
def hello():
    return {"message": "Hello, FastAPI!"}

# Inclusion des routes existantes (ici, les routes liées aux utilisateurs)
router.include_router(users_router)

# Inclusion du router dans l'application principale
app.include_router(router)

# Redirection vers la documentation interactive de FastAPI
@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")
