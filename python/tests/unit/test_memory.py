"""
Unit tests for Memory System.
Tests SessionMemory, WorkingMemory, and LongTermMemory implementations.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from src.memory.models import Message, Session, SessionContext
from src.server.exceptions import ExternalServiceError, DatabaseError


@pytest.mark.unit
@pytest.mark.asyncio
class TestSessionMemory:
    """Tests for SessionMemory (Redis-based)."""
    
    async def test_create_session(self, mock_supabase_client):
        """Test creating a new session."""
        from src.memory import SessionMemory
        
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock(return_value=True)
        mock_redis.setex = AsyncMock(return_value=True)
        
        with patch('redis.asyncio.from_url', return_value=mock_redis):
            memory = SessionMemory()
            await memory.connect()
            
            session = await memory.create_session(user_id="test-user", session_id="test-session")
            
            assert session.session_id == "test-session"
            assert session.user_id == "test-user"
            assert len(session.messages) == 0
            mock_redis.setex.assert_called_once()
    
    async def test_get_session_exists(self, mock_supabase_client):
        """Test retrieving an existing session."""
        from src.memory import SessionMemory
        
        session_data = Session(
            session_id="test-session",
            user_id="test-user",
            messages=[],
            context=SessionContext()
        ).model_dump_json()
        
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock(return_value=True)
        mock_redis.get = AsyncMock(return_value=session_data)
        mock_redis.expire = AsyncMock(return_value=True)
        
        with patch('redis.asyncio.from_url', return_value=mock_redis):
            memory = SessionMemory()
            await memory.connect()
            
            session = await memory.get_session("test-session")
            
            assert session is not None
            assert session.session_id == "test-session"
            mock_redis.get.assert_called_once()
            mock_redis.expire.assert_called_once()
    
    async def test_get_session_not_found(self, mock_supabase_client):
        """Test retrieving a non-existent session."""
        from src.memory import SessionMemory
        
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock(return_value=True)
        mock_redis.get = AsyncMock(return_value=None)
        
        with patch('redis.asyncio.from_url', return_value=mock_redis):
            memory = SessionMemory()
            await memory.connect()
            
            session = await memory.get_session("nonexistent")
            
            assert session is None
    
    async def test_add_message(self, mock_supabase_client):
        """Test adding a message to a session."""
        from src.memory import SessionMemory
        
        existing_session = Session(
            session_id="test-session",
            user_id="test-user",
            messages=[],
            context=SessionContext()
        )
        
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock(return_value=True)
        mock_redis.get = AsyncMock(return_value=existing_session.model_dump_json())
        mock_redis.set = AsyncMock(return_value=True)
        mock_redis.expire = AsyncMock(return_value=True)
        
        with patch('redis.asyncio.from_url', return_value=mock_redis):
            memory = SessionMemory()
            await memory.connect()
            
            message = Message(role="user", content="Test message")
            result = await memory.add_message("test-session", message)
            
            assert result is not None
            assert len(result.messages) == 1
            assert result.messages[0].content == "Test message"


@pytest.mark.unit
@pytest.mark.asyncio
class TestWorkingMemory:
    """Tests for WorkingMemory (Supabase-based)."""
    
    async def test_create_entry(self):
        """Test creating a working memory entry."""
        from src.memory import WorkingMemory
        
        mock_client = MagicMock()
        mock_result = MagicMock()
        mock_result.data = [{
            "id": "test-id",
            "user_id": "test-user",
            "memory_type": "context",
            "content": {"test": "data"},
            "created_at": datetime.utcnow().isoformat()
        }]
        
        mock_client.table().insert().execute.return_value = mock_result
        
        with patch('src.memory.working_memory.create_client', return_value=mock_client):
            memory = WorkingMemory()
            
            entry = await memory.create(
                user_id="test-user",
                memory_type="context",
                content={"test": "data"}
            )
            
            assert entry is not None
            # Circuit breaker will be called, so we can't directly assert on mock_client
    
    async def test_get_recent(self):
        """Test retrieving recent working memories."""
        from src.memory import WorkingMemory
        from src.memory.models import WorkingMemoryEntry
        
        mock_client = MagicMock()
        mock_result = MagicMock()
        mock_result.data = [
            {
                "id": "1",
                "user_id": "test-user",
                "memory_type": "context",
                "content": {"text": "entry1"},
                "created_at": datetime.utcnow().isoformat(),
                "expires_at": (datetime.utcnow() + timedelta(days=7)).isoformat(),
                "relevance_score": 1.0
            }
        ]
        
        mock_client.table().select().eq().order().limit().execute.return_value = mock_result
        
        with patch('src.memory.working_memory.create_client', return_value=mock_client):
            memory = WorkingMemory()
            
            entries = await memory.get_recent(user_id="test-user", limit=10)
            
            assert len(entries) == 1
            assert entries[0].user_id == "test-user"


@pytest.mark.unit
@pytest.mark.asyncio  
class TestLongTermMemory:
    """Tests for LongTermMemory (Supabase-based)."""
    
    async def test_create_entry(self):
        """Test creating a long-term memory entry."""
        from src.memory import LongTermMemory
        
        mock_client = MagicMock()
        mock_result = MagicMock()
        mock_result.data = [{
            "id": "test-id",
            "user_id": "test-user",
            "memory_type": "fact",
            "content": {"fact": "important info"},
            "created_at": datetime.utcnow().isoformat(),
            "importance_score": 0.9,
            "access_count": 0
        }]
        
        mock_client.table().insert().execute.return_value = mock_result
        
        with patch('src.memory.long_term_memory.create_client', return_value=mock_client):
            memory = LongTermMemory()
            
            entry = await memory.create(
                user_id="test-user",
                memory_type="fact",
                content={"fact": "important info"},
                importance_score=0.9
            )
            
            assert entry is not None
    
    async def test_get_important(self):
        """Test retrieving high-importance memories."""
        from src.memory import LongTermMemory
        
        mock_client = MagicMock()
        mock_result = MagicMock()
        mock_result.data = [
            {
                "id": "1",
                "user_id": "test-user",
                "memory_type": "fact",
                "content": {"fact": "critical info"},
                "created_at": datetime.utcnow().isoformat(),
                "importance_score": 0.95,
                "access_count": 5
            }
        ]
        
        mock_client.table().select().eq().gte().order().limit().execute.return_value = mock_result
        
        with patch('src.memory.long_term_memory.create_client', return_value=mock_client):
            memory = LongTermMemory()
            
            entries = await memory.get_important(user_id="test-user", min_importance=0.7)
            
            assert len(entries) == 1
            assert entries[0].importance_score >= 0.7


@pytest.mark.unit
class TestCustomExceptions:
    """Tests for custom exception classes."""
    
    def test_database_error(self):
        """Test DatabaseError exception."""
        from src.server.exceptions import DatabaseError
        
        error = DatabaseError("Connection failed")
        
        assert error.message == "Connection failed"
        assert error.error_code == "DATABASE_ERROR"
        assert error.status_code == 503
    
    def test_validation_error(self):
        """Test ValidationError exception."""
        from src.server.exceptions import ValidationError
        
        error = ValidationError("Invalid input", field="email")
        
        assert error.message == "Invalid input"
        assert error.error_code == "VALIDATION_ERROR"
        assert error.status_code == 422
        assert error.details["field"] == "email"
