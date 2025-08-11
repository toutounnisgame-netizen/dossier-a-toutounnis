# -*- coding: utf-8 -*-
"""
Philosophe Observer Agent for ALMAA v2.0 - FIXED VERSION
Observes all interactions and provides insights
"""
from core.base import BaseAgent, Message
from typing import Optional, List, Dict, Any
from datetime import datetime
from loguru import logger


class AgentPhilosophe(BaseAgent):
    """Agent philosophe qui observe et analyse les interactions"""
    
    def __init__(self):
        super().__init__("Philosophe", "Observer")
        self.observations = []
        self.insights = []
        self.observation_buffer = []
        self.insight_threshold = 0.7
        self.max_buffer_size = 100
        
    def process_message(self, message: Message) -> Optional[Message]:
        """Process messages directed to Philosophe - REQUIRED METHOD"""
        if message.type == "REQUEST_INSIGHTS":
            return self._provide_insights(message)
        elif message.type == "OBSERVE":
            # Manually requested observation
            self.observe_message(message)
            return None
        else:
            logger.warning(f"Philosophe: No handler for message type {message.type}")
            return Message(
                sender=self.name,
                recipient=message.sender,
                type="RESPONSE",
                content={"message": f"Je ne traite que les demandes d'insights. Type reçu: {message.type}"}
            )
        
    def observe_message(self, message: Message):
        """Observe a message passing through the system"""
        observation = {
            "timestamp": datetime.now(),
            "sender": message.sender,
            "recipient": message.recipient,
            "type": message.type,
            "content_summary": self._summarize_content(message.content)
        }
        
        self.observation_buffer.append(observation)
        self.observations.append(observation)  # Keep full history
        
        # Analyze periodically
        if len(self.observation_buffer) >= 10:
            self._analyze_observations()
            
    def _summarize_content(self, content: Any) -> str:
        """Create a brief summary of message content"""
        if isinstance(content, dict):
            keys = list(content.keys())[:3]
            return f"Dict with keys: {keys}..."
        elif isinstance(content, str):
            return content[:50] + "..." if len(content) > 50 else content
        else:
            return f"Type: {type(content).__name__}"
            
    def _analyze_observations(self):
        """Analyze recent observations for patterns"""
        if not self.observation_buffer:
            return
            
        # Simple pattern detection
        message_types = [obs["type"] for obs in self.observation_buffer]
        
        # Check for debate patterns
        if message_types.count("DEBATE_INVITATION") > 2:
            self.insights.append({
                "type": "pattern",
                "insight": "Augmentation des débats - système en mode délibératif",
                "confidence": 0.8,
                "timestamp": datetime.now()
            })
            
        # Check for error patterns
        error_count = message_types.count("ERROR")
        if error_count > len(self.observation_buffer) * 0.3:
            self.insights.append({
                "type": "warning",
                "insight": f"Taux d'erreur élevé: {error_count}/{len(self.observation_buffer)}",
                "confidence": 0.9,
                "timestamp": datetime.now()
            })
            
        # Check for task completion patterns
        task_results = message_types.count("TASK_RESULT")
        if task_results > 5:
            self.insights.append({
                "type": "productivity",
                "insight": f"Système productif: {task_results} tâches complétées récemment",
                "confidence": 0.7,
                "timestamp": datetime.now()
            })
            
        # Memory usage patterns
        memory_ops = sum(1 for t in message_types if "MEMORY" in t)
        if memory_ops > 3:
            self.insights.append({
                "type": "learning",
                "insight": f"Activité mémoire intense: {memory_ops} opérations mémoire",
                "confidence": 0.8,
                "timestamp": datetime.now()
            })
            
        # Clear buffer (keep only recent)
        self.observation_buffer = self.observation_buffer[-50:]  # Keep last 50
        
    def _provide_insights(self, message: Message) -> Message:
        """Provide philosophical insights about the system"""
        recent_insights = self.insights[-5:] if self.insights else []
        
        # Add timestamps to insights
        formatted_insights = []
        for insight in recent_insights:
            formatted_insights.append({
                "type": insight["type"],
                "message": insight["insight"],
                "confidence": insight["confidence"],
                "age_minutes": (datetime.now() - insight.get("timestamp", datetime.now())).total_seconds() / 60
            })
        
        return Message(
            sender=self.name,
            recipient=message.sender,
            type="INSIGHTS_REPORT",
            content={
                "observations_count": len(self.observations),
                "recent_insights": formatted_insights,
                "system_health": self._assess_system_health(),
                "philosophical_note": self._generate_wisdom()
            }
        )
        
    def _assess_system_health(self) -> str:
        """Simple system health assessment"""
        if not self.observation_buffer:
            return "Insufficient data"
            
        # Calculate error rate
        error_types = ["ERROR", "FAILED", "TIMEOUT"]
        error_count = sum(1 for obs in self.observation_buffer if obs["type"] in error_types)
        error_rate = error_count / len(self.observation_buffer) if self.observation_buffer else 0
        
        # Calculate activity level
        activity_level = min(len(self.observation_buffer) / 20, 1.0)  # Normalize to 20 messages
        
        if error_rate < 0.1 and activity_level > 0.5:
            return "Excellent - Système performant et actif"
        elif error_rate < 0.3 and activity_level > 0.3:
            return "Good - Fonctionnement stable"
        elif error_rate < 0.5:
            return "Fair - Quelques problèmes détectés"
        else:
            return "Poor - Nombreuses erreurs système"
            
    def _generate_wisdom(self) -> str:
        """Generate philosophical wisdom based on observations"""
        if not self.observations:
            return "Le silence précède la sagesse."
            
        # Simple wisdom generation based on patterns
        total_obs = len(self.observations)
        
        if total_obs < 10:
            return "Chaque observation est une graine de compréhension."
        elif total_obs < 50:
            return "L'intelligence collective émerge de la coordination des esprits individuels."
        elif total_obs < 100:
            return "La complexité naît de la simplicité orchestrée."
        else:
            return "Dans la danse des agents, je vois l'émergence d'une conscience distribuée."
            
    def think(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Philosophical reflection on context"""
        return {
            "reflection": "Observing the dance of artificial minds",
            "patterns_detected": len(self.insights),
            "wisdom": self._generate_wisdom(),
            "observations": len(self.observations),
            "recent_activity": len(self.observation_buffer)
        }
        
    def get_system_report(self) -> Dict[str, Any]:
        """Generate a comprehensive system report"""
        if not self.observations:
            return {"status": "No observations yet"}
            
        # Analyze message types
        message_types = [obs["type"] for obs in self.observations]
        type_counts = {}
        for msg_type in message_types:
            type_counts[msg_type] = type_counts.get(msg_type, 0) + 1
            
        # Most active agents
        senders = [obs["sender"] for obs in self.observations]
        sender_counts = {}
        for sender in senders:
            sender_counts[sender] = sender_counts.get(sender, 0) + 1
            
        return {
            "total_observations": len(self.observations),
            "message_types": dict(sorted(type_counts.items(), key=lambda x: x[1], reverse=True)[:10]),
            "most_active_agents": dict(sorted(sender_counts.items(), key=lambda x: x[1], reverse=True)[:5]),
            "recent_insights": len(self.insights),
            "system_health": self._assess_system_health(),
            "philosophical_wisdom": self._generate_wisdom()
        }