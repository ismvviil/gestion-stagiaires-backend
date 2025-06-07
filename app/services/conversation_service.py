from sqlalchemy.orm import Session
from app.models.conversation import Conversation
from app.models.utilisateur import Utilisateur
from app.models.message import Message
from sqlalchemy import func  # Ajoutez cette ligne aux imports
from sqlalchemy import or_, and_

def get_or_create_private_conversation(db: Session, user1_id: int, user2_id: int):
    """Récupérer ou créer une conversation privée entre deux utilisateurs."""

    # Vérifier que les deux utilisateurs sont différents
    if user1_id == user2_id:
        return None
    
    # Chercher si une conversation existe déjà entre ces deux utilisateurs
    existing_conversation = db.query(Conversation).filter(
        or_(
            and_(Conversation.participant1_id == user1_id, Conversation.participant2_id == user2_id),
            and_(Conversation.participant1_id == user2_id, Conversation.participant2_id == user1_id)
        )
    ).first()
    
    if existing_conversation:
        return existing_conversation

    # Vérifier que les deux utilisateurs existent
    user1 = db.query(Utilisateur).filter(Utilisateur.id == user1_id).first()
    user2 = db.query(Utilisateur).filter(Utilisateur.id == user2_id).first()

    if not user1 or not user2:
        return None
    
    # Créer une nouvelle conversation
    conversation = Conversation(
        participant1_id=user1_id,
        participant2_id=user2_id
    )
    
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    
    return conversation

def get_user_conversations(db: Session, user_id: int):
    """Récupérer toutes les conversations d'un utilisateur."""
    conversations = db.query(Conversation).filter(
        or_(
            Conversation.participant1_id == user_id,
            Conversation.participant2_id == user_id
        )
    ).filter(Conversation.est_active == True).all()
    
    return conversations

def send_message(db: Session, conversation_id: int, emetteur_id: int, contenu: str):
    """Envoyer un message dans une conversation."""
    
    # Vérifier que la conversation existe et que l'utilisateur y participe
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation or not conversation.has_participant(emetteur_id):
        return None
    
    # Déterminer le destinataire
    destinataire_id = conversation.get_other_participant(emetteur_id).id
    
    # Créer le message
    message = Message(
        contenu=contenu,
        emetteur_id=emetteur_id,
        destinataire_id=destinataire_id,
        conversation_id=conversation_id
    )
    
    db.add(message)
    db.commit()
    db.refresh(message)
    
    return message