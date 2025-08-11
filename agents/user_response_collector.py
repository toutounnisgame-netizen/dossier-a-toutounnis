# -*- coding: utf-8 -*-
"""
ALMAA v2.0 - User Response Collector
Agent spécialisé dans la collecte des réponses utilisateur
Remplace UserListener avec gestion robuste des réponses
"""
from core.base import BaseAgent, Message
from core.response_manager import ResponseManager
from typing import Optional, Dict, Any, List
from loguru import logger


class UserResponseCollector(BaseAgent):
    """Agent spécialisé dans la collecte des réponses pour l'utilisateur"""
    
    def __init__(self, response_manager: ResponseManager):
        super().__init__("User", "ResponseCollector")
        self.response_manager = response_manager
        self.collected_responses: List[Message] = []
        
        # Statistiques
        self.responses_collected = 0
        self.errors_handled = 0
        
    def process_message(self, message: Message) -> Optional[Message]:
        """Traite un message entrant et le sauvegarde si c'est une réponse"""
        
        logger.debug(f"UserResponseCollector received: {message.type} from {message.sender}")
        
        # Sauvegarder TOUTES les réponses destinées à l'utilisateur
        if message.recipient == "User" and message.type in ["RESPONSE", "ERROR", "TASK_RESULT"]:
            self._collect_response(message)
            
        # Traiter selon le type
        if message.type == "RESPONSE":
            return self._handle_response(message)
        elif message.type == "ERROR":
            return self._handle_error(message)
        elif message.type == "TASK_RESULT":
            return self._handle_task_result(message)
        elif message.type == "PING":
            return self._handle_ping(message)
        else:
            logger.debug(f"UserResponseCollector ignoring message type: {message.type}")
            return None
            
    def _collect_response(self, message: Message):
        """Collecte et sauvegarde une réponse"""
        
        # Sauvegarder localement
        self.collected_responses.append(message)
        self.responses_collected += 1
        
        # Notifier le ResponseManager
        self.response_manager.register_response(message)
        
        # Limiter le cache local
        if len(self.collected_responses) > 100:
            self.collected_responses = self.collected_responses[-50:]
            
        logger.info(f"Response collected from {message.sender}")
        
    def _handle_response(self, message: Message) -> None:
        """Traite une réponse normale"""
        content = message.content
        
        if isinstance(content, dict):
            response_text = content.get("message", content.get("result", str(content)))
        else:
            response_text = str(content)
            
        logger.success(f"User response ready: {response_text[:100]}...")
        return None  # Ne pas générer de réponse supplémentaire
        
    def _handle_error(self, message: Message) -> None:
        """Traite une erreur"""
        self.errors_handled += 1
        
        error_msg = message.content.get("error", "Unknown error")
        logger.error(f"User error received: {error_msg}")
        
        return None
        
    def _handle_task_result(self, message: Message) -> None:
        """Traite un résultat de tâche"""
        result = message.content
        status = result.get("status", "unknown")
        
        if status == "completed":
            logger.success(f"Task completed: {result.get('result', 'No result')[:100]}...")
        else:
            logger.warning(f"Task status: {status}")
            
        return None
        
    def _handle_ping(self, message: Message) -> Message:
        """Répond à un ping"""
        return Message(
            sender=self.name,
            recipient=message.sender,
            type="PONG",
            content={
                "status": "alive",
                "responses_collected": self.responses_collected,
                "errors_handled": self.errors_handled
            }
        )
        
    def get_latest_responses(self, count: int = 5) -> List[Message]:
        """Retourne les dernières réponses collectées"""
        return self.collected_responses[-count:]
        
    def get_response_by_sender(self, sender: str) -> Optional[Message]:
        """Retourne la dernière réponse d'un expéditeur spécifique"""
        for message in reversed(self.collected_responses):
            if message.sender == sender:
                return message
        return None
        
    def clear_responses(self):
        """Vide le cache des réponses"""
        self.collected_responses.clear()
        logger.info("Response cache cleared")
        
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques du collector"""
        return {
            "responses_collected": self.responses_collected,
            "errors_handled": self.errors_handled,
            "cached_responses": len(self.collected_responses),
            "state": self.state
        }
        
    def think(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Processus de réflexion (minimal pour ce type d'agent)"""
        return {
            "thought": "Collecting responses for user",
            "status": "ready",
            "capacity": "unlimited"
        }