import pytest
import pytest_asyncio
from datetime import datetime
from src.memory.session_memory import SessionMemory
from src.memory.models import Message

@pytest_asyncio.fixture
async def session_memory():
    # Use a test Redis database (e.g., DB 1) to avoid conflicts
    memory = SessionMemory(redis_url="redis://localhost:6379/1")
    await memory.connect()
    # Clean up before test
    await memory.redis.flushdb()
    yield memory
    # Clean up after test
    await memory.redis.flushdb()
    await memory.close()

@pytest.mark.asyncio
async def test_create_session(session_memory):
    user_id = "test_user"
    session = await session_memory.create_session(user_id)
    
    assert session.user_id == user_id
    assert session.session_id is not None
    
    # Verify it exists in Redis
    retrieved = await session_memory.get_session(session.session_id)
    assert retrieved is not None
    assert retrieved.session_id == session.session_id

@pytest.mark.asyncio
async def test_add_message(session_memory):
    user_id = "test_user"
    session = await session_memory.create_session(user_id)
    
    msg = Message(role="user", content="Hello")
    updated_session = await session_memory.add_message(session.session_id, msg)
    
    assert len(updated_session.messages) == 1
    assert updated_session.messages[0].content == "Hello"
    
    # Verify persistence
    retrieved = await session_memory.get_session(session.session_id)
    assert len(retrieved.messages) == 1

@pytest.mark.asyncio
async def test_update_context(session_memory):
    user_id = "test_user"
    session = await session_memory.create_session(user_id)
    
    updates = {"active_project_id": "proj_123"}
    updated_session = await session_memory.update_context(session.session_id, updates)
    
    assert updated_session.context.active_project_id == "proj_123"
    
    # Verify persistence
    retrieved = await session_memory.get_session(session.session_id)
    assert retrieved.context.active_project_id == "proj_123"

@pytest.mark.asyncio
async def test_ttl_expiry(session_memory):
    # Set a short TTL for testing
    session_memory.ttl_seconds = 1
    
    user_id = "test_user"
    session = await session_memory.create_session(user_id)
    
    # Verify it exists
    assert await session_memory.get_session(session.session_id) is not None
    
    # Wait for expiry (mocking time would be better, but sleep is simple for integration test)
    import asyncio
    await asyncio.sleep(1.1)
    
    # Verify it's gone
    assert await session_memory.get_session(session.session_id) is None
