#!/usr/bin/env python3
"""
RAG Context MCP Server v3.2 - Production Ready
Fixed vector storage and retrieval with unified database integration
"""

import asyncio
import json
import logging
import os
import sqlite3
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime
import hashlib
import numpy as np
from dataclasses import dataclass, field

# MCP imports
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
import mcp.types as types

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("rag-context-v3.2")

# Storage paths
DATA_DIR = Path(os.environ.get("RAG_DATA_DIR", Path.home() / ".rag-context-v3.2"))
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Unified database path for federation
UNIFIED_DB = Path(r"C:\Users\User\mcp-servers\databases\mcp-federation.db")
VECTOR_INDEX_PATH = DATA_DIR / "vectors.npz"
METADATA_PATH = DATA_DIR / "metadata.json"

class VectorStorage:
    """Production-ready vector storage with numpy arrays"""
    
    def __init__(self):
        self.embeddings = {}
        self.metadata = {}
        self.load()
        
    def embed_text(self, text: str) -> np.ndarray:
        """Create simple but effective text embeddings"""
        # Create a 256-dimensional vector based on character frequencies
        vector = np.zeros(256)
        text_lower = text.lower()
        
        # Character frequency embedding
        for char in text_lower:
            if ord(char) < 256:
                vector[ord(char)] += 1
        
        # Add n-gram features for better semantic capture
        for i in range(len(text_lower) - 1):
            bigram = text_lower[i:i+2]
            hash_val = hash(bigram) % 256
            vector[hash_val] += 0.5
            
        # Normalize the vector
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
            
        return vector
    
    def store(self, key: str, content: str, metadata: Optional[Dict] = None) -> bool:
        """Store content with vector embedding"""
        try:
            # Generate embedding
            embedding = self.embed_text(content)
            
            # Store in memory
            self.embeddings[key] = embedding
            self.metadata[key] = {
                'content': content,
                'metadata': metadata or {},
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Persist to disk
            self.save()
            
            # Also store in unified database for federation
            self._store_in_unified_db(key, content, metadata)
            
            logger.info(f"Stored key: {key}")
            return True
            
        except Exception as e:
            logger.error(f"Storage error: {e}")
            return False
    
    def search(self, query: str, limit: int = 5, threshold: float = 0.1) -> List[Dict]:
        """Search for similar content using cosine similarity"""
        if not self.embeddings:
            logger.warning("No embeddings found")
            return []
        
        # Get query embedding
        query_vector = self.embed_text(query)
        
        # Calculate similarities
        similarities = {}
        for key, embedding in self.embeddings.items():
            similarity = float(np.dot(query_vector, embedding))
            if similarity > threshold:
                similarities[key] = similarity
        
        # Sort by similarity
        sorted_keys = sorted(similarities.keys(), 
                           key=lambda k: similarities[k], 
                           reverse=True)[:limit]
        
        # Build results
        results = []
        for key in sorted_keys:
            result = {
                'key': key,
                'content': self.metadata[key]['content'],
                'metadata': self.metadata[key]['metadata'],
                'score': similarities[key],
                'timestamp': self.metadata[key].get('timestamp', '')
            }
            results.append(result)
            
        logger.info(f"Search for '{query}' returned {len(results)} results")
        return results
    
    def save(self):
        """Persist vectors and metadata to disk"""
        try:
            # Save numpy arrays
            np.savez_compressed(VECTOR_INDEX_PATH, **self.embeddings)
            
            # Save metadata as JSON
            with open(METADATA_PATH, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2)
                
            logger.info("Saved vectors and metadata to disk")
            
        except Exception as e:
            logger.error(f"Save error: {e}")
    
    def load(self):
        """Load vectors and metadata from disk"""
        try:
            # Load numpy arrays
            if VECTOR_INDEX_PATH.exists():
                data = np.load(VECTOR_INDEX_PATH)
                self.embeddings = {k: data[k] for k in data.files}
                logger.info(f"Loaded {len(self.embeddings)} vectors")
            
            # Load metadata
            if METADATA_PATH.exists():
                with open(METADATA_PATH, 'r', encoding='utf-8') as f:
                    self.metadata = json.load(f)
                logger.info(f"Loaded metadata for {len(self.metadata)} entries")
                    
        except Exception as e:
            logger.error(f"Load error: {e}")
    
    def _store_in_unified_db(self, key: str, content: str, metadata: Optional[Dict] = None):
        """Store in unified federation database"""
        try:
            # Ensure database directory exists
            UNIFIED_DB.parent.mkdir(parents=True, exist_ok=True)
            
            # Connect to unified database
            conn = sqlite3.connect(UNIFIED_DB)
            
            # Create table if not exists
            conn.execute('''
                CREATE TABLE IF NOT EXISTS mcp_context (
                    id TEXT PRIMARY KEY,
                    mcp_source TEXT NOT NULL,
                    key TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(mcp_source, key)
                )
            ''')
            
            # Insert or replace data
            context_id = str(uuid.uuid4())
            metadata_json = json.dumps(metadata) if metadata else None
            
            conn.execute('''
                INSERT OR REPLACE INTO mcp_context 
                (id, mcp_source, key, content, metadata, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (context_id, 'rag-context', key, content, metadata_json, datetime.now()))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Stored in unified database: {key}")
            
        except Exception as e:
            logger.error(f"Unified DB storage error: {e}")

# Global storage instance
storage = VectorStorage()

# Create MCP server
server = Server("rag-context-v3.2")

@server.list_tools()
async def list_tools() -> list[types.Tool]:
    """List available RAG tools"""
    return [
        types.Tool(
            name="setContext",
            description="Store content with vector embeddings for semantic search",
            inputSchema={
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Unique identifier for the content"},
                    "content": {"type": "string", "description": "Content to store"},
                    "metadata": {"type": "object", "description": "Optional metadata"}
                },
                "required": ["key", "content"]
            }
        ),
        types.Tool(
            name="getContext",
            description="Retrieve content using semantic search",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "limit": {"type": "integer", "description": "Maximum results", "default": 5},
                    "threshold": {"type": "number", "description": "Similarity threshold", "default": 0.1}
                },
                "required": ["query"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """Handle tool calls"""
    
    if name == "setContext":
        key = arguments["key"]
        content = arguments["content"]
        metadata = arguments.get("metadata", {})
        
        success = storage.store(key, content, metadata)
        
        if success:
            return [types.TextContent(
                type="text",
                text=f"Successfully stored context with key: {key}"
            )]
        else:
            return [types.TextContent(
                type="text",
                text=f"Failed to store context with key: {key}"
            )]
    
    elif name == "getContext":
        query = arguments["query"]
        limit = arguments.get("limit", 5)
        threshold = arguments.get("threshold", 0.1)
        
        results = storage.search(query, limit, threshold)
        
        if results:
            response = json.dumps(results, indent=2)
        else:
            response = "[]"
            
        return [types.TextContent(
            type="text",
            text=response
        )]
    
    else:
        return [types.TextContent(
            type="text",
            text=f"Unknown tool: {name}"
        )]

async def main():
    """Run the RAG Context MCP server"""
    logger.info("Starting RAG Context v3.2 server...")
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="rag-context-v3.2",
                server_version="3.2.0",
                capabilities={}
            )
        )

if __name__ == "__main__":
    asyncio.run(main())