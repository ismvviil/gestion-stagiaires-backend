from app.core.database import engine
from app.models import BaseModel
import logging

def init_db():
    try:
        BaseModel.metadata.create_all(bind=engine)
        logging.info("Base de données initialisée avec succès")
    except Exception as e:
        logging.error(f"Erreur lors de l'initialisation de la base de données: {e}")
        raise