from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.schemas.auth import TokenData
from app.models.utilisateur import Utilisateur
from typing import Optional

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> Utilisateur:
    """Obtenir l'utilisateur actuel à partir du token JWT."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Impossible de valider les informations d'identification",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    
    user = db.query(Utilisateur).filter(Utilisateur.email == token_data.email).first()
    if user is None:
        raise credentials_exception
    
    if not user.actif:
        raise HTTPException(status_code=400, detail="Utilisateur inactif")
    
    return user

def get_current_active_user(
    current_user: Utilisateur = Depends(get_current_user),
) -> Utilisateur:
    """Vérifier que l'utilisateur actuel est actif."""
    if not current_user.actif:
        raise HTTPException(status_code=400, detail="Utilisateur inactif")
    return current_user

def get_user_by_type(user_type: str):
    """Obtenir un utilisateur par type (recruteur, responsable_rh, stagiaire)."""
    def _get_user_by_type(current_user: Utilisateur = Depends(get_current_user)) -> Utilisateur:
        if current_user.type != user_type:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"L'utilisateur n'est pas un {user_type}",
            )
        return current_user
    return _get_user_by_type