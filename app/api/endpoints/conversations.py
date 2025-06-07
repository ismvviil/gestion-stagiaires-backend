from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.api.deps import get_current_user, get_db
from app.models.utilisateur import Utilisateur
from app.models.conversation import Conversation
from app.models.message import Message

from app.schemas.conversation import (
    ConversationCreate, ConversationResponse, ConversationWithLastMessage
)
from app.services.conversation_service import (
    get_or_create_private_conversation, get_user_conversations
)

from app.schemas.message import (
     MessageResponse
)


router = APIRouter()

@router.get("/", response_model=List[ConversationWithLastMessage])
def get_my_conversations(
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)
):
    """Récupérer toutes les conversations de l'utilisateur connecté."""
    
    conversations = get_user_conversations(db, current_user.id)

    result = []
    for conv in conversations:
        # Récupérer l'autre participant
        autre_participant = conv.get_other_participant(current_user.id)

        # Récupérer le dernier message
        dernier_message = conv.get_last_message()

        # Compter les messages non lus
        messages_non_lus = db.query(Message).filter(
            Message.conversation_id == conv.id,
            Message.destinataire_id == current_user.id,
            Message.lu == False
        ).count()

        conv_data = ConversationWithLastMessage(
            id=conv.id,
            created_at=conv.created_at,
            updated_at=conv.updated_at,
            est_active=conv.est_active,
            participant1_id=conv.participant1_id,
            participant2_id=conv.participant2_id,
            dernier_message=dernier_message,
            messages_non_lus=messages_non_lus,
            autre_participant=autre_participant
        )
        result.append(conv_data)
    
    # Trier par date du dernier message (plus récent en premier)
    result.sort(key=lambda x: x.dernier_message.date if x.dernier_message else x.created_at, reverse=True)
    
    return result

@router.post("/", response_model=ConversationResponse)
def create_or_get_conversation(
    *,
    db: Session = Depends(get_db),
    conversation_in: ConversationCreate,
    current_user: Utilisateur = Depends(get_current_user)
):
    """Créer ou récupérer une conversation avec un autre utilisateur."""

    # Vérifier que l'autre participant existe
    autre_participant = db.query(Utilisateur).filter(
        Utilisateur.id == conversation_in.participant_id
    ).first()

    if not autre_participant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé"
        )
    
    if autre_participant.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossible de créer une conversation avec soi-même"
        )
    
    # Créer ou récupérer la conversation
    conversation = get_or_create_private_conversation(
        db, current_user.id, conversation_in.participant_id
    )

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la création de la conversation"
        )
    
    return conversation


@router.get("/{conversation_id}", response_model=ConversationResponse)
def get_conversation(
    *,
    db: Session = Depends(get_db),
    conversation_id: int,
    current_user: Utilisateur = Depends(get_current_user)
):
    """Récupérer une conversation spécifique."""

    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation non trouvée"
        )
    
    # Vérifier que l'utilisateur participe à cette conversation
    if not conversation.has_participant(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès non autorisé à cette conversation"
        )
    
    return conversation

@router.put("/{conversation_id}/mark-as-read")
def mark_conversation_as_read(
    *,
    db: Session = Depends(get_db),
    conversation_id: int,
    current_user: Utilisateur = Depends(get_current_user)
):
    """Marquer tous les messages de la conversation comme lus."""

    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation non trouvée"
        )
    
    if not conversation.has_participant(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès non autorisé à cette conversation"
        )
    
    # Marquer tous les messages reçus comme lus
    db.query(Message).filter(
        Message.conversation_id == conversation_id,
        Message.destinataire_id == current_user.id,
        Message.lu == False
    ).update({"lu": True})

    db.commit()
    
    return {"message": "Messages marqués comme lus"}


@router.get("/{conversation_id}/messages", response_model=List[MessageResponse])
def get_conversation_messages(
    *,
    db: Session = Depends(get_db),
    conversation_id: int,
    skip: int = 0,
    limit: int = 50,  # Pagination
    current_user: Utilisateur = Depends(get_current_user)
):
    """Récupérer l'historique des messages d'une conversation."""
    
    # Vérifier l'accès à la conversation
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation or not conversation.has_participant(current_user.id):
        raise HTTPException(status_code=403, detail="Accès refusé")
    
    # Récupérer les messages avec pagination
    messages = db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).order_by(Message.date.desc()).offset(skip).limit(limit).all()
    
    return messages