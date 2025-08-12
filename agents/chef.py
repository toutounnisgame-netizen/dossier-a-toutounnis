# -*- coding: utf-8 -*-
"""
Chef Agent for ALMAA v2.0 - FIXED OLLAMA VERSION
CEO level agent that handles high-level decisions
"""
from core.base import BaseAgent, Message
from typing import Optional, Dict, Any
from core.ollama_client import generate  # Use fixed client
import json
from loguru import logger


class AgentChef(BaseAgent):
    """Agent Chef - CEO level agent for strategic decisions"""
    
    def __init__(self):
        super().__init__("Chef", "CEO")
        
        self.prompt_template = """
Tu es le Chef (CEO) d'une organisation d'agents IA.

Demande de l'utilisateur: {user_request}

Ton rôle:
1. Comprendre la demande de l'utilisateur
2. Évaluer la complexité et les enjeux
3. Décider si tu traites directement ou délègues
4. Si délégation: identifier le bon agent et les informations nécessaires

Réponds en JSON:
{{
    "compréhension": "reformulation claire de la demande",
    "complexité": "simple|moyenne|complexe",
    "type_tache": "développement|analyse|recherche|général",
    "enjeux": "faibles|moyens|élevés",
    "décision": "traiter_directement|déléguer",
    "agent_cible": "ChefProjet|Developer1|null si traitement direct",
    "priorité": 1-10,
    "instructions_spéciales": "instructions pour l'agent cible ou null"
}}
"""
        
    def process_message(self, message: Message) -> Optional[Message]:
        """Process messages directed to Chef"""
        if message.type == "REQUEST":
            return self.handle_request(message)
        elif message.type == "TASK_RESULT":
            return self.handle_task_result(message)
        else:
            # Default handler for unknown types
            logger.warning(f"Chef: No handler for message type {message.type}")
            return Message(
                sender=self.name,
                recipient=message.sender,
                type="RESPONSE",
                content={"message": f"Je ne sais pas traiter le message de type {message.type}"}
            )
        
    def handle_request(self, message: Message) -> Optional[Message]:
        """Handle user requests"""
        if message.sender != "User":
            return None
            
        user_request = message.content.get("request", "")
        logger.info(f"Chef processing user request: {user_request[:50]}...")
        
        # Analyze request with LLM
        analysis = self.think({"user_request": user_request})
        
        if not analysis:
            # Fallback analysis
            analysis = {
                "compréhension": user_request,
                "complexité": "simple",
                "type_tache": "général",
                "enjeux": "faibles",
                "décision": "traiter_directement",
                "agent_cible": None,
                "priorité": 5,
                "instructions_spéciales": None
            }
            
        # Decide how to handle
        if analysis.get("décision") == "déléguer":
            return self._delegate_task(analysis, message)
        else:
            return self._handle_directly(analysis, message)
        
    def think(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze context with LLM"""
        try:
            prompt = self.prompt_template.format(**context)
            
            response = generate(
                model="solar:10.7b",
                prompt=prompt,
                format="json",
                options={
                    "temperature": 0.7,
                    "num_predict": 512
                }
            )
            
            analysis = json.loads(response["response"])
            logger.debug(f"Chef analysis: {analysis.get('décision', 'unknown')}")
            return analysis
            
        except Exception as e:
            logger.error(f"Chef thinking error: {e}")
            return None
            
    def _delegate_task(self, analysis: Dict[str, Any], original_message: Message) -> Message:
        """Delegate task to appropriate agent"""
        target_agent = analysis.get("agent_cible", "ChefProjet")
        priority = self._calculate_priority(analysis)
        
        return Message(
            sender=self.name,
            recipient=target_agent,
            type="TASK_ASSIGNMENT",
            priority=priority,
            content={
                "task": original_message.content["request"],
                "analysis": analysis,
                "original_sender": original_message.sender,
                "instructions": analysis.get("instructions_spéciales")
            }
        )
        
    def _handle_directly(self, analysis: Dict[str, Any], original_message: Message) -> Message:
        """Handle task directly"""
        logger.info("Chef handling directly")
        
        # Simple direct response
        task_type = analysis.get("type_tache", "général")
        user_request = original_message.content.get("request", "")
        
        if "bonjour" in user_request.lower() or "hello" in user_request.lower():
            response_text = "Bonjour ! Je suis le Chef d'ALMAA Phase 2. Comment puis-je vous aider aujourd'hui ?"
        else:
            response_text = f"J'ai bien reçu votre demande concernant: {analysis.get('compréhension', user_request)}. Je m'en occupe personnellement."
        
        return Message(
            sender=self.name,
            recipient=original_message.sender,
            type="RESPONSE",
            content={
                "status": "handled_directly",
                "message": response_text,
                "analysis": analysis
            }
        )
        
    def _calculate_priority(self, analysis: Dict[str, Any]) -> int:
        """Calculate task priority"""
        base_priority = analysis.get("priorité", 5)
        complexity = analysis.get("complexité", "simple")
        stakes = analysis.get("enjeux", "faibles")
        
        # Adjust based on complexity and stakes
        if complexity == "complexe":
            base_priority += 2
        elif complexity == "moyenne":
            base_priority += 1
            
        if stakes == "élevés":
            base_priority += 2
        elif stakes == "moyens":
            base_priority += 1
            
        return min(base_priority, 10)
        
    def handle_task_result(self, message: Message) -> Optional[Message]:
        """Handle task completion results"""
        result = message.content
        original_sender = result.get("original_sender", "User")
        
        # Forward result to original requester
        return Message(
            sender=self.name,
            recipient=original_sender,
            type="RESPONSE",
            content={
                "status": "completed",
                "message": "Tâche terminée par mon équipe.",
                "result": result,
                "completed_by": message.sender
            }
        )
