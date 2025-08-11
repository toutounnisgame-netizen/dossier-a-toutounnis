# -*- coding: utf-8 -*-
"""
Memory Mixin for ALMAA v2.0
Gives memory capabilities to any agent
"""
from typing import Dict, Any, List, Optional
from core.memory.vector_store import VectorMemory
from datetime import datetime
from loguru import logger


class MemoryMixin:
    """Mixin to give memory capabilities to agents"""
    
    def __init__(self, memory_store: VectorMemory):
        self.memory = memory_store
        
        # Configuration
        self.memory_config = {
            "auto_store": True,  # Automatically store experiences
            "importance_threshold": 0.5,  # Minimum importance to store
            "search_on_task": True,  # Search memory before tasks
            "personal_only": False  # Only search own memories
        }
        
        # Track memory usage
        self.memories_stored = 0
        self.memories_recalled = 0
        
    def remember_experience(self, content: str, metadata: Dict[str, Any]) -> Optional[str]:
        """Store an experience in memory"""
        # Calculate importance if not provided
        if "importance" not in metadata:
            metadata["importance"] = self.calculate_importance(content, metadata)
            
        # Add agent name
        metadata["agent"] = getattr(self, 'name', 'Unknown')
        
        # Store if important enough
        if metadata["importance"] >= self.memory_config["importance_threshold"]:
            doc_id = self.memory.store(
                content=content,
                metadata=metadata,
                collection_name="experiences"
            )
            self.memories_stored += 1
            logger.debug(f"{metadata['agent']} remembered: {doc_id}")
            return doc_id
            
        return None
        
    def recall_similar(self, query: str, context: Optional[Dict] = None) -> List[Dict]:
        """Recall similar experiences from memory"""
        # Enrich query with context
        if context:
            enriched_query = f"{query} Context: {str(context)}"
        else:
            enriched_query = query
            
        # Search filters
        filters = None
        if self.memory_config.get("personal_only"):
            filters = {"agent": getattr(self, 'name', 'Unknown')}
            
        # Search memory
        results = self.memory.search(
            query=enriched_query,
            filters=filters,
            top_k=5
        )
        
        self.memories_recalled += len(results)
        return results
        
    def learn_from_result(self, task: str, result: Any, success: bool):
        """Learn from a task result"""
        content = f"""
Task: {task}
Result: {str(result)[:500]}
Success: {success}
Learning: {self._extract_learning(task, result, success)}
"""
        
        metadata = {
            "type": "task_result",
            "success": success,
            "task_type": self._classify_task(task)
        }
        
        self.remember_experience(content, metadata)
        
    def _extract_learning(self, task: str, result: Any, success: bool) -> str:
        """Extract key learning from result"""
        if success:
            return f"Successfully completed by {getattr(self, 'name', 'agent')}"
        else:
            return f"Failed - needs different approach"
            
    def _classify_task(self, task: str) -> str:
        """Classify task type"""
        task_lower = task.lower()
        
        if any(word in task_lower for word in ["code", "function", "debug", "fix"]):
            return "coding"
        elif any(word in task_lower for word in ["analyze", "review", "evaluate"]):
            return "analysis"
        elif any(word in task_lower for word in ["search", "find", "research"]):
            return "research"
        else:
            return "general"
            
    def calculate_importance(self, content: str, metadata: Dict[str, Any]) -> float:
        """Calculate importance of a memory"""
        factors = {
            "uniqueness": self._calculate_uniqueness(content),
            "success": 1.0 if metadata.get("success", False) else 0.3,
            "complexity": min(len(content) / 1000, 1.0),  # Longer = more complex
            "recency": 1.0  # Will decay over time
        }
        
        # Weighted average
        weights = {
            "uniqueness": 0.4,
            "success": 0.3,
            "complexity": 0.2,
            "recency": 0.1
        }
        
        importance = sum(factors[f] * weights[f] for f in factors)
        return min(1.0, max(0.0, importance))
        
    def _calculate_uniqueness(self, content: str) -> float:
        """Calculate uniqueness relative to existing memories"""
        # Search for similar content
        similar = self.memory.search(content, top_k=3)
        
        if not similar:
            return 1.0
            
        # Average similarity of top results
        avg_similarity = sum(r['similarity'] for r in similar) / len(similar)
        
        # More unique = less similar to existing
        uniqueness = 1.0 - avg_similarity
        return max(0.0, uniqueness)
        
    def share_memory(self, query: str, recipient: str) -> List[Dict]:
        """Share relevant memories with another agent"""
        memories = self.recall_similar(query)
        
        if memories and hasattr(self, 'send_message'):
            # Send memories to recipient
            self.send_message({
                "sender": getattr(self, 'name', 'Unknown'),
                "recipient": recipient,
                "type": "MEMORY_SHARE",
                "content": {
                    "query": query,
                    "memories": memories[:3]  # Share top 3
                }
            })
            
        return memories
        
    def forget_old_memories(self, days: int = 30):
        """Forget memories older than specified days"""
        criteria = {
            "older_than": days,
            "importance_below": 0.3,  # Only forget unimportant ones
            "agent": getattr(self, 'name', 'Unknown')  # Only own memories
        }
        
        forgotten = self.memory.forget(criteria)
        logger.info(f"{getattr(self, 'name', 'Agent')} forgot {forgotten} old memories")
        
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get statistics about memory usage"""
        return {
            "memories_stored": self.memories_stored,
            "memories_recalled": self.memories_recalled,
            "recall_rate": self.memories_recalled / max(1, self.memories_stored),
            "agent": getattr(self, 'name', 'Unknown')
        }