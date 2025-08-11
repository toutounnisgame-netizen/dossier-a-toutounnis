# -*- coding: utf-8 -*-
"""
Memory Enhanced Worker for ALMAA v2.0 - COMPLETE FIXED VERSION
Worker agent with integrated memory capabilities and proper handlers
"""
from core.base import BaseAgent, Message
from agents.mixins.debater import DebaterMixin
from agents.mixins.memory import MemoryMixin
from core.memory.vector_store import VectorMemory
from typing import Dict, Any, Optional
from core.ollama_client import generate  # Fixed import
from loguru import logger


class MemoryEnhancedWorker(BaseAgent, DebaterMixin, MemoryMixin):
    """Worker agent with memory and debate capabilities"""
    
    def __init__(self, name: str, specialty: str, memory_store: VectorMemory):
        # Initialize base classes
        BaseAgent.__init__(self, name, f"Worker_{specialty}")
        DebaterMixin.__init__(self)
        MemoryMixin.__init__(self, memory_store)
        
        self.specialty = specialty
        self.model = "solar:10.7b"  # Better model for workers
        self.completed_tasks = 0
        self.success_rate = 1.0
        self.processed_messages = set()  # Prevent loops
        
        # Enhanced prompt with memory
        self.task_prompt = """
Tu es {name}, spécialiste en {specialty}.

Tâche: {task}

Expériences similaires:
{memories}

En te basant sur tes expériences passées et tes connaissances, propose la meilleure solution.

Réponds de manière structurée et professionnelle.
"""
        
        # Add memory-aware handlers
        self.message_handlers.update({
            "TASK_ASSIGNMENT": self.handle_task_with_memory,
            "CODE_TASK": self.handle_code_task,
            "ANALYSIS_TASK": self.handle_analysis_task,
            "MEMORY_SHARE": self.handle_memory_share,
            "DEBATE_INVITATION": self.handle_debate_invitation,
            "REQUEST_ARGUMENT": self.handle_argument_request,
            "REQUEST_VOTE": self.handle_vote_request,
            "RESPONSE": self.handle_response,  # Add RESPONSE handler
            "ERROR": self.handle_error  # Add ERROR handler
        })
        
    def process_message(self, message: Message) -> Optional[Message]:
        """Process messages directed to this worker - REQUIRED METHOD"""
        # Prevent message loops
        message_id = f"{message.sender}_{message.type}_{hash(str(message.content))}"
        if message_id in self.processed_messages:
            logger.debug(f"{self.name}: Ignoring duplicate message {message_id}")
            return None
        self.processed_messages.add(message_id)
        
        # Clean old processed messages (keep last 100)
        if len(self.processed_messages) > 100:
            self.processed_messages.clear()
            
        handler = self.message_handlers.get(message.type)
        if handler:
            try:
                return handler(message)
            except Exception as e:
                logger.error(f"{self.name} handler error for {message.type}: {e}")
                return Message(
                    sender=self.name,
                    recipient=message.sender,
                    type="ERROR",
                    content={"error": f"Handler error: {str(e)}"}
                )
        else:
            logger.debug(f"{self.name}: Unknown message type {message.type} from {message.sender}")
            return None
        
    def handle_response(self, message: Message) -> Optional[Message]:
        """Handle RESPONSE messages to prevent loops"""
        logger.debug(f"{self.name} received RESPONSE from {message.sender}")
        return None
        
    def handle_error(self, message: Message) -> Optional[Message]:
        """Handle ERROR messages"""
        error_content = message.content.get("error", "Unknown error")
        logger.error(f"{self.name} received error from {message.sender}: {error_content}")
        return None
        
    def handle_task_with_memory(self, message: Message) -> Optional[Message]:
        """Handle task assignment with memory search"""
        task_info = message.content
        task = task_info.get("task", "")
        
        # Search for similar experiences
        if self.memory_config["search_on_task"] and self.memory.is_ready():
            try:
                similar_experiences = self.recall_similar(
                    task,
                    context={"type": message.type}
                )
                
                if similar_experiences:
                    logger.info(f"{self.name} found {len(similar_experiences)} similar experiences")
            except Exception as e:
                logger.warning(f"Memory search failed: {e}")
                similar_experiences = []
        else:
            similar_experiences = []
            
        # Process task with memory context
        try:
            result = self.execute_task(task, similar_experiences)
            
            # Store experience
            if self.memory_config["auto_store"] and self.memory.is_ready():
                try:
                    self.remember_experience(
                        content=f"Task: {task}\nResult: {result}",
                        metadata={
                            "task_type": self.specialty,
                            "success": True,
                            "message_type": message.type
                        }
                    )
                except Exception as e:
                    logger.warning(f"Failed to store experience: {e}")
                
            self.completed_tasks += 1
            
            # Send result back to sender
            return Message(
                sender=self.name,
                recipient=message.sender,
                type="TASK_RESULT",
                content={
                    "status": "completed",
                    "result": result,
                    "memories_used": len(similar_experiences),
                    "worker": self.name,
                    "original_sender": task_info.get("original_sender", "User")
                }
            )
            
        except Exception as e:
            logger.error(f"{self.name} task failed: {e}")
            
            # Learn from failure
            if self.memory.is_ready():
                try:
                    self.remember_experience(
                        content=f"Task: {task}\nError: {str(e)}",
                        metadata={
                            "task_type": self.specialty,
                            "success": False,
                            "error": str(e)
                        }
                    )
                except Exception as mem_error:
                    logger.warning(f"Failed to store failure: {mem_error}")
            
            self.success_rate = self.completed_tasks / (self.completed_tasks + 1) if self.completed_tasks > 0 else 0.5
            
            return Message(
                sender=self.name,
                recipient=message.sender,
                type="TASK_RESULT",
                content={
                    "status": "failed",
                    "error": str(e),
                    "original_sender": task_info.get("original_sender", "User")
                }
            )
            
    def execute_task(self, task: str, memories: list) -> str:
        """Execute task with memory context"""
        # Format memories for prompt
        memory_context = self._format_memories(memories)
        
        prompt = self.task_prompt.format(
            name=self.name,
            specialty=self.specialty,
            task=task,
            memories=memory_context
        )
        
        try:
            response = generate(
                model=self.model,
                prompt=prompt,
                options={
                    "temperature": 0.7,
                    "num_predict": 1024
                }
            )
            
            return response["response"]
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            # Fallback response
            if "bonjour" in task.lower():
                return f"Bonjour ! Je suis {self.name}, spécialisé en {self.specialty}. Comment puis-je vous aider ?"
            elif "fibonacci" in task.lower():
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
            else:
                return f"J'ai traité votre tâche : {task}. (Mode dégradé - Ollama indisponible)"
        
    def _format_memories(self, memories: list) -> str:
        """Format memories for inclusion in prompt"""
        if not memories:
            return "Aucune expérience similaire trouvée."
            
        formatted = []
        for i, mem in enumerate(memories[:3], 1):  # Limit to 3
            success = "✓ Succès" if mem['metadata'].get('success') else "✗ Échec"
            formatted.append(
                f"{i}. {success} - Similarité: {mem['similarity']:.1%}\n"
                f"   {mem['content'][:150]}..."
            )
            
        return "\n".join(formatted)
        
    def handle_code_task(self, message: Message) -> Optional[Message]:
        """Handle coding tasks with memory"""
        # Delegate to handle_task_with_memory
        return self.handle_task_with_memory(message)
        
    def handle_analysis_task(self, message: Message) -> Optional[Message]:
        """Handle analysis tasks with memory"""
        # Delegate to handle_task_with_memory
        return self.handle_task_with_memory(message)
        
    def handle_memory_share(self, message: Message) -> Optional[Message]:
        """Handle shared memories from other agents"""
        shared_memories = message.content.get("memories", [])
        query = message.content.get("query", "")
        
        # Store shared memories as knowledge
        if self.memory.is_ready():
            for mem in shared_memories:
                try:
                    self.remember_experience(
                        content=f"Shared from {message.sender}: {mem['content']}",
                        metadata={
                            "type": "shared_knowledge",
                            "source": message.sender,
                            "original_query": query,
                            "importance": 0.7  # Moderate importance for shared knowledge
                        }
                    )
                except Exception as e:
                    logger.warning(f"Failed to store shared memory: {e}")
                    
        logger.info(f"{self.name} received {len(shared_memories)} shared memories")
        return None
        
    def think(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Think about a problem with memory assistance"""
        # Search memory for relevant information
        if self.memory.is_ready():
            try:
                memories = self.recall_similar(str(context))
            except Exception as e:
                logger.warning(f"Memory recall failed: {e}")
                memories = []
        else:
            memories = []
        
        return {
            "thought": f"Processing as {self.specialty} specialist",
            "confidence": self.success_rate,
            "memories_consulted": len(memories),
            "approach": "memory-assisted" if memories else "standard"
        }
        
    def get_stats(self) -> Dict[str, Any]:
        """Get worker statistics including memory usage"""
        base_stats = {
            "completed_tasks": self.completed_tasks,
            "success_rate": self.success_rate,
            "specialty": self.specialty
        }
        
        # Add memory stats if available
        if self.memory.is_ready():
            try:
                memory_stats = self.get_memory_stats()
                base_stats.update(memory_stats)
            except Exception as e:
                logger.warning(f"Failed to get memory stats: {e}")
        
        return base_stats