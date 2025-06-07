# Créez: app/api/endpoints/upload.py
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from app.core.file_storage import save_photo_file, delete_photo  # Utilisez votre système existant
from app.api.deps import get_current_user
from app.models.utilisateur import Utilisateur
import os
import uuid
import time
from pathlib import Path

router = APIRouter()

@router.post("/photo")
async def upload_photo(file: UploadFile = File(...)):
    """Upload d'une photo de profil - PAS d'authentification requise pour l'inscription."""
    
    print(f"=== UPLOAD PHOTO (NO AUTH) ===")
    print(f"Fichier reçu: {file.filename}")
    print(f"Taille: {file.size} bytes")
    print(f"Type: {file.content_type}")
    
    try:
        # Vérifications
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="Le fichier doit être une image")
        
        if file.size > 5 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="Fichier trop volumineux (max 5MB)")
        
        # Créer le dossier
        photos_dir = Path("uploads/photos")
        photos_dir.mkdir(parents=True, exist_ok=True)
        
        # Nom unique
        timestamp = int(time.time())
        extension = Path(file.filename).suffix.lower() or '.jpg'
        unique_filename = f"{timestamp}_{uuid.uuid4().hex[:8]}{extension}"
        
        # Sauvegarder
        file_path = photos_dir / unique_filename
        content = await file.read()
        
        with open(file_path, "wb") as buffer:
            buffer.write(content)
        
        result_filename = f"photos/{unique_filename}"
        
        print(f"✅ Photo sauvegardée: {result_filename}")
        print(f"📁 Chemin complet: {file_path.absolute()}")
        
        return {
            "filename": result_filename,
            "url": f"/uploads/{result_filename}",
            "message": "Photo uploadée avec succès"
        }
        
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint pour upload avec authentification (pour utilisateurs connectés)
@router.post("/photo-auth")
async def upload_photo_authenticated(
    file: UploadFile = File(...),
    current_user: Utilisateur = Depends(get_current_user)
):
    """Upload d'une photo de profil - Authentification requise."""
    
    print(f"=== UPLOAD PHOTO (WITH AUTH) ===")
    print(f"Utilisateur: {current_user.email}")
    print(f"Fichier reçu: {file.filename}")
    
    # Même logique que l'endpoint sans auth
    try:
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="Le fichier doit être une image")
        
        if file.size > 5 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="Fichier trop volumineux (max 5MB)")
        
        photos_dir = Path("uploads/photos")
        photos_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = int(time.time())
        extension = Path(file.filename).suffix.lower() or '.jpg'
        unique_filename = f"{timestamp}_{uuid.uuid4().hex[:8]}{extension}"
        
        file_path = photos_dir / unique_filename
        content = await file.read()
        
        with open(file_path, "wb") as buffer:
            buffer.write(content)
        
        result_filename = f"photos/{unique_filename}"
        
        print(f"✅ Photo sauvegardée: {result_filename}")
        
        return {
            "filename": result_filename,
            "url": f"/uploads/{result_filename}",
            "message": "Photo uploadée avec succès"
        }
        
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/photo/{photo_filename}")
async def delete_photo_endpoint(
    photo_filename: str,
    current_user: Utilisateur = Depends(get_current_user)
):
    """Supprimer une photo."""
    
    try:
        success = delete_photo(photo_filename)
        if success:
            return {"message": "Photo supprimée avec succès"}
        else:
            raise HTTPException(
                status_code=404,
                detail="Photo non trouvée"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la suppression: {str(e)}"
        )