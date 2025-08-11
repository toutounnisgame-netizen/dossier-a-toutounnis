# -*- coding: utf-8 -*-
"""
Vector Memory Store for ALMAA v2.0 - WINDOWS FIXED VERSION
Uses ChromaDB for semantic memory storage and retrieval
"""
import chromadb
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Optional
import numpy as np
from datetime import datetime
import time
import os
from pathlib import Path
from loguru import logger


class VectorMemory:
    """Manages vector storage and retrieval using ChromaDB"""
    
    def __init__(self, persist_dir: str = "./data/memory/vectors"):
        """Initialize vector memory with ChromaDB"""
        try:
            # Ensure directory exists and use absolute path for Windows
            persist_path = Path(persist_dir).resolve()
            persist_path.mkdir(parents=True, exist_ok=True)
            
            # ChromaDB setup - Fixed for Windows
            self.client = chromadb.PersistentClient(path=str(persist_path))
            
            # Embedding model
            logger.info("Loading sentence transformer model...")
            self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
            
            # Create collections (including "code" collection)
            logger.info("Initializing memory collections...")
            self.collections = {
                "experiences": self._get_or_create_collection("experiences"),
                "knowledge": self._get_or_create_collection("knowledge"),
                "conversations": self._get_or_create_collection("conversations"),
                "decisions": self._get_or_create_collection("decisions"),
                "code": self._get_or_create_collection("code")  # Added for code snippets
            }
            
            # Configuration
            self.max_results = 10
            self.similarity_threshold = 0.7
            
            # Filter out None collections
            active_collections = {k: v for k, v in self.collections.items() if v is not None}
            
            logger.info(f"Initialized VectorMemory with {len(active_collections)} collections")
            
        except Exception as e:
            logger.error(f"Failed to initialize VectorMemory: {e}")
            # Fallback initialization
            self.client = None
            self.collections = {}
            self.encoder = None
        
    def _get_or_create_collection(self, name: str):
        """Get or create a collection"""
        try:
            return self.client.get_or_create_collection(name)
        except Exception as e:
            logger.error(f"Failed to create collection {name}: {e}")
            return None
            
    def store(self, content: str, metadata: Dict[str, Any], 
              collection_name: str = "experiences") -> str:
        """Store information in memory"""
        if not self.client or not self.encoder:
            logger.warning("VectorMemory not properly initialized")
            return None
            
        try:
            # Generate embedding
            embedding = self.encoder.encode(content).tolist()
            
            # Create unique ID
            doc_id = f"{collection_name}_{int(time.time() * 1000)}"
            
            # Add system metadata
            metadata.update({
                "timestamp": datetime.now().isoformat(),
                "length": len(content),
                "collection": collection_name
            })
            
            # Store in collection
            collection = self.collections.get(collection_name)
            if collection:
                collection.add(
                    embeddings=[embedding],
                    documents=[content],
                    metadatas=[metadata],
                    ids=[doc_id]
                )
                logger.debug(f"Stored in {collection_name}: {doc_id}")
                
            return doc_id
            
        except Exception as e:
            logger.error(f"Failed to store memory: {e}")
            return None
        
    def search(self, query: str, collection_name: Optional[str] = None, 
               filters: Optional[Dict[str, Any]] = None, 
               top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar memories"""
        if not self.client or not self.encoder:
            logger.warning("VectorMemory not properly initialized")
            return []
            
        try:
            # Generate query embedding
            query_embedding = self.encoder.encode(query).tolist()
            
            # Search in specified collection(s)
            if collection_name:
                collections = [self.collections.get(collection_name)]
            else:
                collections = [c for c in self.collections.values() if c is not None]
                
            all_results = []
            
            for collection in collections:
                if not collection:
                    continue
                    
                try:
                    # Search
                    results = collection.query(
                        query_embeddings=[query_embedding],
                        n_results=top_k,
                        where=filters
                    )
                    
                    # Format results
                    if results['ids'] and len(results['ids']) > 0:
                        for i in range(len(results['ids'][0])):
                            all_results.append({
                                "id": results['ids'][0][i],
                                "content": results['documents'][0][i],
                                "metadata": results['metadatas'][0][i],
                                "distance": results['distances'][0][i],
                                "similarity": 1 - results['distances'][0][i]
                            })
                except Exception as e:
                    logger.warning(f"Error searching collection: {e}")
                    continue
                    
            # Sort by similarity
            all_results.sort(key=lambda x: x['similarity'], reverse=True)
            
            # Filter by threshold
            filtered = [r for r in all_results if r['similarity'] >= self.similarity_threshold]
            
            return filtered[:self.max_results]
            
        except Exception as e:
            logger.error(f"Failed to search memory: {e}")
            return []
        
    def update(self, doc_id: str, content: Optional[str] = None, 
               metadata_update: Optional[Dict[str, Any]] = None):
        """Update an existing document"""
        if not self.client:
            return
            
        try:
            # Find collection from ID
            collection_name = doc_id.split('_')[0]
            collection = self.collections.get(collection_name)
            
            if not collection:
                raise ValueError(f"Unknown collection: {collection_name}")
                
            # Get current document
            current = collection.get(ids=[doc_id])
            if not current['ids']:
                raise ValueError(f"Document not found: {doc_id}")
                
            # Prepare updates
            new_content = content or current['documents'][0]
            new_metadata = current['metadatas'][0].copy() if current['metadatas'][0] else {}
            
            if metadata_update:
                new_metadata.update(metadata_update)
                new_metadata['last_updated'] = datetime.now().isoformat()
                
            # New embedding if content changed
            if content and self.encoder:
                new_embedding = self.encoder.encode(new_content).tolist()
            else:
                new_embedding = None
                
            # Update
            update_kwargs = {
                "ids": [doc_id],
                "documents": [new_content],
                "metadatas": [new_metadata]
            }
            
            if new_embedding:
                update_kwargs["embeddings"] = [new_embedding]
                
            collection.update(**update_kwargs)
            
            logger.debug(f"Updated document: {doc_id}")
            
        except Exception as e:
            logger.error(f"Failed to update document: {e}")
        
    def forget(self, criteria: Dict[str, Any]) -> int:
        """Selective forgetting based on criteria"""
        if not self.client:
            return 0
            
        to_delete = []
        
        try:
            # Search for documents to forget
            for collection_name, collection in self.collections.items():
                if not collection:
                    continue
                    
                try:
                    # Get all documents (limited for performance)
                    all_docs = collection.get(limit=1000)
                    
                    for i, metadata in enumerate(all_docs['metadatas']):
                        doc_id = all_docs['ids'][i]
                        
                        # Check criteria
                        if self._matches_criteria(metadata, criteria):
                            to_delete.append((collection_name, doc_id))
                except Exception as e:
                    logger.warning(f"Error processing collection {collection_name}: {e}")
                    continue
                        
            # Delete matching documents
            deleted_count = 0
            for collection_name, doc_id in to_delete:
                try:
                    collection = self.collections[collection_name]
                    if collection:
                        collection.delete(ids=[doc_id])
                        deleted_count += 1
                except Exception as e:
                    logger.warning(f"Error deleting {doc_id}: {e}")
                    continue
                    
            logger.info(f"Forgot {deleted_count} memories matching criteria")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to forget memories: {e}")
            return 0
        
    def _matches_criteria(self, metadata: Dict[str, Any], criteria: Dict[str, Any]) -> bool:
        """Check if metadata matches forgetting criteria"""
        try:
            if not metadata:
                return False
                
            for key, value in criteria.items():
                if key == "older_than":
                    # Age in days
                    timestamp = metadata.get("timestamp")
                    if not timestamp:
                        continue
                    doc_time = datetime.fromisoformat(timestamp)
                    age = (datetime.now() - doc_time).days
                    if age < value:
                        return False
                elif key == "importance_below":
                    if metadata.get("importance", 1.0) >= value:
                        return False
                elif key in metadata:
                    if metadata[key] != value:
                        return False
                        
            return True
            
        except Exception as e:
            logger.error(f"Error matching criteria: {e}")
            return False
        
    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics"""
        stats = {
            "total_memories": 0,
            "collections": {}
        }
        
        if not self.client:
            return stats
            
        try:
            for name, collection in self.collections.items():
                if collection:
                    try:
                        count = collection.count()
                        stats["collections"][name] = count
                        stats["total_memories"] += count
                    except Exception as e:
                        logger.warning(f"Error getting count for {name}: {e}")
                        stats["collections"][name] = 0
                else:
                    stats["collections"][name] = 0
                    
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            
        return stats
        
    def clear_collection(self, collection_name: str):
        """Clear all memories from a collection"""
        if not self.client:
            return
            
        try:
            collection = self.collections.get(collection_name)
            if collection:
                # Delete and recreate collection
                self.client.delete_collection(collection_name)
                self.collections[collection_name] = self.client.get_or_create_collection(collection_name)
                logger.info(f"Cleared collection: {collection_name}")
                
        except Exception as e:
            logger.error(f"Failed to clear collection: {e}")
            
    def is_ready(self) -> bool:
        """Check if memory system is ready"""
        return (self.client is not None and 
                self.encoder is not None and
                any(c is not None for c in self.collections.values()))