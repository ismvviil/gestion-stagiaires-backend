from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, Table, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import BaseModel
from app.core.database import Base


class Conversation(BaseModel):
    """Modèle pour les conversations entre utilisateurs."""
    
    est_active = Column(Boolean, default=True)

    # Clés étrangères pour les deux participants
    participant1_id = Column(Integer, ForeignKey("utilisateur.id"), nullable=False)
    participant2_id = Column(Integer, ForeignKey("utilisateur.id"), nullable=False)
    
     # Relations
    participant1 = relationship("Utilisateur", foreign_keys=[participant1_id])
    participant2 = relationship("Utilisateur", foreign_keys=[participant2_id])
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

    def get_other_participant(self, current_user_id):
        """Récupérer l'autre participant dans la conversation."""
        if self.participant1_id == current_user_id:
            return self.participant2
        elif self.participant2_id == current_user_id:
            return self.participant1
        return None
    
    def get_last_message(self):
        """Récupérer le dernier message de la conversation."""
        if self.messages:
            return sorted(self.messages, key=lambda x: x.date, reverse=True)[0]
        return None
    
    def has_participant(self, user_id):
        """Vérifier si un utilisateur participe à cette conversation."""
        return user_id in [self.participant1_id, self.participant2_id]