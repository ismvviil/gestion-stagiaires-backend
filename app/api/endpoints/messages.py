from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List

from app.api.deps import get_current_user, get_db
from app.models.utilisateur import Utilisateur
from app.models.conversation import Conversation
from app.models.message import Message
from app.schemas.message import (
    MessageCreate, MessageResponse, MessageUpdate, ConversationMessages
)
from app.services.conversation_service import send_message

router = APIRouter()

@router.get("/conversation/{conversation_id}", response_model=ConversationMessages)
def get_conversation_messages(
    *,
    db: Session = Depends(get_db),
    conversation_id: int,
    current_user: Utilisateur = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100)
):
    """Récupérer les messages d'une conversation."""
    
    # Vérifier que la conversation existe et que l'utilisateur y participe
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
    
     # Récupérer les messages avec pagination
    messages_query = db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).order_by(Message.date.desc())

    total = messages_query.count()
    messages = messages_query.offset(skip).limit(limit).all()

     # Enrichir les messages avec les informations de l'émetteur
    messages_with_info = []
    for message in messages:
        message_dict = {
            **message.__dict__,
            "emetteur_nom": message.emetteur.nom,
            "emetteur_prenom": message.emetteur.prenom
        }
        messages_with_info.append(MessageResponse(**message_dict))

    return ConversationMessages(
        conversation_id=conversation_id,
        messages=messages_with_info,
        total=total
    )

# @router.post("/", response_model=MessageResponse)
# def send_message_endpoint(
#     *,
#     db: Session = Depends(get_db),
#     message_in: MessageCreate,
#     current_user: Utilisateur = Depends(get_current_user)
# ):
#     """Envoyer un message dans une conversation."""

#     # Vérifier que la conversation existe et que l'utilisateur y participe
#     conversation = db.query(Conversation).filter(
#         Conversation.id == message_in.conversation_id
#     ).first()

#     if not conversation:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Conversation non trouvée"
#         )
    
#     if not conversation.has_participant(current_user.id):
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Accès non autorisé à cette conversation"
#         )
    
#     # Envoyer le message
#     message = send_message(
#         db, 
#         message_in.conversation_id, 
#         current_user.id, 
#         message_in.contenu
#     )

#     if not message:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Erreur lors de l'envoi du message"
#         )
    
#     # Enrichir avec les informations de l'émetteur
#     message_response = MessageResponse(
#         **message.__dict__,
#         emetteur_nom=current_user.nom,
#         emetteur_prenom=current_user.prenom
#     )

#     return message_response

@router.post("/", response_model=MessageResponse)
async def send_message_endpoint(  # ← ASYNC obligatoire pour WebSocket
    *,
    db: Session = Depends(get_db),
    message_in: MessageCreate,
    current_user: Utilisateur = Depends(get_current_user)
):
    """Envoyer un message dans une conversation."""

    # Vérifier que la conversation existe et que l'utilisateur y participe
    conversation = db.query(Conversation).filter(
        Conversation.id == message_in.conversation_id
    ).first()

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
    
    # Envoyer le message via le service
    message = send_message(
        db, 
        message_in.conversation_id, 
        current_user.id, 
        message_in.contenu
    )

    if not message:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de l'envoi du message"
        )

    # Créer la réponse enrichie
    message_response = MessageResponse(
        **message.__dict__,
        emetteur_nom=current_user.nom,
        emetteur_prenom=current_user.prenom
    )

    # 🔥 Notification WebSocket en temps réel
    try:
        participants = [conversation.participant1_id, conversation.participant2_id]
        websocket_message = {
            "type": "new_message",
            "message": {
                "id": message.id,
                "contenu": message.contenu,
                "date": message.date.isoformat(),
                "lu": message.lu,
                "emetteur_id": message.emetteur_id,
                "destinataire_id": message.destinataire_id,
                "conversation_id": message.conversation_id,
                "emetteur_nom": current_user.nom,
                "emetteur_prenom": current_user.prenom
            }
        }
        
        # Notifier via WebSocket
        from app.websocket.connection_manager import manager
        await manager.send_message_to_conversation(websocket_message, participants)
        
    except Exception as e:
        # Log l'erreur mais ne pas faire échouer l'envoi du message
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erreur notification WebSocket: {e}")

    return message_response


@router.put("/{message_id}/read", response_model=MessageResponse)
def mark_message_as_read(
    *,
    db: Session = Depends(get_db),
    message_id: int,
    current_user: Utilisateur = Depends(get_current_user)
):
    """Marquer un message comme lu."""

    message = db.query(Message).filter(Message.id == message_id).first()

    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message non trouvé"
        )
    
    # Vérifier que l'utilisateur est le destinataire
    if message.destinataire_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous ne pouvez marquer comme lu que vos propres messages"
        )
    
    message.mark_as_read()
    db.commit()
    db.refresh(message)
    
    return MessageResponse(
        **message.__dict__,
        emetteur_nom=message.emetteur.nom,
        emetteur_prenom=message.emetteur.prenom
    )

@router.get("/unread-count")
def get_unread_messages_count(
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)
):
    """Récupérer le nombre total de messages non lus."""
    
    count = db.query(Message).filter(
        Message.destinataire_id == current_user.id,
        Message.lu == False
    ).count()
    
    return {"unread_count": count}
