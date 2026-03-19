"""
Database Connection Pooling
Reuses database connections to reduce latency
"""

import logging
from typing import Optional, Any
import asyncpg
from asyncpg import Pool
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class DatabasePool:
    """Async connection pool for PostgreSQL"""
    
    def __init__(
        self,
        dsn: str = "postgresql://user:password@localhost/insurance",
        min_size: int = 10,
        max_size: int = 20
    ):
        self.dsn = dsn
        self.min_size = min_size
        self.max_size = max_size
        self.pool: Optional[Pool] = None
    
    async def initialize(self):
        """Create connection pool"""
        try:
            self.pool = await asyncpg.create_pool(
                self.dsn,
                min_size=self.min_size,
                max_size=self.max_size,
                command_timeout=60
            )
            logger.info(f"Database pool created: min={self.min_size}, max={self.max_size}")
        except Exception as e:
            logger.error(f"Failed to create database pool: {e}")
            raise
    
    async def close(self):
        """Close connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("Database pool closed")
    
    @asynccontextmanager
    async def acquire(self):
        """Acquire connection from pool"""
        if not self.pool:
            raise RuntimeError("Pool not initialized")
        
        async with self.pool.acquire() as conn:
            yield conn
    
    async def execute(self, query: str, *args):
        """Execute query"""
        async with self.acquire() as conn:
            return await conn.execute(query, *args)
    
    async def fetch(self, query: str, *args):
        """Fetch query results"""
        async with self.acquire() as conn:
            return await conn.fetch(query, *args)
    
    async def fetchval(self, query: str, *args):
        """Fetch single value"""
        async with self.acquire() as conn:
            return await conn.fetchval(query, *args)
    
    async def fetchrow(self, query: str, *args):
        """Fetch single row"""
        async with self.acquire() as conn:
            return await conn.fetchrow(query, *args)
    
    def get_pool_status(self) -> dict:
        """Get pool status"""
        if not self.pool:
            return {"status": "not_initialized"}
        
        return {
            "size": self.pool.get_size(),
            "idle": self.pool.get_idle_size(),
            "min_size": self.min_size,
            "max_size": self.max_size
        }


class SQLitePool:
    """SQLite connection pool (minimal pooling)"""
    
    def __init__(self, db_path: str = "rag.db"):
        self.db_path = db_path
        self.connection = None
    
    async def initialize(self):
        """Initialize SQLite connection"""
        import aiosqlite
        
        try:
            self.connection = await aiosqlite.connect(self.db_path)
            # Enable journaling for better concurrency
            await self.connection.execute("PRAGMA journal_mode=WAL")
            logger.info(f"SQLite pool initialized: {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize SQLite: {e}")
            raise
    
    async def close(self):
        """Close connection"""
        if self.connection:
            await self.connection.close()
    
    @asynccontextmanager
    async def acquire(self):
        """Acquire connection"""
        if not self.connection:
            raise RuntimeError("Pool not initialized")
        yield self.connection
    
    async def execute(self, query: str, *args):
        """Execute query"""
        async with self.acquire() as conn:
            cursor = await conn.execute(query, args)
            await conn.commit()
            return cursor
    
    async def fetch(self, query: str, *args):
        """Fetch query results"""
        async with self.acquire() as conn:
            cursor = await conn.execute(query, args)
            return await cursor.fetchall()
    
    async def fetchval(self, query: str, *args):
        """Fetch single value"""
        async with self.acquire() as conn:
            cursor = await conn.execute(query, args)
            result = await cursor.fetchone()
            return result[0] if result else None
    
    async def fetchrow(self, query: str, *args):
        """Fetch single row"""
        async with self.acquire() as conn:
            cursor = await conn.execute(query, args)
            return await cursor.fetchone()
    
    def get_pool_status(self) -> dict:
        """Get pool status"""
        return {
            "type": "sqlite",
            "db_path": self.db_path,
            "connected": self.connection is not None
        }


class PolicyDatabase:
    """Policy data access layer with pooling"""
    
    def __init__(self, pool):
        self.pool = pool
    
    async def search_policies(self, keywords: list, limit: int = 10):
        """Search policies by keywords"""
        try:
            # Example query (adjust to your schema)
            query = """
                SELECT id, name, description, price, coverage
                FROM policies
                WHERE description LIKE any($1)
                LIMIT $2
            """
            
            like_patterns = [f"%{kw}%" for kw in keywords]
            results = await self.pool.fetch(query, like_patterns, limit)
            return results
        except Exception as e:
            logger.warning(f"Policy search error: {e}")
            return []
    
    async def get_policy_details(self, policy_id: int):
        """Get detailed policy information"""
        try:
            query = """
                SELECT * FROM policies WHERE id = $1
            """
            return await self.pool.fetchrow(query, policy_id)
        except Exception as e:
            logger.warning(f"Policy retrieval error: {e}")
            return None
    
    async def search_claims_info(self, keywords: list):
        """Search claims procedures"""
        try:
            query = """
                SELECT id, title, content
                FROM claims_procedures
                WHERE content LIKE any($1)
                LIMIT 5
            """
            
            like_patterns = [f"%{kw}%" for kw in keywords]
            results = await self.pool.fetch(query, like_patterns)
            return results
        except Exception as e:
            logger.warning(f"Claims search error: {e}")
            return []
