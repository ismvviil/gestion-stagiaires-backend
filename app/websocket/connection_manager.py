from typing import Dict, List
from fastapi import WebSocket, WebSocketDisconnect
import json
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        # Dictionnaire des connexions actives: {user_id: [websocket1, websocket2, ...]}
        self.active_connections: Dict[int, List[WebSocket]] = {}
        # Dictionnaire pour mapper websocket -> user_id
        self.websocket_to_user: Dict[WebSocket, int] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
            """Accepter une nouvelle connexion WebSocket."""
            await websocket.accept()
            
            # Ajouter la connexion à la liste des connexions actives
            if user_id not in self.active_connections:
                self.active_connections[user_id] = []
            
            self.active_connections[user_id].append(websocket)
            self.websocket_to_user[websocket] = user_id
            
            logger.info(f"Utilisateur {user_id} connecté via WebSocket")
            
            # Notifier que l'utilisateur est en ligne
            await self.broadcast_user_status(user_id, "online")

    async def disconnect(self, websocket: WebSocket):
        """Déconnecter un WebSocket."""
        user_id = self.websocket_to_user.get(websocket)
        
        if user_id and user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)
            
            # Si plus de connexions pour cet utilisateur, le supprimer
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                # Notifier que l'utilisateur est hors ligne
                await self.broadcast_user_status(user_id, "offline")
        
        if websocket in self.websocket_to_user:
            del self.websocket_to_user[websocket]
        
        logger.info(f"Utilisateur {user_id} déconnecté")


    async def send_personal_message(self, message: dict, user_id: int):
        """Envoyer un message privé à un utilisateur spécifique."""
        if user_id in self.active_connections:
            message_str = json.dumps(message)
            
            # Envoyer à toutes les connexions de cet utilisateur
            disconnected_websockets = []
            for websocket in self.active_connections[user_id]:
                try:
                    await websocket.send_text(message_str)
                except:
                    # Marquer les connexions fermées pour suppression
                    disconnected_websockets.append(websocket)
            
            # Nettoyer les connexions fermées
            for ws in disconnected_websockets:
                await self.disconnect(ws)

    async def send_message_to_conversation(self, message: dict, participant_ids: List[int]):
        """Envoyer un message à tous les participants d'une conversation."""
        for user_id in participant_ids:
            await self.send_personal_message(message, user_id)

    async def broadcast_user_status(self, user_id: int, status: str):
        """Diffuser le statut d'un utilisateur à tous les utilisateurs connectés."""
        status_message = {
            "type": "user_status",
            "user_id": user_id,
            "status": status,
            "timestamp": self.get_current_timestamp()
        }
        
        # Envoyer à tous les utilisateurs connectés
        for connected_user_id in self.active_connections.keys():
            if connected_user_id != user_id:  # Ne pas envoyer à soi-même
                await self.send_personal_message(status_message, connected_user_id)

    def is_user_online(self, user_id: int) -> bool:
        """Vérifier si un utilisateur est en ligne."""
        return user_id in self.active_connections and len(self.active_connections[user_id]) > 0
    
    def get_online_users(self) -> List[int]:
        """Obtenir la liste des utilisateurs en ligne."""
        return list(self.active_connections.keys())
    
    @staticmethod
    def get_current_timestamp():
        """Obtenir le timestamp actuel."""
        from datetime import datetime
        return datetime.now().isoformat()
    
# Instance globale du gestionnaire de connexions
manager = ConnectionManager()