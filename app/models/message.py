from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text , Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import BaseModel

class Message(BaseModel):
    """Modèle pour les messages dans les conversations."""
    
    contenu = Column(Text, nullable=False)
    date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    lu = Column(Boolean, default=False)
    type_message = Column(String, default="texte")  # "texte", "fichier", "image"
    fichier_url = Column(String, nullable=True)
    
    # Clés étrangères
    emetteur_id = Column(Integer, ForeignKey("utilisateur.id"), nullable=False)
    destinataire_id = Column(Integer, ForeignKey("utilisateur.id"), nullable=False)  
    conversation_id = Column(Integer, ForeignKey("conversation.id"), nullable=False)


    # Relations
    emetteur = relationship("Utilisateur", foreign_keys=[emetteur_id], back_populates="messages_envoyes")
    destinataire = relationship("Utilisateur", foreign_keys=[destinataire_id], back_populates="messages_recus")
    conversation = relationship("Conversation", back_populates="messages")

    def mark_as_read(self):
        """Marquer le message comme lu."""
        self.lu = True
    
    def is_from_user(self, user_id):
        """Vérifier si le message provient d'un utilisateur spécifique."""
        return self.emetteur_id == user_id