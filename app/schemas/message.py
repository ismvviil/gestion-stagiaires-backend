from pydantic import BaseModel
from typing import Optional , List
from datetime import datetime
from app.schemas.base import BaseSchema

class MessageBase(BaseModel):
    contenu: str
    type_message: str = "texte"

class MessageCreate(MessageBase):
    conversation_id: int

class MessageUpdate(BaseModel):
    lu: bool


class MessageResponse(MessageBase, BaseSchema):
    date: datetime
    lu: bool
    fichier_url: Optional[str] = None
    emetteur_id: int
    destinataire_id: int
    conversation_id: int
    
    # Informations de l'émetteur pour l'affichage
    emetteur_nom: Optional[str] = None
    emetteur_prenom: Optional[str] = None
    
    class Config:
        from_attributes = True

class ConversationMessages(BaseModel):
    conversation_id: int
    messages: List[MessageResponse]
    total: int