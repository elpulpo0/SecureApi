from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from modules.api.users.routes import users_router

from modules.api.users.create_db import init_users_db


init_users_db()

app = FastAPI(
    title="SecureAPI",
    description="Cours Simplon: Fast API Sécurité",
    version="1.0.0",
)

# Ajouter le middleware CORS
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

router.include_router(users_router)

app.include_router(router)


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")
