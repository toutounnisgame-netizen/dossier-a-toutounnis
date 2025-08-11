from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, Optional, List
from uuid import uuid4
from pydantic import BaseModel, Field
from loguru import logger

class Message(BaseModel):
    """Message de base pour communication inter-agents"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=datetime.now)
    sender: str
    recipient: Optional[str] = None
    type: str  # REQUEST, RESPONSE, BROADCAST, etc.
    priority: int = Field(default=5, ge=1, le=10)
    content: Dict[str, Any] = Field(default_factory=dict)
    thread_id: Optional[str] = None
    requires_ack: bool = False

    def to_json(self) -> str:
        return self.model_dump_json()

    @classmethod
    def from_json(cls, json_str: str) -> 'Message':
        return cls.model_validate_json(json_str)

class BaseAgent(ABC):
    """Classe abstraite pour tous les agents"""

    def __init__(self, name: str, role: str):
        self.id = str(uuid4())
        self.name = name
        self.role = role
        self.inbox: List[Message] = []
        self.outbox: List[Message] = []
        self.state = "idle"
        self.created_at = datetime.now()
        self.message_handlers = {
            "REQUEST": self.handle_request,
            "TASK_ASSIGNMENT": self.handle_task,
            "PING": self.handle_ping
        }
        logger.info(f"Agent {name} ({role}) initialized")

    @abstractmethod
    def process_message(self, message: Message) -> Optional[Message]:
        """Traite un message entrant"""
        pass

    @abstractmethod
    def think(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Processus de réflexion de l'agent"""
        pass

    def handle_request(self, message: Message) -> Optional[Message]:
        """Handler par défaut pour REQUEST"""
        return Message(
            sender=self.name,
            recipient=message.sender,
            type="RESPONSE",
            content={"status": "not_implemented"}
        )

    def handle_task(self, message: Message) -> Optional[Message]:
        """Handler par défaut pour TASK_ASSIGNMENT"""
        return self.handle_request(message)

    def handle_ping(self, message: Message) -> Optional[Message]:
        """Handler pour PING"""
        return Message(
            sender=self.name,
            recipient=message.sender,
            type="PONG",
            content={"status": "alive", "state": self.state}
        )

    def send_message(self, message: Message):
        """Envoie un message"""
        self.outbox.append(message)
        logger.debug(f"{self.name} sending {message.type} to {message.recipient}")

    def receive_message(self, message: Message):
        """Reçoit un message"""
        self.inbox.append(message)
        logger.debug(f"{self.name} received {message.type} from {message.sender}")

    def get_state(self) -> Dict[str, Any]:
        """Retourne l'état actuel de l'agent"""
        return {
            "id": self.id,
            "name": self.name,
            "role": self.role,
            "state": self.state,
            "inbox_count": len(self.inbox),
            "created_at": self.created_at.isoformat()
        }
