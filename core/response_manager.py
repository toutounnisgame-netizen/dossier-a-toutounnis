# -*- coding: utf-8 -*-
"""
ALMAA v2.0 - Response Manager
Gestionnaire centralisé des réponses utilisateur
Résout définitivement le problème de perte de messages
"""
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from uuid import uuid4
import threading
from collections import defaultdict
from loguru import logger
from core.base import Message


class PendingRequest:
    """Représente une requête en attente de réponse"""
    
    def __init__(self, request_id: str, user_request: str, timeout: int = 30):
        self.request_id = request_id
        self.user_request = user_request
        self.created_at = datetime.now()
        self.timeout = timeout
        self.response: Optional[Message] = None
        self.status = "pending"  # pending, completed, timeout, error
        self.thread_id: Optional[str] = None
        
    def is_expired(self) -> bool:
        """Vérifie si la requête a expiré"""
        return datetime.now() - self.created_at > timedelta(seconds=self.timeout)
        
    def complete_with_response(self, response: Message):
        """Marque la requête comme complétée avec une réponse"""
        self.response = response
        self.status = "completed"
        logger.debug(f"Request {self.request_id} completed")
        
    def complete_with_error(self, error: str):
        """Marque la requête comme échouée"""
        self.status = "error"
        self.response = Message(
            sender="System",
            recipient="User",
            type="ERROR",
            content={"error": error}
        )
        logger.error(f"Request {self.request_id} failed: {error}")


class ResponseManager:
    """Gestionnaire centralisé des réponses utilisateur"""
    
    def __init__(self):
        self.pending_requests: Dict[str, PendingRequest] = {}
        self.completed_responses: List[Message] = []
        self._lock = threading.Lock()
        self.stats = {
            "requests_created": 0,
            "responses_received": 0,
            "timeouts": 0,
            "errors": 0
        }
        
        # Nettoyage automatique des anciennes requêtes
        self._cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self._cleanup_running = True
        self._cleanup_thread.start()
        
    def create_request(self, user_request: str, timeout: int = 30) -> str:
        """Crée une nouvelle requête et retourne son ID"""
        request_id = str(uuid4())
        
        with self._lock:
            pending_request = PendingRequest(request_id, user_request, timeout)
            self.pending_requests[request_id] = pending_request
            self.stats["requests_created"] += 1
            
        logger.info(f"Created request {request_id}: {user_request[:50]}...")
        return request_id
        
    def register_response(self, response: Message) -> bool:
        """Enregistre une réponse et l'associe à une requête en attente"""
        
        with self._lock:
            # Sauvegarder toutes les réponses
            self.completed_responses.append(response)
            self.stats["responses_received"] += 1
            
            # Chercher la requête correspondante
            matching_request = None
            
            # 1. Chercher par thread_id si disponible
            if response.thread_id:
                for req in self.pending_requests.values():
                    if req.thread_id == response.thread_id and req.status == "pending":
                        matching_request = req
                        break
            
            # 2. Chercher la plus ancienne requête en attente (fallback)
            if not matching_request:
                oldest_pending = None
                for req in self.pending_requests.values():
                    if req.status == "pending":
                        if not oldest_pending or req.created_at < oldest_pending.created_at:
                            oldest_pending = req
                matching_request = oldest_pending
            
            # Associer la réponse à la requête
            if matching_request:
                matching_request.complete_with_response(response)
                logger.info(f"Response matched to request {matching_request.request_id}")
                return True
            else:
                logger.warning("Received response but no pending request found")
                return False
                
    def get_response(self, request_id: str, wait_timeout: float = 0.1) -> Optional[Dict[str, Any]]:
        """Récupère la réponse pour une requête donnée"""
        
        end_time = datetime.now() + timedelta(seconds=wait_timeout)
        
        while datetime.now() < end_time:
            with self._lock:
                if request_id in self.pending_requests:
                    request = self.pending_requests[request_id]
                    
                    if request.status == "completed":
                        # Nettoyer la requête
                        del self.pending_requests[request_id]
                        
                        return {
                            "success": True,
                            "response": request.response.content.get("message", request.response.content),
                            "full_message": request.response,
                            "duration": (datetime.now() - request.created_at).total_seconds()
                        }
                        
                    elif request.status == "error":
                        # Nettoyer la requête
                        del self.pending_requests[request_id]
                        
                        return {
                            "success": False,
                            "error": request.response.content.get("error", "Unknown error"),
                            "duration": (datetime.now() - request.created_at).total_seconds()
                        }
                        
                    elif request.is_expired():
                        # Marquer comme timeout
                        request.status = "timeout"
                        self.stats["timeouts"] += 1
                        del self.pending_requests[request_id]
                        
                        return {
                            "success": False,
                            "error": "Request timeout",
                            "duration": request.timeout
                        }
            
            # Petite pause pour éviter le busy waiting
            import time
            time.sleep(0.01)
        
        # Timeout de la fonction get_response elle-même
        return {
            "success": False,
            "error": "Response retrieval timeout",
            "duration": wait_timeout
        }
        
    def get_all_responses_for_user(self, limit: int = 10) -> List[Message]:
        """Récupère les dernières réponses pour l'utilisateur"""
        with self._lock:
            user_responses = [
                msg for msg in self.completed_responses 
                if msg.recipient == "User" and msg.type in ["RESPONSE", "ERROR"]
            ]
            return user_responses[-limit:]
            
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques du gestionnaire"""
        with self._lock:
            return {
                **self.stats,
                "pending_requests": len(self.pending_requests),
                "completed_responses": len(self.completed_responses)
            }
            
    def _cleanup_loop(self):
        """Boucle de nettoyage des anciennes requêtes"""
        while self._cleanup_running:
            try:
                with self._lock:
                    expired_requests = [
                        req_id for req_id, req in self.pending_requests.items()
                        if req.is_expired()
                    ]
                    
                    for req_id in expired_requests:
                        self.pending_requests[req_id].status = "timeout"
                        self.stats["timeouts"] += 1
                        del self.pending_requests[req_id]
                        logger.warning(f"Request {req_id} expired")
                
                # Limiter l'historique des réponses
                with self._lock:
                    if len(self.completed_responses) > 1000:
                        self.completed_responses = self.completed_responses[-500:]
                
                import time
                time.sleep(5)  # Nettoyage toutes les 5 secondes
                
            except Exception as e:
                logger.error(f"Cleanup loop error: {e}")
                import time
                time.sleep(1)
                
    def shutdown(self):
        """Arrêt propre du gestionnaire"""
        self._cleanup_running = False
        if self._cleanup_thread.is_alive():
            self._cleanup_thread.join(timeout=2)
        logger.info("ResponseManager shutdown complete")