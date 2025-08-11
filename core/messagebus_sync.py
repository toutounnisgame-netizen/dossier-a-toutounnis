# -*- coding: utf-8 -*-
"""
MessageBus Synchrone pour ALMAA - VERSION DEBUG FIXÉE
Résout le problème de délivrance des messages
"""
from typing import List, Dict, Optional, Callable, Set
from collections import defaultdict
from .base import Message, BaseAgent
from loguru import logger


class MessageBusSync:
    """MessageBus synchrone - sans threading pour debug"""
    
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.subscribers: Dict[str, Set[str]] = defaultdict(set)
        self.message_history: List[Message] = []
        
        # Statistiques
        self.stats = {
            "messages_sent": 0,
            "messages_delivered": 0, 
            "messages_failed": 0
        }
        
    def register_agent(self, agent: BaseAgent):
        """Enregistre un agent sur le bus"""
        self.agents[agent.name] = agent
        logger.info(f"Agent {agent.name} registered on message bus")
        
    def subscribe(self, agent_name: str, message_type: str):
        """Abonne un agent à un type de message"""
        self.subscribers[message_type].add(agent_name)
        logger.debug(f"{agent_name} subscribed to {message_type}")
        
    def publish(self, message: Message):
        """Publie et traite immédiatement un message (synchrone)"""
        logger.debug(f"Publishing message {message.type} from {message.sender}")
        
        self.stats["messages_sent"] += 1
        self.message_history.append(message)
        
        # Délivrer immédiatement
        delivered = self._deliver_message(message)
        
        if delivered:
            logger.debug(f"Message delivered successfully")
            # Traiter immédiatement les réponses
            self._process_all_inboxes()
        else:
            logger.warning(f"Message delivery failed")
            
    def _deliver_message(self, message: Message) -> bool:
        """Délivre un message aux destinataires"""
        delivered = False
        
        # Message direct
        if message.recipient:
            if message.recipient in self.agents:
                self.agents[message.recipient].receive_message(message)
                self.stats["messages_delivered"] += 1
                delivered = True
                logger.debug(f"Direct message delivered to {message.recipient}")
            else:
                logger.warning(f"Recipient {message.recipient} not found")
                self.stats["messages_failed"] += 1
                
        # Broadcast aux abonnés
        else:
            subscribers = self.subscribers.get(message.type, set())
            for subscriber in subscribers:
                if subscriber in self.agents and subscriber != message.sender:
                    self.agents[subscriber].receive_message(message)
                    delivered = True
                    self.stats["messages_delivered"] += 1
                    logger.debug(f"Broadcast delivered to {subscriber}")
                    
        return delivered
        
    def _process_all_inboxes(self):
        """Traite tous les messages en attente dans les inboxes"""
        max_iterations = 10  # Éviter boucles infinies
        iteration = 0
        
        while iteration < max_iterations:
            messages_processed = False
            iteration += 1
            
            # Traiter chaque agent
            for agent in self.agents.values():
                while agent.inbox:
                    message = agent.inbox.pop(0)
                    logger.debug(f"Processing message {message.type} for {agent.name}")
                    
                    try:
                        response = agent.process_message(message)
                        messages_processed = True
                        
                        if response:
                            logger.debug(f"{agent.name} generated response: {response.type}")
                            # Publier la réponse récursivement
                            self.publish(response)
                            
                    except Exception as e:
                        logger.error(f"Error processing message for {agent.name}: {e}")
                        self.stats["messages_failed"] += 1
                        
            # Si aucun message traité, arrêter
            if not messages_processed:
                break
                
        if iteration >= max_iterations:
            logger.warning("Max iterations reached in message processing")
            
    def process_agent_messages(self):
        """Méthode pour compatibilité - traite immédiatement"""
        self._process_all_inboxes()
        
    def get_stats(self) -> Dict[str, any]:
        """Retourne les statistiques du bus"""
        return {
            **self.stats,
            "agents_count": len(self.agents),
            "queue_size": 0,  # Pas de queue en mode synchrone
            "history_size": len(self.message_history)
        }
        
    def start(self):
        """Start - pas nécessaire en mode synchrone"""
        logger.info("MessageBus (sync) started")
        
    def stop(self):
        """Stop - pas nécessaire en mode synchrone"""
        logger.info("MessageBus (sync) stopped")