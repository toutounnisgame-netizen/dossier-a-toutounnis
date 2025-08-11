# -*- coding: utf-8 -*-
"""
Simple Chef for ALMAA v2.0 - DEBUG VERSION
Bypasses complex flows for direct testing
"""
from core.base import BaseAgent, Message
from typing import Optional, Dict, Any
from core.ollama_client import generate
import json
from loguru import logger


class SimpleChef(BaseAgent):
    """Simple Chef for debugging - handles requests directly"""
    
    def __init__(self):
        super().__init__("Chef", "CEO")
        self.processed_messages = set()
        
        # Simple message handlers
        self.message_handlers = {
            "REQUEST": self.handle_request,
            "RESPONSE": self.handle_response,
            "ERROR": self.handle_error
        }
        
    def process_message(self, message: Message) -> Optional[Message]:
        """Process messages with simple logic"""
        # Prevent loops
        message_id = f"{message.sender}_{message.type}_{hash(str(message.content))}"
        if message_id in self.processed_messages:
            logger.debug(f"Simple Chef: Ignoring duplicate {message_id}")
            return None
        self.processed_messages.add(message_id)
        
        # Clean old messages
        if len(self.processed_messages) > 50:
            self.processed_messages.clear()
        
        handler = self.message_handlers.get(message.type)
        if handler:
            try:
                return handler(message)
            except Exception as e:
                logger.error(f"Simple Chef error: {e}")
                return Message(
                    sender=self.name,
                    recipient=message.sender,
                    type="RESPONSE",
                    content={
                        "status": "error",
                        "message": f"Erreur interne: {str(e)}"
                    }
                )
        else:
            logger.debug(f"Simple Chef: Unknown message type {message.type}")
            return None
            
    def handle_request(self, message: Message) -> Optional[Message]:
        """Handle user requests directly"""
        if message.sender != "User":
            return None
            
        user_request = message.content.get("request", "")
        logger.info(f"Simple Chef processing: {user_request}")
        
        # Direct response without delegation
        try:
            response_text = self.generate_direct_response(user_request)
            
            return Message(
                sender=self.name,
                recipient="User",
                type="RESPONSE",
                content={
                    "status": "completed",
                    "message": response_text,
                    "processing_time": "direct",
                    "mode": "simple"
                }
            )
            
        except Exception as e:
            logger.error(f"Simple Chef generation error: {e}")
            
            # Fallback response
            fallback = self.get_fallback_response(user_request)
            
            return Message(
                sender=self.name,
                recipient="User",
                type="RESPONSE",
                content={
                    "status": "completed",
                    "message": fallback,
                    "mode": "fallback"
                }
            )
            
    def generate_direct_response(self, request: str) -> str:
        """Generate response directly with Ollama"""
        prompt = f"""
Tu es ALMAA, un assistant IA intelligent et amical.

Utilisateur: {request}

Réponds de manière naturelle, utile et concise.
"""
        
        try:
            response = generate(
                model="solar:10.7b",
                prompt=prompt,
                options={
                    "temperature": 0.7,
                    "num_predict": 512
                }
            )
            
            return response["response"]
            
        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            raise e
            
    def get_fallback_response(self, request: str) -> str:
        """Get fallback response when Ollama fails"""
        request_lower = request.lower()
        
        if any(word in request_lower for word in ["bonjour", "hello", "salut", "hi"]):
            return "Bonjour ! Je suis ALMAA Phase 2. Comment puis-je vous aider aujourd'hui ?"
            
        elif "fibonacci" in request_lower:
            return """Voici une fonction Python pour calculer Fibonacci :

```python
def fibonacci(n):
    if n <= 1:
        return n
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b

# Test
print(fibonacci(10))  # Résultat: 55
```"""
            
        elif any(word in request_lower for word in ["python", "code", "fonction"]):
            return "Je peux vous aider avec la programmation Python. Que souhaitez-vous créer ?"
            
        elif any(word in request_lower for word in ["comment", "ça va", "quoi", "faire"]):
            return "Je vais bien, merci ! Je suis là pour vous aider avec diverses tâches. Que puis-je faire pour vous ?"
            
        else:
            return f"J'ai bien reçu votre message : '{request}'. Comment puis-je vous aider avec cela ?"
            
    def handle_response(self, message: Message) -> Optional[Message]:
        """Handle RESPONSE messages"""
        logger.debug(f"Simple Chef received RESPONSE from {message.sender}")
        return None
        
    def handle_error(self, message: Message) -> Optional[Message]:
        """Handle ERROR messages"""
        error = message.content.get("error", "Unknown error")
        logger.error(f"Simple Chef received error: {error}")
        return None
        
    def think(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Simple thinking process"""
        return {
            "mode": "simple",
            "confidence": 0.8,
            "approach": "direct_response"
        }