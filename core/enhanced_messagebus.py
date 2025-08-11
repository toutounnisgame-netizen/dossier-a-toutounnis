# -*- coding: utf-8 -*-
"""
ALMAA v2.0 - Enhanced MessageBus
MessageBus amélioré avec routing intelligent et gestion robuste
"""
from typing import List, Dict, Optional, Callable, Set, Any
from collections import defaultdict
import threading
import time
from queue import Queue, Empty
from core.base import Message, BaseAgent
from core.response_manager import ResponseManager
from loguru import logger


class EnhancedMessageBus:
    """MessageBus amélioré avec routing intelligent"""
    
    def __init__(self, response_manager: Optional[ResponseManager] = None):
        self.agents: Dict[str, BaseAgent] = {}
        self.subscribers: Dict[str, Set[str]] = defaultdict(set)
        self.response_manager = response_manager or ResponseManager()
        
        # Gestion des messages
        self.message_queue = Queue()
        self.message_history: List[Message] = []
        self.running = False
        self.processing_thread = None
        self._lock = threading.Lock()
        
        # Routing intelligent
        self.routing_rules: Dict[str, Callable] = {
            "REQUEST": self._route_request,
            "RESPONSE": self._route_response,
            "TASK_ASSIGNMENT": self._route_task,
            "ERROR": self._route_error
        }
        
        # Statistiques détaillées
        self.stats = {
            "messages_sent": 0,
            "messages_delivered": 0,
            "messages_failed": 0,
            "routing_errors": 0,
            "processing_errors": 0
        }
        
    def register_agent(self, agent: BaseAgent):
        """Enregistre un agent sur le bus"""
        with self._lock:
            self.agents[agent.name] = agent
            logger.info(f"Agent {agent.name} registered on enhanced message bus")
            
    def unregister_agent(self, agent_name: str):
        """Désenregistre un agent"""
        with self._lock:
            if agent_name in self.agents:
                del self.agents[agent_name]
                # Nettoyer les subscriptions
                for msg_type in list(self.subscribers.keys()):
                    self.subscribers[msg_type].discard(agent_name)
                logger.info(f"Agent {agent_name} unregistered")
                
    def subscribe(self, agent_name: str, message_type: str):
        """Abonne un agent à un type de message"""
        with self._lock:
            self.subscribers[message_type].add(agent_name)
            logger.debug(f"{agent_name} subscribed to {message_type}")
            
    def publish(self, message: Message):
        """Publie un message sur le bus avec routing intelligent"""
        # Ajouter métadonnées
        if not message.id:
            from uuid import uuid4
            message.id = str(uuid4())
            
        self.message_queue.put(message)
        self.stats["messages_sent"] += 1
        logger.debug(f"Message {message.type} published by {message.sender}")
        
    def start(self):
        """Démarre le traitement des messages"""
        if not self.running:
            self.running = True
            self.processing_thread = threading.Thread(target=self._process_loop)
            self.processing_thread.daemon = True
            self.processing_thread.start()
            logger.info("Enhanced MessageBus started")
            
    def stop(self):
        """Arrête le traitement des messages"""
        self.running = False
        if self.processing_thread:
            self.processing_thread.join(timeout=5)
        self.response_manager.shutdown()
        logger.info("Enhanced MessageBus stopped")
        
    def _process_loop(self):
        """Boucle principale de traitement des messages"""
        while self.running:
            try:
                message = self.message_queue.get(timeout=0.1)
                success = self._route_and_deliver(message)
                
                if success:
                    self.message_history.append(message)
                    # Limiter l'historique
                    if len(self.message_history) > 1000:
                        self.message_history = self.message_history[-500:]
                else:
                    self.stats["messages_failed"] += 1
                    
            except Empty:
                continue
            except Exception as e:
                logger.error(f"Message processing error: {e}")
                self.stats["processing_errors"] += 1
                
    def _route_and_deliver(self, message: Message) -> bool:
        """Route et délivre un message selon son type"""
        try:
            # Utiliser le routeur approprié
            router = self.routing_rules.get(message.type, self._route_default)
            return router(message)
            
        except Exception as e:
            logger.error(f"Routing error for {message.type}: {e}")
            self.stats["routing_errors"] += 1
            return False
            
    def _route_request(self, message: Message) -> bool:
        """Route une requête utilisateur"""
        # Les REQUEST vont par défaut au Chef
        if not message.recipient:
            message.recipient = "Chef"
            
        # Enregistrer dans le response manager si c'est une requête utilisateur
        if message.sender == "User":
            self.response_manager.create_request(
                message.content.get("request", ""),
                timeout=30
            )
            
        return self._deliver_message(message)
        
    def _route_response(self, message: Message) -> bool:
        """Route une réponse"""
        # Enregistrer la réponse dans le manager
        if message.recipient == "User":
            self.response_manager.register_response(message)
            
        return self._deliver_message(message)
        
    def _route_task(self, message: Message) -> bool:
        """Route une assignation de tâche"""
        # Vérifier que le destinataire existe
        if message.recipient and message.recipient not in self.agents:
            logger.warning(f"Task assigned to unknown agent: {message.recipient}")
            # Essayer de le router vers un agent similaire
            similar_agent = self._find_similar_agent(message.recipient)
            if similar_agent:
                message.recipient = similar_agent
                logger.info(f"Rerouted task to similar agent: {similar_agent}")
            else:
                return False
                
        return self._deliver_message(message)
        
    def _route_error(self, message: Message) -> bool:
        """Route une erreur"""
        # Les erreurs remontent toujours vers l'utilisateur ou le chef
        if not message.recipient:
            message.recipient = "User" if message.sender != "Chef" else "System"
            
        # Enregistrer l'erreur
        if message.recipient == "User":
            self.response_manager.register_response(message)
            
        return self._deliver_message(message)
        
    def _route_default(self, message: Message) -> bool:
        """Routage par défaut"""
        return self._deliver_message(message)
        
    def _deliver_message(self, message: Message) -> bool:
        """Délivre physiquement un message"""
        delivered = False
        
        try:
            # Message direct
            if message.recipient:
                if message.recipient in self.agents:
                    self.agents[message.recipient].receive_message(message)
                    delivered = True
                    self.stats["messages_delivered"] += 1
                    logger.debug(f"Direct message delivered to {message.recipient}")
                else:
                    logger.warning(f"Recipient {message.recipient} not found")
                    return False
                    
            # Broadcast aux abonnés
            else:
                subscribers = self.subscribers.get(message.type, set())
                for subscriber in subscribers:
                    if subscriber in self.agents and subscriber != message.sender:
                        self.agents[subscriber].receive_message(message)
                        delivered = True
                        
                if delivered:
                    self.stats["messages_delivered"] += len(subscribers)
                    
            return delivered
            
        except Exception as e:
            logger.error(f"Message delivery error: {e}")
            return False
            
    def _find_similar_agent(self, agent_name: str) -> Optional[str]:
        """Trouve un agent similaire par nom/rôle"""
        # Extraction du type d'agent
        agent_type = agent_name.lower()
        
        for name, agent in self.agents.items():
            if (agent_type in name.lower() or 
                agent_type in agent.role.lower() or
                name.lower() in agent_type):
                return name
                
        return None
        
    def process_agent_messages(self):
        """Traite les messages en attente des agents"""
        with self._lock:
            for agent in self.agents.values():
                # Traiter inbox
                messages_to_process = list(agent.inbox)
                agent.inbox.clear()
                
                for message in messages_to_process:
                    try:
                        response = agent.process_message(message)
                        if response:
                            self.publish(response)
                    except Exception as e:
                        logger.error(f"Agent {agent.name} processing error: {e}")
                        
                # Envoyer outbox
                messages_to_send = list(agent.outbox)
                agent.outbox.clear()
                
                for message in messages_to_send:
                    self.publish(message)
                    
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques détaillées"""
        return {
            **self.stats,
            "agents_count": len(self.agents),
            "queue_size": self.message_queue.qsize(),
            "history_size": len(self.message_history),
            "response_manager": self.response_manager.get_stats()
        }
        
    def get_agent_status(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """Retourne le statut d'un agent spécifique"""
        if agent_name in self.agents:
            agent = self.agents[agent_name]
            return {
                "name": agent.name,
                "role": agent.role,
                "state": agent.state,
                "inbox_size": len(agent.inbox),
                "outbox_size": len(agent.outbox),
                "subscriptions": [
                    msg_type for msg_type, subscribers in self.subscribers.items()
                    if agent_name in subscribers
                ]
            }
        return None
        
    def clear_history(self):
        """Vide l'historique des messages"""
        with self._lock:
            self.message_history.clear()
            logger.info("Message history cleared")