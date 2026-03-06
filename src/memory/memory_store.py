import asyncio
import logging
from datetime import datetime
from sqlalchemy import Column, String, Text, Float, DateTime, select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker

logger = logging.getLogger(__name__)

Base = declarative_base()

class MemoryItem(Base):
    """SQLAlchemy model for storing persistent memory items."""
    __tablename__ = "memories"

    id = Column(String, primary_key=True)
    type = Column(String, nullable=False, index=True) # user_profile, contact, fact, preference
    content = Column(Text, nullable=False)            # The actual memory content
    metadata_json = Column(Text, nullable=True)       # JSON string for extra structured data
    importance = Column(Float, default=1.0)           # 1.0 to 10.0 scale of importance
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<MemoryItem(type='{self.type}', content='{self.content[:30]}...')>"


class MemoryStore:
    """Manages the SQLite database for memory persistence."""
    
    def __init__(self, db_url: str = "sqlite+aiosqlite:///memory.db"):
        self.engine = create_async_engine(db_url, echo=False)
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
        self._initialized = False

    async def initialize(self):
        """Create tables if they don't exist."""
        if self._initialized:
            return
            
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            
            # Setup FTS5 (Full Text Search) virtual table for fast semantic-like searching
            # This is SQLite specific but very powerful for local agent memory without a vector DB
            try:
                await conn.exec_driver_sql(
                    "CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(content, content_id UNINDEXED);"
                )
            except Exception as e:
                logger.debug(f"FTS5 might already exist or isn't supported: {e}")
                
        self._initialized = True
        logger.info("MemoryStore initialized")

    async def add_memory(self, type_category: str, content: str, importance: float = 1.0) -> str:
        """Add a new memory to the store."""
        import uuid
        mem_id = str(uuid.uuid4())
        
        async with self.async_session() as session:
            new_mem = MemoryItem(
                id=mem_id,
                type=type_category,
                content=content,
                importance=importance
            )
            session.add(new_mem)
            await session.commit()
            
            # Also add to FTS table
            async with self.engine.begin() as conn:
                try:
                    await conn.exec_driver_sql(
                        "INSERT INTO memories_fts(rowid, content, content_id) VALUES (?, ?, ?)",
                        (None, content, mem_id)
                    )
                except Exception as e:
                    logger.warning(f"Failed to add to FTS index: {e}")
                    
            logger.info(f"Stored memory: [{type_category}] {content[:50]}...")
            return mem_id

    async def search_memories(self, query: str, limit: int = 5) -> list[MemoryItem]:
        """Search memories using FTS."""
        async with self.async_session() as session:
            # We use the FTS table to find IDs, then load the actual models
            # In SQLite FTS5, we can use MATCH
            try:
                # FTS query syntax can be strict, we'll do a simple OR based split for robustness
                terms = " OR ".join(f'"{word}"' for word in query.split() if len(word) > 3)
                if not terms:
                    terms = f'"{query}"'
                
                # Use raw SQL for FTS lookup because the virtual table is not in SQLAlchemy metadata
                raw_sql = f"SELECT content_id FROM memories_fts WHERE content MATCH '{terms}'"
                
                async with self.engine.connect() as conn:
                    ids_result = await conn.execute(asyncio.get_event_loop().run_in_executor(None, lambda: conn.exec_driver_sql(raw_sql)))
                    # Wait, no, simpler way with session
                    pass

                # Actually, let's just use session.execute with text()
                from sqlalchemy import text
                fts_results = await session.execute(text(raw_sql))
                ids = [row[0] for row in fts_results.fetchall()]
                
                if not ids:
                    result = await session.execute(
                        select(MemoryItem).where(MemoryItem.content.ilike(f"%{query}%")).limit(limit)
                    )
                else:
                    result = await session.execute(
                        select(MemoryItem).where(MemoryItem.id.in_(ids))
                        .order_by(MemoryItem.importance.desc()).limit(limit)
                    )
                return result.scalars().all()
            except Exception as e:
                logger.warning(f"FTS search failed, falling back to LIKE: {e}")
                # Fallback to simple LIKE search if FTS fails
                like_term = f"%{query}%"
                result = await session.execute(
                    select(MemoryItem)
                    .where(MemoryItem.content.ilike(like_term))
                    .order_by(MemoryItem.importance.desc())
                    .limit(limit)
                )
                return result.scalars().all()

    async def close(self):
        """Close the database engine to release file locks."""
        if self.engine:
            await self.engine.dispose()
            self._initialized = False
            logger.info("MemoryStore engine disposed")

# Global Singleton instance
store = MemoryStore()
