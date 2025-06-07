from pydantic import BaseModel
from typing import Optional, List , TYPE_CHECKING
from datetime import datetime
from app.schemas.base import BaseSchema
from app.schemas.utilisateur import Utilisateur

from app.schemas.message import MessageResponse  # ⬅️ Import direct

class ConversationBase(BaseModel):
    est_active: bool = True

class ConversationCreate(BaseModel):
    participant_id: int  # L'autre participant (l'utilisateur actuel sera ajouté automatiquement)

class ConversationResponse(ConversationBase, BaseSchema):
    participant1_id: int
    participant2_id: int
    participant1: Optional[Utilisateur] = None
    participant2: Optional[Utilisateur] = None
    
    class Config:
        from_attributes = True


class ConversationWithLastMessage(ConversationResponse):
    dernier_message: Optional['MessageResponse'] = None
    messages_non_lus: int = 0
    autre_participant: Optional[Utilisateur] = None