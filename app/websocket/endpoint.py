from fastapi import WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.websocket.connection_manager import manager
from app.websocket.auth import get_user_from_token
from app.services.conversation_service import send_message
import json
import logging

logger = logging.getLogger(__name__)

async def websocket_endpoint(websocket: WebSocket, token: str, db: Session = Depends(get_db)):
    """Endpoint WebSocket principal pour la messagerie."""

    try:
        # Authentifier l'utilisateur
        user = await get_user_from_token(token, db)

        # Connecter l'utilisateur
        await manager.connect(websocket, user.id)
    
        # Envoyer les informations de connexion
        await manager.send_personal_message({
            "type": "connection_success",
            "message": "Connecté avec succès",
            "user_id": user.id,
            "online_users": manager.get_online_users()
        }, user.id)

        try:
            while True:
                # Recevoir les messages du client
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                await handle_websocket_message(message_data, user, db)

        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for user {user.id}")
        except Exception as e:
            logger.error(f"Erreur dans WebSocket pour user {user.id}: {e}")
            await manager.send_personal_message({
                "type": "error",
                "message": f"Erreur: {str(e)}"
            }, user.id)

    except HTTPException as e:
        # Erreur d'authentification
        await websocket.close(code=1008, reason="Authentication failed")
        return
    except Exception as e:
        logger.error(f"Erreur WebSocket: {e}")
        await websocket.close(code=1011, reason="Internal server error")
    
    finally:
        # Déconnecter proprement
        await manager.disconnect(websocket)

async def handle_websocket_message(message_data: dict, user, db: Session):
    """Gérer les différents types de messages WebSocket."""

    message_type = message_data.get("type")
    
    if message_type == "send_message":
        await handle_send_message(message_data, user, db)
    elif message_type == "mark_as_read":
        await handle_mark_as_read(message_data, user, db)
    elif message_type == "typing":
        await handle_typing_indicator(message_data, user, db)
    elif message_type == "ping":
        await handle_ping(user)
    else:
        logger.warning(f"Type de message inconnu: {message_type}")

async def handle_send_message(message_data: dict, user, db: Session):
    """Gérer l'envoi d'un nouveau message."""
    try:
        conversation_id = message_data.get("conversation_id")
        contenu = message_data.get("contenu")

        if not conversation_id or not contenu:
            raise ValueError("conversation_id et contenu sont requis")
        
        # Envoyer le message via le service
        message = send_message(db, conversation_id, user.id, contenu)

        if message:
            # Récupérer les participants de la conversation
            participants = [message.conversation.participant1_id, message.conversation.participant2_id]
            
            # Préparer le message à diffuser
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
                    "emetteur_nom": user.nom,
                    "emetteur_prenom": user.prenom
                }
            }

            # Envoyer à tous les participants
            await manager.send_message_to_conversation(websocket_message, participants)
        else:
            await manager.send_personal_message({
                "type": "error",
                "message": "Impossible d'envoyer le message"
            }, user.id)
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi du message: {e}")
        await manager.send_personal_message({
            "type": "error",
            "message": f"Erreur lors de l'envoi: {str(e)}"
        }, user.id)

async def handle_mark_as_read(message_data: dict, user, db: Session):
    """Gérer le marquage des messages comme lus."""
    try:
        conversation_id = message_data.get("conversation_id")
        
        if not conversation_id:
            return
        
        # Marquer tous les messages de la conversation comme lus pour cet utilisateur
        from app.models.message import Message
        messages_to_update = db.query(Message).filter(
            Message.conversation_id == conversation_id,
            Message.destinataire_id == user.id,
            Message.lu == False
        ).all()

        for msg in messages_to_update:
            msg.lu = True

        db.commit()

        # Notifier les autres participants
        from app.models.conversation import Conversation
        conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if conversation:
            participants = [conversation.participant1_id, conversation.participant2_id]
            other_participant_id = None
            for p_id in participants:
                if p_id != user.id:
                    other_participant_id = p_id
                    break
            
            if other_participant_id:
                await manager.send_personal_message({
                    "type": "messages_read",
                    "conversation_id": conversation_id,
                    "reader_id": user.id
                }, other_participant_id)

    except Exception as e:
        logger.error(f"Erreur lors du marquage comme lu: {e}")

async def handle_typing_indicator(message_data: dict, user, db: Session):
    """Gérer l'indicateur de frappe."""
    try:
        conversation_id = message_data.get("conversation_id")
        is_typing = message_data.get("is_typing", False)

        if not conversation_id:
            return
        
        # Récupérer la conversation et notifier l'autre participant
        from app.models.conversation import Conversation
        conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()

        if conversation:
            other_participant_id = conversation.get_other_participant(user.id).id
            
            await manager.send_personal_message({
                "type": "typing_indicator",
                "conversation_id": conversation_id,
                "user_id": user.id,
                "user_name": f"{user.prenom} {user.nom}",
                "is_typing": is_typing
            }, other_participant_id)
    
    except Exception as e:
        logger.error(f"Erreur indicateur de frappe: {e}")

async def handle_ping(user):
    """Gérer les messages de ping pour maintenir la connexion."""
    await manager.send_personal_message({
        "type": "pong",
        "timestamp": manager.get_current_timestamp()
    }, user.id)