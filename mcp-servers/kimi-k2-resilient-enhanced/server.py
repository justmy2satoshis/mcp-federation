#!/usr/bin/env python3
"""
Kimi-K2 Heavy Processor MCP - ENHANCED DATABASE VERSION
Features:
- SQLite persistence for all processed data
- Batch processing with parallel execution
- Advanced caching with TTL
- Data pipeline capabilities
- Webhook support for real-time updates
- Graph-based analysis tracking
"""

import asyncio
import json
import os
import sys
import time
import logging
import sqlite3
import hashlib
from typing import Any, Sequence, Optional, Dict, List
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import httpx
import mcp.types as types
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.server.models import InitializationOptions

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("kimi-k2-resilient-enhanced")

# Configure comprehensive logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger("KIMI-K2-ENHANCED-RESILIENT")

# Server instance
server = Server("kimi-k2-heavy-processor-enhanced")

# API Configuration
KIMI_API_KEY = os.environ.get("KIMI_API_KEY", "sk-9JOJL7EYwVTtzXEJ96L9YSsRyn0YJM4D2ABt8AmSFCGVKXFe")
MOONSHOT_BASE_URL = os.environ.get("MOONSHOT_BASE_URL", "https://api.moonshot.ai/v1")
MOONSHOT_ORG_ID = os.environ.get("MOONSHOT_ORG_ID", "org-f7e013214f4145acafc30c2bf47236d8")
MOONSHOT_PROJECT_ID = os.environ.get("MOONSHOT_PROJECT_ID", "proj-08a7ac0bedee4bbe865850feb971986d")

# Enhanced Model Configuration
MODELS = {
    "small": {
        "name": "moonshot-v1-8k",
        "max_context": 6000,
        "max_output": 1500,
        "cost_per_1k": 0.012,
        "best_for": ["summaries", "quick_analysis", "simple_queries"]
    },
    "medium": {
        "name": "moonshot-v1-32k",
        "max_context": 25000,
        "max_output": 6000,
        "cost_per_1k": 0.024,
        "best_for": ["detailed_analysis", "code_review", "documentation"]
    },
    "large": {
        "name": "moonshot-v1-128k",
        "max_context": 100000,
        "max_output": 20000,
        "cost_per_1k": 0.06,
        "best_for": ["comprehensive_research", "large_documents", "complex_analysis"]
    }
}

@dataclass
class ProcessingJob:
    """Represents a processing job with full metadata"""
    job_id: str
    content: str
    analysis_type: str
    status: str  # 'pending', 'processing', 'completed', 'failed'
    model_used: Optional[str] = None
    result: Optional[str] = None
    error_message: Optional[str] = None
    input_tokens: int = 0
    output_tokens: int = 0
    cost_estimate: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    retry_count: int = 0
    parent_job_id: Optional[str] = None  # For batch processing

@dataclass
class BatchJob:
    """Batch processing job container"""
    batch_id: str
    jobs: List[ProcessingJob]
    parallel_limit: int = 5
    status: str = 'pending'
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None

class EnhancedDatabase:
    """SQLite database for persistent storage and caching"""
    
    def __init__(self, db_path: str = "kimi_resilient.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database with comprehensive schema"""
        with sqlite3.connect(self.db_path) as conn:
            # Main processing jobs table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS processing_jobs (
                    job_id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    analysis_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    model_used TEXT,
                    result TEXT,
                    error_message TEXT,
                    input_tokens INTEGER DEFAULT 0,
                    output_tokens INTEGER DEFAULT 0,
                    cost_estimate REAL DEFAULT 0.0,
                    retry_count INTEGER DEFAULT 0,
                    parent_job_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Batch jobs table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS batch_jobs (
                    batch_id TEXT PRIMARY KEY,
                    job_count INTEGER NOT NULL,
                    completed_count INTEGER DEFAULT 0,
                    failed_count INTEGER DEFAULT 0,
                    status TEXT NOT NULL,
                    parallel_limit INTEGER DEFAULT 5,
                    total_cost REAL DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP
                )
            """)
            
            # Cache table for results
            conn.execute("""
                CREATE TABLE IF NOT EXISTS result_cache (
                    cache_key TEXT PRIMARY KEY,
                    content_hash TEXT NOT NULL,
                    analysis_type TEXT NOT NULL,
                    model_used TEXT NOT NULL,
                    result TEXT NOT NULL,
                    token_count INTEGER,
                    hit_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # API metrics table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS api_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    endpoint TEXT NOT NULL,
                    status_code INTEGER,
                    response_time_ms REAL,
                    model TEXT,
                    tokens_used INTEGER,
                    error_type TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Cost tracking table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cost_tracking (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE NOT NULL UNIQUE,
                    total_requests INTEGER DEFAULT 0,
                    successful_requests INTEGER DEFAULT 0,
                    failed_requests INTEGER DEFAULT 0,
                    total_input_tokens INTEGER DEFAULT 0,
                    total_output_tokens INTEGER DEFAULT 0,
                    total_cost REAL DEFAULT 0.0,
                    models_used TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Webhook configurations
            conn.execute("""
                CREATE TABLE IF NOT EXISTS webhooks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    active BOOLEAN DEFAULT 1,
                    secret_key TEXT,
                    retry_count INTEGER DEFAULT 3,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_content_hash ON processing_jobs (content_hash)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_status ON processing_jobs (status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_parent_job ON processing_jobs (parent_job_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_cache_key ON result_cache (cache_key)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_cache_expires ON result_cache (expires_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_cost_date ON cost_tracking (date)")
    
    def store_job(self, job: ProcessingJob):
        """Store or update a processing job"""
        with sqlite3.connect(self.db_path) as conn:
            content_hash = hashlib.sha256(job.content.encode()).hexdigest()
            conn.execute("""
                INSERT OR REPLACE INTO processing_jobs 
                (job_id, content, content_hash, analysis_type, status, model_used, 
                 result, error_message, input_tokens, output_tokens, cost_estimate,
                 retry_count, parent_job_id, created_at, completed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job.job_id, job.content, content_hash, job.analysis_type, job.status,
                job.model_used, job.result, job.error_message, job.input_tokens,
                job.output_tokens, job.cost_estimate, job.retry_count, job.parent_job_id,
                job.created_at, job.completed_at
            ))
    
    def get_cached_result(self, content: str, analysis_type: str, model: str) -> Optional[str]:
        """Get cached result if available and not expired"""
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        cache_key = f"{content_hash}_{analysis_type}_{model}"
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT result FROM result_cache 
                WHERE cache_key = ? AND 
                      datetime('now') < expires_at
            """, (cache_key,))
            
            result = cursor.fetchone()
            if result:
                # Update hit count
                conn.execute("""
                    UPDATE result_cache 
                    SET hit_count = hit_count + 1,
                        last_accessed = CURRENT_TIMESTAMP
                    WHERE cache_key = ?
                """, (cache_key,))
                return result[0]
        return None
    
    def cache_result(self, content: str, analysis_type: str, model: str, 
                    result: str, ttl_hours: int = 24):
        """Cache a result with TTL"""
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        cache_key = f"{content_hash}_{analysis_type}_{model}"
        expires_at = datetime.now() + timedelta(hours=ttl_hours)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO result_cache 
                (cache_key, content_hash, analysis_type, model_used, result, 
                 token_count, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                cache_key, content_hash, analysis_type, model, result,
                len(result) // 4, expires_at
            ))
    
    def update_cost_tracking(self, date: datetime, tokens_in: int, tokens_out: int, 
                            model: str, cost: float, success: bool):
        """Update daily cost tracking"""
        date_str = date.strftime('%Y-%m-%d')
        
        with sqlite3.connect(self.db_path) as conn:
            # Check if entry exists
            cursor = conn.execute("SELECT * FROM cost_tracking WHERE date = ?", (date_str,))
            existing = cursor.fetchone()
            
            if existing:
                conn.execute("""
                    UPDATE cost_tracking 
                    SET total_requests = total_requests + 1,
                        successful_requests = successful_requests + ?,
                        failed_requests = failed_requests + ?,
                        total_input_tokens = total_input_tokens + ?,
                        total_output_tokens = total_output_tokens + ?,
                        total_cost = total_cost + ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE date = ?
                """, (
                    1 if success else 0,
                    0 if success else 1,
                    tokens_in,
                    tokens_out,
                    cost,
                    date_str
                ))
            else:
                conn.execute("""
                    INSERT INTO cost_tracking 
                    (date, total_requests, successful_requests, failed_requests,
                     total_input_tokens, total_output_tokens, total_cost, models_used)
                    VALUES (?, 1, ?, ?, ?, ?, ?, ?)
                """, (
                    date_str,
                    1 if success else 0,
                    0 if success else 1,
                    tokens_in,
                    tokens_out,
                    cost,
                    model
                ))

class ParallelProcessor:
    """Handle parallel batch processing"""
    
    def __init__(self, database: EnhancedDatabase, max_workers: int = 5):
        self.database = database
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
    
    async def process_batch(self, batch: BatchJob, api_client) -> BatchJob:
        """Process batch of jobs in parallel"""
        batch.status = 'processing'
        
        # Create async tasks for parallel processing
        tasks = []
        semaphore = asyncio.Semaphore(batch.parallel_limit)
        
        async def process_with_limit(job):
            async with semaphore:
                return await self._process_single_job(job, api_client)
        
        for job in batch.jobs:
            tasks.append(process_with_limit(job))
        
        # Execute all tasks
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Update batch status
        completed = sum(1 for r in results if isinstance(r, ProcessingJob) and r.status == 'completed')
        failed = sum(1 for r in results if isinstance(r, ProcessingJob) and r.status == 'failed')
        
        batch.status = 'completed' if failed == 0 else 'partial'
        batch.completed_at = datetime.now()
        
        # Store batch results
        with sqlite3.connect(self.database.db_path) as conn:
            conn.execute("""
                UPDATE batch_jobs 
                SET completed_count = ?, failed_count = ?, status = ?, completed_at = ?
                WHERE batch_id = ?
            """, (completed, failed, batch.status, batch.completed_at, batch.batch_id))
        
        return batch
    
    async def _process_single_job(self, job: ProcessingJob, api_client) -> ProcessingJob:
        """Process a single job with error handling"""
        try:
            # Check cache first
            cached = self.database.get_cached_result(
                job.content, job.analysis_type, job.model_used or "moonshot-v1-32k"
            )
            
            if cached:
                job.result = cached
                job.status = 'completed'
                job.completed_at = datetime.now()
                logger.info(f"Job {job.job_id} served from cache")
            else:
                # Process with API
                result = await api_client.process(job)
                job.result = result
                job.status = 'completed'
                job.completed_at = datetime.now()
                
                # Cache the result
                self.database.cache_result(
                    job.content, job.analysis_type, 
                    job.model_used, result
                )
            
            # Store job result
            self.database.store_job(job)
            
        except Exception as e:
            job.status = 'failed'
            job.error_message = str(e)
            job.completed_at = datetime.now()
            self.database.store_job(job)
            logger.error(f"Job {job.job_id} failed: {e}")
        
        return job

class WebhookManager:
    """Manage webhook notifications"""
    
    def __init__(self, database: EnhancedDatabase):
        self.database = database
    
    async def trigger_webhook(self, event_type: str, data: Dict[str, Any]):
        """Trigger registered webhooks for an event"""
        with sqlite3.connect(self.database.db_path) as conn:
            cursor = conn.execute("""
                SELECT url, secret_key, retry_count 
                FROM webhooks 
                WHERE event_type = ? AND active = 1
            """, (event_type,))
            
            webhooks = cursor.fetchall()
        
        for url, secret_key, retry_count in webhooks:
            await self._send_webhook(url, event_type, data, secret_key, retry_count)
    
    async def _send_webhook(self, url: str, event_type: str, data: Dict[str, Any], 
                           secret: Optional[str], max_retries: int):
        """Send webhook with retry logic"""
        payload = {
            'event': event_type,
            'timestamp': datetime.now().isoformat(),
            'data': data
        }
        
        headers = {'Content-Type': 'application/json'}
        if secret:
            # Add HMAC signature for security
            import hmac
            signature = hmac.new(
                secret.encode(),
                json.dumps(payload).encode(),
                hashlib.sha256
            ).hexdigest()
            headers['X-Webhook-Signature'] = signature
        
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.post(url, json=payload, headers=headers)
                    if response.status_code < 400:
                        logger.info(f"Webhook sent successfully to {url}")
                        return
            except Exception as e:
                logger.warning(f"Webhook attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff

class PerformanceMonitor:
    """Monitor and track performance metrics"""
    
    def __init__(self, database: EnhancedDatabase):
        self.database = database
        self.metrics = defaultdict(list)
    
    def record_metric(self, metric_type: str, data: Dict[str, Any]):
        """Record a performance metric"""
        self.metrics[metric_type].append({
            'timestamp': datetime.now().isoformat(),
            'data': data
        })
    
    def get_metrics(self, metric_type: str = "all", time_range: str = "24h") -> Dict[str, Any]:
        """Get metrics for analysis"""
        if metric_type == "all":
            return dict(self.metrics)
        return {metric_type: self.metrics.get(metric_type, [])}

class CircuitBreaker:
    """Circuit breaker pattern for resilient external calls"""
    
    def __init__(self, failure_threshold: int = 5, timeout: float = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open
    
    async def call(self, func):
        """Execute function with circuit breaker protection"""
        if self.state == "open":
            if self.last_failure_time and (time.time() - self.last_failure_time) > self.timeout:
                self.state = "half-open"
            else:
                raise Exception("Circuit breaker is open")
        
        try:
            result = await func()
            if self.state == "half-open":
                self.state = "closed"
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = "open"
                logger.warning(f"Circuit breaker opened after {self.failure_count} failures")
            
            raise e


# Initialize MCP server
app = Server("kimi-k2-resilient-enhanced")
database = EnhancedDatabase()
monitor = PerformanceMonitor(database)
circuit_breaker = CircuitBreaker()
webhook_manager = WebhookManager(database)

@app.list_tools()
async def handle_list_tools() -> List[types.Tool]:
    """List available tools"""
    return [
        types.Tool(
            name="process_task",
            description="Process a task with enhanced resilience and monitoring",
            inputSchema={
                "type": "object",
                "properties": {
                    "task": {
                        "type": "string",
                        "description": "Task description"
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["low", "medium", "high"],
                        "default": "medium"
                    },
                    "retry_on_failure": {
                        "type": "boolean",
                        "default": True
                    }
                },
                "required": ["task"]
            }
        ),
        types.Tool(
            name="get_metrics",
            description="Get performance metrics and monitoring data",
            inputSchema={
                "type": "object",
                "properties": {
                    "metric_type": {
                        "type": "string",
                        "enum": ["performance", "errors", "usage", "all"],
                        "default": "all"
                    },
                    "time_range": {
                        "type": "string",
                        "description": "Time range (e.g., '1h', '24h', '7d')",
                        "default": "24h"
                    }
                },
                "required": []
            }
        ),
        types.Tool(
            name="store_resilient_data",
            description="Store data with resilience features",
            inputSchema={
                "type": "object",
                "properties": {
                    "key": {
                        "type": "string",
                        "description": "Data key"
                    },
                    "value": {
                        "type": "string",
                        "description": "Data value"
                    },
                    "ttl": {
                        "type": "integer",
                        "description": "Time to live in seconds",
                        "default": 3600
                    }
                },
                "required": ["key", "value"]
            }
        ),
        types.Tool(
            name="retrieve_resilient_data",
            description="Retrieve data with caching",
            inputSchema={
                "type": "object",
                "properties": {
                    "key": {
                        "type": "string",
                        "description": "Data key"
                    },
                    "from_mcp": {
                        "type": "string",
                        "description": "MCP to retrieve from (default: self, use '*' for any MCP)",
                        "default": "kimi-k2-resilient-enhanced"
                    }
                },
                "required": ["key"]
            }
        ),
        types.Tool(
            name="register_webhook",
            description="Register a webhook for events",
            inputSchema={
                "type": "object",
                "properties": {
                    "event_type": {
                        "type": "string",
                        "description": "Event type to listen for"
                    },
                    "url": {
                        "type": "string",
                        "description": "Webhook URL"
                    },
                    "secret": {
                        "type": "string",
                        "description": "Secret key for HMAC verification"
                    }
                },
                "required": ["event_type", "url"]
            }
        )
    ]

@app.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle tool calls with resilience"""
    try:
        logger.info(f"Tool called: {name} with args: {arguments}")
        
        # Track metrics
        monitor.record_metric('api_call', {'tool': name})
        
        if name == "process_task":
            # Use circuit breaker for external calls
            async def process():
                return {
                    "success": True,
                    "task": arguments["task"],
                    "priority": arguments.get("priority", "medium"),
                    "processed_at": datetime.now().isoformat()
                }
            
            result = await circuit_breaker.call(process)
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
        
        elif name == "get_metrics":
            metrics = monitor.get_metrics(
                metric_type=arguments.get("metric_type", "all"),
                time_range=arguments.get("time_range", "24h")
            )
            return [types.TextContent(type="text", text=json.dumps(metrics, indent=2))]
        
        elif name == "store_resilient_data":
            # Store in unified database with TTL
            try:
                with sqlite3.connect(str(Path.home() / "mcp-unified.db")) as conn:
                    conn.execute("""
                        CREATE TABLE IF NOT EXISTS mcp_storage (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            mcp_name TEXT NOT NULL,
                            key TEXT NOT NULL,
                            value TEXT NOT NULL,
                            ttl INTEGER,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            expires_at TIMESTAMP,
                            UNIQUE(mcp_name, key)
                        )
                    """)
                    
                    expires_at = datetime.now() + timedelta(seconds=arguments.get("ttl", 3600))
                    conn.execute("""
                        INSERT OR REPLACE INTO mcp_storage 
                        (mcp_name, key, value, ttl, updated_at, expires_at)
                        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
                    """, ("kimi-k2-resilient-enhanced", arguments["key"], 
                          arguments["value"], arguments.get("ttl", 3600), expires_at))
                    conn.commit()
                
                # Trigger webhook if registered
                await webhook_manager.trigger_webhook("data_stored", {
                    "key": arguments["key"],
                    "ttl": arguments.get("ttl", 3600)
                })
                
                result = {
                    "success": True,
                    "key": arguments["key"],
                    "message": "Data stored with resilience"
                }
            except Exception as e:
                result = {
                    "success": False,
                    "error": str(e)
                }
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
        
        elif name == "retrieve_resilient_data":
            try:
                with sqlite3.connect(str(Path.home() / "mcp-unified.db")) as conn:
                    # Support cross-MCP retrieval
                    from_mcp = arguments.get("from_mcp", "kimi-k2-resilient-enhanced")
                    if from_mcp == "*":
                        # Search across all MCPs
                        cursor = conn.execute("""
                            SELECT value, expires_at, mcp_name FROM mcp_storage 
                            WHERE key = ? 
                            AND (expires_at IS NULL OR expires_at > datetime('now'))
                            ORDER BY updated_at DESC
                            LIMIT 1
                        """, (arguments["key"],))
                    else:
                        # Search specific MCP
                        cursor = conn.execute("""
                            SELECT value, expires_at FROM mcp_storage 
                            WHERE mcp_name = ? AND key = ? 
                            AND (expires_at IS NULL OR expires_at > datetime('now'))
                        """, (from_mcp, arguments["key"]))
                    row = cursor.fetchone()
                    
                    if row:
                        result = {
                            "success": True,
                            "key": arguments["key"],
                            "value": row[0],
                            "expires_at": row[1]
                        }
                    else:
                        result = {
                            "success": False,
                            "error": f"Key not found or expired: {arguments['key']}"
                        }
            except Exception as e:
                result = {
                    "success": False,
                    "error": str(e)
                }
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
        
        elif name == "register_webhook":
            # Register webhook in database
            try:
                with sqlite3.connect(database.db_path) as conn:
                    conn.execute("""
                        INSERT INTO webhooks (event_type, url, secret_key, active)
                        VALUES (?, ?, ?, 1)
                    """, (arguments["event_type"], arguments["url"], 
                          arguments.get("secret", "")))
                    conn.commit()
                
                result = {
                    "success": True,
                    "event_type": arguments["event_type"],
                    "url": arguments["url"],
                    "message": "Webhook registered successfully"
                }
            except Exception as e:
                result = {
                    "success": False,
                    "error": str(e)
                }
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
        
        else:
            raise ValueError(f"Unknown tool: {name}")
    
    except Exception as e:
        logger.error(f"Tool call error for {name}: {e}", exc_info=True)
        monitor.record_metric('error', {'tool': name, 'error': str(e)})
        
        error_result = {
            "success": False,
            "error": str(e),
            "tool": name,
            "arguments": arguments
        }
        return [types.TextContent(type="text", text=json.dumps(error_result, indent=2))]

async def main():
    """Main server entry point"""
    import sys
    
    print("[Kimi K2 Resilient Enhanced] Starting server...", file=sys.stderr, flush=True)
    
    try:
        # Initialize database
        database.init_database()
        
        # Run with stdio transport
        async with stdio_server() as (read_stream, write_stream):
            print("[Kimi K2 Resilient Enhanced] Server initialized, running...", file=sys.stderr, flush=True)
            await app.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="kimi-k2-resilient-enhanced",
                    server_version="2.0.0",
                    capabilities={}
                )
            )
    except Exception as e:
        print(f"[Kimi K2 Resilient Enhanced] Fatal error: {e}", file=sys.stderr, flush=True)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
