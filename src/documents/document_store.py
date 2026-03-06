import logging
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker

logger = logging.getLogger(__name__)

Base = declarative_base()

class DocumentChunk(Base):
    """SQLAlchemy model for storing document chunks for search."""
    __tablename__ = "document_chunks"

    id = Column(String, primary_key=True)
    doc_id = Column(String, index=True)
    title = Column(String)
    content = Column(Text, nullable=False)
    metadata_json = Column(Text, nullable=True) # JSON for tags, source, etc.
    created_at = Column(DateTime, default=datetime.utcnow)

class DocumentStore:
    """Manages document indexing and search using SQLite FTS5."""
    
    def __init__(self, db_url: str = "sqlite+aiosqlite:///documents.db"):
        self.engine = create_async_engine(db_url, echo=False)
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
        self._initialized = False

    async def initialize(self):
        if self._initialized:
            return
            
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            try:
                # FTS5 for documents
                await conn.exec_driver_sql(
                    "CREATE VIRTUAL TABLE IF NOT EXISTS docs_fts USING fts5(content, chunk_id UNINDEXED, title UNINDEXED);"
                )
            except Exception as e:
                logger.debug(f"FTS5 setup error: {e}")
                
        self._initialized = True
        logger.info("DocumentStore initialized")

    async def index_document(self, title: str, content: str, doc_id: str = None) -> str:
        """Index a document by splitting it into chunks."""
        if not doc_id:
            doc_id = str(uuid.uuid4())
            
        # Simple chunking (e.g. 1500 chars with 200 overlap)
        chunk_size = 1500
        overlap = 200
        chunks = []
        
        for i in range(0, len(content), chunk_size - overlap):
            chunks.append(content[i : i + chunk_size])
            
        async with self.async_session() as session:
            for chunk_content in chunks:
                chunk_id = str(uuid.uuid4())
                new_chunk = DocumentChunk(
                    id=chunk_id,
                    doc_id=doc_id,
                    title=title,
                    content=chunk_content
                )
                session.add(new_chunk)
                
                # Add to FTS
                async with self.engine.begin() as conn:
                    await conn.exec_driver_sql(
                        "INSERT INTO docs_fts(chunk_id, content, title) VALUES (?, ?, ?)",
                        (chunk_id, chunk_content, title)
                    )
            
            await session.commit()
        
        logger.info(f"Indexed document '{title}' ({len(chunks)} chunks)")
        return doc_id

    async def search_documents(self, query: str, limit: int = 5) -> list[dict]:
        """Search across documents using FTS5."""
        async with self.async_session() as session:
            try:
                # Basic FTS5 MATCH query
                clean_query = query.replace("'", "''")
                result = await session.execute(
                    select(DocumentChunk).where(
                        DocumentChunk.id.in_(
                            select(Column("chunk_id")).select_from(Base.metadata.tables.get('docs_fts', None))
                            .where(Column("docs_fts").compile().string + f" MATCH '{clean_query}'")
                        )
                    ).limit(limit)
                )
                chunks = result.scalars().all()
                return [{"title": c.title, "content": c.content, "doc_id": c.doc_id} for c in chunks]
            except Exception as e:
                logger.warning(f"Doc FTS search failed: {e}")
                return []

# Singleton instance
doc_store = DocumentStore()
