# -*- coding: utf-8 -*-
"""
Memory Compressor for ALMAA v2.0
Compresses similar memories to save space
"""
from typing import List, Dict, Any, Optional
from core.memory.vector_store import VectorMemory
from sklearn.cluster import DBSCAN
import numpy as np
from datetime import datetime
import ollama
import json
from loguru import logger


class MemoryCompressor:
    """Handles compression of similar memories"""
    
    def __init__(self, vector_memory: VectorMemory):
        self.memory = vector_memory
        self.compression_threshold = 0.85  # Similarity threshold for compression
        self.min_cluster_size = 2
        
    def compress_memories(self, collection_name: str = "experiences", 
                         target_reduction: float = 0.5) -> int:
        """Compress similar memories in a collection"""
        # Get collection
        collection = self.memory.collections.get(collection_name)
        if not collection:
            return 0
            
        # Get all documents (limited for performance)
        all_docs = collection.get(limit=1000)
        
        if len(all_docs['ids']) < 10:
            logger.info("Not enough memories to compress")
            return 0
            
        # Extract embeddings
        embeddings = np.array(all_docs['embeddings'])
        
        # Cluster similar memories using DBSCAN
        clustering = DBSCAN(
            eps=1-self.compression_threshold,  # Distance threshold
            min_samples=self.min_cluster_size,
            metric='cosine'
        )
        
        clusters = clustering.fit_predict(embeddings)
        
        # Compress each cluster
        compressed_count = 0
        
        for cluster_id in set(clusters):
            if cluster_id == -1:  # Noise, not a cluster
                continue
                
            # Get indices of memories in this cluster
            cluster_indices = np.where(clusters == cluster_id)[0]
            
            if len(cluster_indices) >= self.min_cluster_size:
                # Compress this cluster
                compressed = self._compress_cluster(
                    documents=[all_docs['documents'][i] for i in cluster_indices],
                    metadatas=[all_docs['metadatas'][i] for i in cluster_indices],
                    ids=[all_docs['ids'][i] for i in cluster_indices]
                )
                
                if compressed:
                    compressed_count += len(cluster_indices) - 1  # -1 for the summary
                    
        logger.info(f"Compressed {compressed_count} memories")
        return compressed_count
        
    def _compress_cluster(self, documents: List[str], metadatas: List[Dict], 
                         ids: List[str]) -> Optional[str]:
        """Compress a cluster of similar documents"""
        if len(documents) < self.min_cluster_size:
            return None
            
        # Create summary prompt
        summary_prompt = f"""
Voici {len(documents)} expériences similaires:

{chr(10).join([f"{i+1}. {doc[:200]}..." for i, doc in enumerate(documents)])}

Crée un résumé concis qui capture l'essence commune et les variations importantes.
"""
        
        try:
            # Generate summary with LLM
            response = ollama.generate(
                model="solar:10.7b",
                prompt=summary_prompt,
                options={
                    "temperature": 0.3,
                    "num_predict": 500
                }
            )
            
            summary = response["response"]
            
            # Create combined metadata
            combined_metadata = {
                "type": "compressed",
                "original_count": len(documents),
                "original_ids": ids,
                "compression_date": datetime.now().isoformat(),
                "importance": max(m.get("importance", 0.5) for m in metadatas),
                "time_range": (
                    min(m.get("timestamp", "") for m in metadatas),
                    max(m.get("timestamp", "") for m in metadatas)
                )
            }
            
            # Store compressed summary
            summary_id = self.memory.store(summary, combined_metadata)
            
            # Delete original memories
            for doc_id in ids:
                collection_name = doc_id.split('_')[0]
                self.memory.collections[collection_name].delete(ids=[doc_id])
                
            return summary_id
            
        except Exception as e:
            logger.error(f"Compression failed: {e}")
            return None
            
    def find_redundant_memories(self, similarity_threshold: float = 0.9) -> List[List[str]]:
        """Find groups of highly redundant memories"""
        redundant_groups = []
        
        for collection_name, collection in self.memory.collections.items():
            # Get all documents
            all_docs = collection.get(limit=500)
            
            if len(all_docs['ids']) < 2:
                continue
                
            # Compare all pairs
            for i in range(len(all_docs['ids'])):
                for j in range(i+1, len(all_docs['ids'])):
                    # Calculate similarity
                    embedding1 = np.array(all_docs['embeddings'][i])
                    embedding2 = np.array(all_docs['embeddings'][j])
                    
                    similarity = 1 - np.dot(embedding1, embedding2) / (
                        np.linalg.norm(embedding1) * np.linalg.norm(embedding2)
                    )
                    
                    if similarity >= similarity_threshold:
                        redundant_groups.append([
                            all_docs['ids'][i],
                            all_docs['ids'][j]
                        ])
                        
        return redundant_groups
        
    def auto_compress(self, max_memory_size: int = 100000) -> Dict[str, int]:
        """Automatically compress when memory exceeds size limit"""
        stats = self.memory.get_stats()
        total_memories = stats['total_memories']
        
        compression_results = {}
        
        if total_memories > max_memory_size:
            logger.info(f"Memory size ({total_memories}) exceeds limit ({max_memory_size})")
            
            # Compress each collection proportionally
            for collection_name, count in stats['collections'].items():
                if count > 100:  # Only compress larger collections
                    compressed = self.compress_memories(
                        collection_name,
                        target_reduction=0.5
                    )
                    compression_results[collection_name] = compressed
                    
        return compression_results