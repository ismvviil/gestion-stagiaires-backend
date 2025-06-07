from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import sys

# Ajouter le chemin racine au PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import de votre application
try:
    from app.main import app
except ImportError:
    # Fallback si l'import échoue
    app = FastAPI(title="API Gestion Stagiaires")
    
    @app.get("/")
    def read_root():
        return {"message": "API de gestion des stagiaires", "status": "running"}
    
    @app.get("/health")
    def health_check():
        return {"status": "healthy"}

# Configuration CORS pour Vercel
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En production, spécifiez vos domaines
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Export pour Vercel
handler = app