# import os
# import uuid
# from pathlib import Path
# from fastapi import UploadFile
# from app.core.config import settings


# # Configuration des dossiers de stockage
# UPLOAD_DIR = Path("uploads")
# CV_DIR = UPLOAD_DIR / "cv"
# LETTRES_DIR = UPLOAD_DIR / "lettres"

# # Créer les dossiers s'ils n'existent pas
# CV_DIR.mkdir(parents=True, exist_ok=True)
# LETTRES_DIR.mkdir(parents=True, exist_ok=True)


# # Extensions de fichiers autorisées
# ALLOWED_CV_EXTENSIONS = {".pdf", ".doc", ".docx"}
# ALLOWED_LETTER_EXTENSIONS = {".pdf", ".doc", ".docx", ".txt"}

# def generate_unique_filename(original_filename: str) -> str:
#     """Générer un nom de fichier unique."""
#     file_extension = Path(original_filename).suffix.lower()
#     unique_id = str(uuid.uuid4())
#     return f"{unique_id}{file_extension}"

# def is_allowed_file(filename: str, allowed_extensions: set) -> bool:
#     """Vérifier si l'extension du fichier est autorisée."""
#     return Path(filename).suffix.lower() in allowed_extensions

# async def save_cv_file(file: UploadFile) -> str:
#     """Sauvegarder le fichier CV et retourner le chemin."""
#     if not is_allowed_file(file.filename, ALLOWED_CV_EXTENSIONS):
#         raise ValueError(f"Extension de fichier non autorisée pour le CV: {Path(file.filename).suffix}")
    
#     filename = generate_unique_filename(file.filename)
#     file_path = CV_DIR / filename
    
#     with open(file_path, "wb") as buffer:
#         content = await file.read()
#         buffer.write(content)
    
#     return str(file_path)

# async def save_letter_file(file: UploadFile) -> str:
#     """Sauvegarder le fichier lettre de motivation et retourner le chemin."""
#     if not is_allowed_file(file.filename, ALLOWED_LETTER_EXTENSIONS):
#         raise ValueError(f"Extension de fichier non autorisée pour la lettre: {Path(file.filename).suffix}")
    
#     filename = generate_unique_filename(file.filename)
#     file_path = LETTRES_DIR / filename
    
#     with open(file_path, "wb") as buffer:
#         content = await file.read()
#         buffer.write(content)
    
#     return str(file_path)

# def delete_file(file_path: str) -> bool:
#     """Supprimer un fichier du système de fichiers."""
#     try:
#         if os.path.exists(file_path):
#             os.remove(file_path)
#             return True
#         return False
#     except Exception as e:
#         print(f"Erreur lors de la suppression du fichier {file_path}: {e}")
#         return False

import os
import uuid
from pathlib import Path
from fastapi import UploadFile
from app.core.config import settings

# Configuration des dossiers de stockage
UPLOAD_DIR = Path("uploads")
CV_DIR = UPLOAD_DIR / "cv"
LETTRES_DIR = UPLOAD_DIR / "lettres"
PHOTOS_DIR = UPLOAD_DIR / "photos"  # ← NOUVEAU: Dossier pour les photos

# Créer les dossiers s'ils n'existent pas
CV_DIR.mkdir(parents=True, exist_ok=True)
LETTRES_DIR.mkdir(parents=True, exist_ok=True)
PHOTOS_DIR.mkdir(parents=True, exist_ok=True)  # ← NOUVEAU

# Extensions de fichiers autorisées
ALLOWED_CV_EXTENSIONS = {".pdf", ".doc", ".docx"}
ALLOWED_LETTER_EXTENSIONS = {".pdf", ".doc", ".docx", ".txt"}
ALLOWED_PHOTO_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}  # ← NOUVEAU

def generate_unique_filename(original_filename: str) -> str:
    """Générer un nom de fichier unique."""
    file_extension = Path(original_filename).suffix.lower()
    unique_id = str(uuid.uuid4())
    return f"{unique_id}{file_extension}"

def is_allowed_file(filename: str, allowed_extensions: set) -> bool:
    """Vérifier si l'extension du fichier est autorisée."""
    return Path(filename).suffix.lower() in allowed_extensions

async def save_cv_file(file: UploadFile) -> str:
    """Sauvegarder le fichier CV et retourner le chemin."""
    if not is_allowed_file(file.filename, ALLOWED_CV_EXTENSIONS):
        raise ValueError(f"Extension de fichier non autorisée pour le CV: {Path(file.filename).suffix}")
        
    filename = generate_unique_filename(file.filename)
    file_path = CV_DIR / filename
        
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
        
    return str(file_path)

async def save_letter_file(file: UploadFile) -> str:
    """Sauvegarder le fichier lettre de motivation et retourner le chemin."""
    if not is_allowed_file(file.filename, ALLOWED_LETTER_EXTENSIONS):
        raise ValueError(f"Extension de fichier non autorisée pour la lettre: {Path(file.filename).suffix}")
        
    filename = generate_unique_filename(file.filename)
    file_path = LETTRES_DIR / filename
        
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
        
    return str(file_path)

# ← NOUVELLE FONCTION pour les photos
async def save_photo_file(file: UploadFile) -> str:
    """Sauvegarder le fichier photo et retourner le nom du fichier."""
    if not is_allowed_file(file.filename, ALLOWED_PHOTO_EXTENSIONS):
        raise ValueError(f"Extension de fichier non autorisée pour la photo: {Path(file.filename).suffix}")
    
    # Vérifier la taille (max 5MB)
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise ValueError("La photo ne doit pas dépasser 5MB")
    
    filename = generate_unique_filename(file.filename)
    file_path = PHOTOS_DIR / filename
    
    with open(file_path, "wb") as buffer:
        buffer.write(content)
    
    # Retourner seulement le nom du fichier (pas le chemin complet)
    # car FastAPI sert les images depuis /uploads/photos/
    return f"photos/{filename}"

def delete_file(file_path: str) -> bool:
    """Supprimer un fichier du système de fichiers."""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False
    except Exception as e:
        print(f"Erreur lors de la suppression du fichier {file_path}: {e}")
        return False

def delete_photo(photo_filename: str) -> bool:
    """Supprimer une photo de profil."""
    if not photo_filename:
        return True
    
    # Construire le chemin complet
    if photo_filename.startswith("photos/"):
        file_path = UPLOAD_DIR / photo_filename
    else:
        file_path = PHOTOS_DIR / photo_filename
    
    return delete_file(str(file_path))