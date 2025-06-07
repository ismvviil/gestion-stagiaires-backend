from sqlalchemy import Boolean, Column, String, Integer, ForeignKey, Table
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
from app.core.database import Base

# Table d'association entre Utilisateur et Role
utilisateur_role = Table('utilisateur_role', Base.metadata,
    Column('utilisateur_id', Integer, ForeignKey('utilisateur.id')),
    Column('role_id', Integer, ForeignKey('role.id'))
)

class Utilisateur(BaseModel):
    email = Column(String, unique=True, index=True, nullable=False)
    mot_de_passe = Column(String, nullable=False)
    nom = Column(String, nullable=False)
    prenom = Column(String, nullable=False)
    actif = Column(Boolean, default=True)
    
    # Type d'utilisateur (discriminator)
    type = Column(String(50))
    
    # Relation avec les rôles
    roles = relationship("Role", secondary=utilisateur_role, back_populates="utilisateurs")
    
    # Relations pour les conversations (en tant que participant1)
    conversations_as_participant1 = relationship(
    "Conversation", 
    foreign_keys="Conversation.participant1_id",
    back_populates="participant1"
    )

    # Relations pour les conversations (en tant que participant2)  
    conversations_as_participant2 = relationship(
    "Conversation", 
    foreign_keys="Conversation.participant2_id",
    back_populates="participant2"
    )
    
    __mapper_args__ = {
        'polymorphic_identity': 'utilisateur',
        'polymorphic_on': type
    }

# Ces relations sont définies après la classe pour éviter les dépendances circulaires
Utilisateur.messages_envoyes = relationship("Message", foreign_keys="Message.emetteur_id", back_populates="emetteur")
Utilisateur.messages_recus = relationship("Message", foreign_keys="Message.destinataire_id", back_populates="destinataire")