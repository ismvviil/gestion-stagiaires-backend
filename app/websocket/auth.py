from fastapi import HTTPException, status
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.models.utilisateur import Utilisateur

async def get_user_from_token(token: str, db: Session) -> Utilisateur:
    """Authentifier un utilisateur à partir d'un token JWT."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token invalide",
    )
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(Utilisateur).filter(Utilisateur.email == email).first()
    if user is None or not user.actif:
        raise credentials_exception
    
    return user