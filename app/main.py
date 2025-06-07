# from fastapi import FastAPI, WebSocket, Depends
# from fastapi.middleware.cors import CORSMiddleware
# from app.core.config import settings
# from app.api.endpoints.router import api_router
# from app.db import init_db
# import logging
# from sqlalchemy.orm import Session
# from app.core.database import get_db
# from app.websocket.endpoint import websocket_endpoint
# # Import all models to ensure they are registered with SQLAlchemy
# from app.models import (
#     BaseModel, Utilisateur, Role, ResponsableRH, 
#     Recruteur, Stagiaire, Entreprise, Message , Candidature , Conversation
# )
# from fastapi.staticfiles import StaticFiles

# # Dans votre main.py - Ajoutez du debug

# app = FastAPI(
#     title=settings.PROJECT_NAME,
#     openapi_url=f"{settings.API_V1_STR}/openapi.json",
#     # redirect_slashes=False
# )

# # DEBUG: Vérifiez ce qui est chargé
# print(f"DEBUG - PROJECT_NAME: {settings.PROJECT_NAME}")
# print(f"DEBUG - BACKEND_CORS_ORIGINS: {settings.BACKEND_CORS_ORIGINS}")
# print(f"DEBUG - Type de BACKEND_CORS_ORIGINS: {type(settings.BACKEND_CORS_ORIGINS)}")

# # Configuration CORS avec vérification
# try:
#     if settings.BACKEND_CORS_ORIGINS:
#         print("✅ Configuration CORS avec settings...")
#         app.add_middleware(
#             CORSMiddleware,
#             allow_origins=settings.BACKEND_CORS_ORIGINS,  # Pas besoin de str() si c'est déjà une liste
#             allow_credentials=True,
#             allow_methods=["*"],
#             allow_headers=["*"],
#         )
#         print(f"✅ CORS configuré pour: {settings.BACKEND_CORS_ORIGINS}")
#     else:
#         print("⚠️ BACKEND_CORS_ORIGINS est vide!")
# except Exception as e:
#     print(f"❌ Erreur CORS: {e}")
#     # Configuration CORS de secours
#     app.add_middleware(
#         CORSMiddleware,
#         allow_origins=["http://localhost:3000"],
#         allow_credentials=True,
#         allow_methods=["*"],
#         allow_headers=["*"],
#     )
#     print("🔧 CORS de secours activé")

# app.include_router(api_router, prefix=settings.API_V1_STR)

# # Route WebSocket
# @app.websocket("/ws")
# async def websocket_route(websocket: WebSocket, token: str, db: Session = Depends(get_db)):
#     await websocket_endpoint(websocket, token, db)
    
# @app.get("/")
# async def root():
#     return {"message": "Bienvenue sur l'API de gestion des stagiaires"}

# @app.on_event("startup")
# async def startup_event():
#     logging.basicConfig(level=logging.INFO)
#     logging.info("Initialisation de l'application...")
#     try:
#         init_db()
#         logging.info("Base de données initialisée avec succès")
#     except Exception as e:
#         logging.error(f"Erreur lors de l'initialisation de la base de données: {e}")

# app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


from fastapi import FastAPI, WebSocket, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.endpoints.router import api_router
from app.db import init_db
import logging
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.websocket.endpoint import websocket_endpoint
# Import all models to ensure they are registered with SQLAlchemy
from app.models import (
    BaseModel, Utilisateur, Role, ResponsableRH, 
    Recruteur, Stagiaire, Entreprise, Message , Candidature , Conversation
)
from fastapi.staticfiles import StaticFiles
import os

# 🚀 AJOUT POUR LA PRODUCTION RAILWAY
# Configuration spéciale pour Railway
if os.getenv("ENVIRONMENT") == "production":
    print("🌐 Mode production détecté!")
    # Railway peut parfois donner une URL postgres:// au lieu de postgresql://
    DATABASE_URL = os.getenv("DATABASE_URL")
    if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
        os.environ["DATABASE_URL"] = DATABASE_URL
        print(f"✅ URL de base de données corrigée pour Railway")
    
    # Configuration pour Railway qui utilise le PORT comme variable d'environnement
    PORT = int(os.getenv("PORT", 8000))
    print(f"🚀 Port configuré pour Railway: {PORT}")
else:
    print("🏠 Mode développement local")

# Dans votre main.py - Ajoutez du debug
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    # redirect_slashes=False
)

# DEBUG: Vérifiez ce qui est chargé
print(f"DEBUG - PROJECT_NAME: {settings.PROJECT_NAME}")
print(f"DEBUG - BACKEND_CORS_ORIGINS: {settings.BACKEND_CORS_ORIGINS}")
print(f"DEBUG - Type de BACKEND_CORS_ORIGINS: {type(settings.BACKEND_CORS_ORIGINS)}")
print(f"DEBUG - ENVIRONMENT: {os.getenv('ENVIRONMENT', 'development')}")

# Configuration CORS avec vérification
try:
    if settings.BACKEND_CORS_ORIGINS:
        print("✅ Configuration CORS avec settings...")
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.BACKEND_CORS_ORIGINS,  # Pas besoin de str() si c'est déjà une liste
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        print(f"✅ CORS configuré pour: {settings.BACKEND_CORS_ORIGINS}")
    else:
        print("⚠️ BACKEND_CORS_ORIGINS est vide!")
except Exception as e:
    print(f"❌ Erreur CORS: {e}")
    # Configuration CORS de secours
    cors_origins = ["http://localhost:3000"]
    
    # En production, ajouter des origines par défaut
    if os.getenv("ENVIRONMENT") == "production":
        cors_origins.extend([
            "https://*.vercel.app",
            "https://*.railway.app"
        ])
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    print(f"🔧 CORS de secours activé pour: {cors_origins}")

app.include_router(api_router, prefix=settings.API_V1_STR)

# Route WebSocket
@app.websocket("/ws")
async def websocket_route(websocket: WebSocket, token: str, db: Session = Depends(get_db)):
    await websocket_endpoint(websocket, token, db)
    
@app.get("/")
async def root():
    return {
        "message": "Bienvenue sur l'API de gestion des stagiaires",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """Route de vérification de santé pour Railway"""
    return {
        "status": "healthy",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "timestamp": "2024-01-01T00:00:00Z"
    }

@app.on_event("startup")
async def startup_event():
    logging.basicConfig(level=logging.INFO)
    logging.info("🚀 Initialisation de l'application...")
    logging.info(f"🌍 Environnement: {os.getenv('ENVIRONMENT', 'development')}")
    
    try:
        init_db()
        logging.info("✅ Base de données initialisée avec succès")
    except Exception as e:
        logging.error(f"❌ Erreur lors de l'initialisation de la base de données: {e}")
        # En production, on peut vouloir lever l'exception pour arrêter l'app
        if os.getenv("ENVIRONMENT") == "production":
            raise e

# Mount pour les fichiers statiques
try:
    app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
    print("✅ Dossier uploads monté")
except Exception as e:
    print(f"⚠️ Impossible de monter le dossier uploads: {e}")
    # En production Railway, créer le dossier s'il n'existe pas
    if os.getenv("ENVIRONMENT") == "production":
        os.makedirs("uploads", exist_ok=True)
        app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
        print("✅ Dossier uploads créé et monté pour Railway")

# 🚀 Pour Railway : Optionnel - handler pour démarrer avec uvicorn
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=port, 
        log_level="info",
        reload=os.getenv("ENVIRONMENT") != "production"
    )