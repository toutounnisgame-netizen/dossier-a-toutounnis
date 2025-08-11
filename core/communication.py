from typing import List, Dict, Optional, Callable, Set
from collections import defaultdict
import threading
import time
from queue import Queue, Empty
from .base import Message, BaseAgent
from loguru import logger

class MessageBus:
    """Bus de messages pour communication inter-agents"""

    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.subscribers: Dict[str, Set[str]] = defaultdict(set)
        self.message_queue = Queue()
        self.message_history: List[Message] = []
        self.handlers: Dict[str, List[Callable]] = defaultdict(list)
        self.running = False
        self.processing_thread = None
        self._lock = threading.Lock()

        # Statistiques
        self.stats = {
            "messages_sent": 0,
            "messages_delivered": 0,
            "messages_failed": 0
        }

    def register_agent(self, agent: BaseAgent):
        """Enregistre un agent sur le bus"""
        with self._lock:
            self.agents[agent.name] = agent
            logger.info(f"Agent {agent.name} registered on message bus")

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

    def unsubscribe(self, agent_name: str, message_type: str):
        """Désabonne un agent d'un type de message"""
        with self._lock:
            self.subscribers[message_type].discard(agent_name)

    def publish(self, message: Message):
        """Publie un message sur le bus"""
        self.message_queue.put(message)
        self.stats["messages_sent"] += 1
        logger.debug(f"Message {message.type} published by {message.sender}")

    def add_handler(self, message_type: str, handler: Callable):
        """Ajoute un handler global pour un type de message"""
        self.handlers[message_type].append(handler)

    def start(self):
        """Démarre le traitement des messages"""
        if not self.running:
            self.running = True
            self.processing_thread = threading.Thread(target=self._process_loop)
            self.processing_thread.daemon = True
            self.processing_thread.start()
            logger.info("Message bus started")

    def stop(self):
        """Arrête le traitement des messages"""
        self.running = False
        if self.processing_thread:
            self.processing_thread.join(timeout=5)
        logger.info("Message bus stopped")

    def _process_loop(self):
        """Boucle de traitement des messages"""
        while self.running:
            try:
                message = self.message_queue.get(timeout=0.1)
                self._deliver_message(message)
                self.message_history.append(message)

                # Limiter l'historique
                if len(self.message_history) > 1000:
                    self.message_history = self.message_history[-500:]

            except Empty:
                continue
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                self.stats["messages_failed"] += 1

    def _deliver_message(self, message: Message):
        """Délivre un message aux destinataires"""
        delivered = False

        # Message direct
        if message.recipient:
            if message.recipient in self.agents:
                self.agents[message.recipient].receive_message(message)
                delivered = True
                self.stats["messages_delivered"] += 1
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

            if delivered:
                self.stats["messages_delivered"] += len(subscribers)

        # Handlers globaux
        for handler in self.handlers.get(message.type, []):
            try:
                handler(message)
            except Exception as e:
                logger.error(f"Handler error: {e}")

    def process_agent_messages(self):
        """Traite les messages en attente des agents"""
        with self._lock:
            for agent in self.agents.values():
                # NE PAS traiter les messages de l'agent User !
                if agent.name == "User":
                    continue

                # Traiter inbox
                while agent.inbox:
                    message = agent.inbox.pop(0)
                    try:
                        response = agent.process_message(message)
                        if response:
                            # IMPORTANT: Publier la réponse sur le bus!
                            self.publish(response)
                    except Exception as e:
                        logger.error(f"Agent {agent.name} error processing message: {e}")

                # Envoyer outbox
                while agent.outbox:
                    message = agent.outbox.pop(0)
                    self.publish(message)

    def get_stats(self) -> Dict[str, any]:
        """Retourne les statistiques du bus"""
        return {
            **self.stats,
            "agents_count": len(self.agents),
            "queue_size": self.message_queue.qsize(),
            "history_size": len(self.message_history)
        }
