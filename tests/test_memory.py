import pytest
import asyncio
import os
from src.memory.memory_store import MemoryStore

@pytest.fixture
def memory_db_path():
    db_path = "test_memory.db"
    yield db_path
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except PermissionError:
            pass # Windows lock

@pytest.mark.asyncio
async def test_memory_store_init(memory_db_path):
    """Test memory store initialization."""
    store = MemoryStore(f"sqlite+aiosqlite:///{memory_db_path}")
    await store.initialize()
    
    assert os.path.exists(memory_db_path)
    await store.close()

@pytest.mark.asyncio
async def test_memory_add_and_search(memory_db_path):
    """Test adding and searching memories with FTS."""
    store = MemoryStore(f"sqlite+aiosqlite:///{memory_db_path}")
    await store.initialize()
    
    mem_id = await store.add_memory("preference", "Utente ama il colore blu", 8.5)
    assert mem_id is not None
    
    results = await store.search_memories("colore blu")
    
    assert len(results) >= 1
    assert results[0].content == "Utente ama il colore blu"
    assert results[0].type == "preference"
    assert results[0].importance == 8.5
    
    await store.close()
