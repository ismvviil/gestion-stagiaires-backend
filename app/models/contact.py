# app/models/contact.py
from sqlalchemy import Column, String, Integer, Text, DateTime, Enum
from sqlalchemy.sql import func
import enum
from app.models.base import BaseModel

class StatusContact(enum.Enum):
    """Énumération des statuts pour les messages de contact."""
    NOUVEAU = "nouveau"        # Message non lu
    EN_COURS = "en_cours"      # Message en cours de traitement
    RESOLU = "resolu"          # Message résolu
    FERME = "ferme"            # Message fermé

class TypeMessage(enum.Enum):
    """Types de messages de contact."""
    QUESTION = "question"               # Question générale
    SUPPORT_TECHNIQUE = "support"       # Support technique
    DEMANDE_DEMO = "demo"              # Demande de démonstration
    PARTENARIAT = "partenariat"        # Proposition de partenariat
    AUTRE = "autre"                    # Autre type

class Contact(BaseModel):
    """Modèle pour les messages de contact."""
    
    # Informations de contact
    nom = Column(String(100), nullable=False)
    prenom = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False)
    telephone = Column(String(20), nullable=True)
    entreprise = Column(String(200), nullable=True)
    poste = Column(String(100), nullable=True)
    
    # Message
    type_message = Column(Enum(TypeMessage), default=TypeMessage.QUESTION)
    sujet = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    
    # Suivi
    status = Column(Enum(StatusContact), default=StatusContact.NOUVEAU)
    reponse = Column(Text, nullable=True)
    date_reponse = Column(DateTime(timezone=True), nullable=True)
    
    # Métadonnées
    ip_address = Column(String(45), nullable=True)  # Support IPv6
    user_agent = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<Contact {self.nom} {self.prenom} - {self.sujet}>"
    
    def marquer_resolu(self, reponse_text: str):
        """Marquer le message comme résolu avec une réponse."""
        self.status = StatusContact.RESOLU
        self.reponse = reponse_text
        self.date_reponse = func.now()
    
    def get_nom_complet(self):
        """Retourne le nom complet du contact."""
        return f"{self.prenom} {self.nom}"