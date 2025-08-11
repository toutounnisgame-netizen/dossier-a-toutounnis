# -*- coding: utf-8 -*-
"""
User Listener for ALMAA v2.0
Simple agent to receive messages for the user
"""
from core.base import BaseAgent, Message
from typing import Optional
from loguru import logger


class UserListener(BaseAgent):
    """Agent that represents the user in the system"""
    
    def __init__(self):
        super().__init__("User", "Listener")
        
    def process_message(self, message: Message) -> Optional[Message]:
        """Simply receive messages addressed to user"""
        # User agent doesn't process messages, just receives them
        logger.debug(f"User received: {message.type} from {message.sender}")
        return None
        
    def think(self, context: dict) -> dict:
        """User doesn't think in the system"""
        return {"status": "listening"}