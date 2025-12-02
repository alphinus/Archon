"""
Integration tests for Memory API endpoints.
Tests the complete request/response cycle through FastAPI.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime


@pytest.mark.integration
class TestMemoryAPIEndpoints:
    """Integration tests for /api/memory/* endpoints."""
    
    def test_get_session_memory_success(self, client, mock_supabase_client):
        """Test GET /api/memory/session/{session_id} - success case."""
        # Mock Redis response
        mock_session_data = {
            "session_id": "test-session",
            "user_id": "test-user",
            "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there"}
            ],
            "created_at": datetime.utcnow().isoformat(),
            "last_accessed_at": datetime.utcnow().isoformat(),
            "context": {}
        }
        
        with patch('src.memory.session_memory.redis.from_url') as mock_redis:
            mock_redis_instance = AsyncMock()
            mock_redis_instance.get.return_value = str(mock_session_data)
            mock_redis.return_value = mock_redis_instance
            
            response = client.get("/api/memory/session/test-session")
            
            assert response.status_code == 200
            data = response.json()
            assert "session_id" in data
    
    def test_get_session_memory_not_found(self, client, mock_supabase_client):
        """Test GET /api/memory/session/{session_id} - not found."""
        with patch('src.memory.session_memory.redis.from_url') as mock_redis:
            mock_redis_instance = AsyncMock()
            mock_redis_instance.get.return_value = None
            mock_redis.return_value = mock_redis_instance
            
            response = client.get("/api/memory/session/nonexistent")
            
            assert response.status_code == 404
    
    def test_get_working_memory(self, client, mock_supabase_client):
        """Test GET /api/memory/working."""
        mock_supabase_client.table().select().eq().order().limit().execute.return_value.data = [
            {
                "id": "1",
                "user_id": "test-user",
                "memory_type": "context",
                "content": {"text": "test"},
                "created_at": datetime.utcnow().isoformat(),
                "expires_at": datetime.utcnow().isoformat(),
                "relevance_score": 1.0
            }
        ]
        
        response = client.get("/api/memory/working?user_id=test-user")
        
        assert response.status_code == 200
        data = response.json()
        assert "entries" in data
    
    def test_get_working_memory_missing_user_id(self, client, mock_supabase_client):
        """Test GET /api/memory/working without user_id - should fail."""
        response = client.get("/api/memory/working")
        
        assert response.status_code == 422  # Validation error
    
    def test_get_longterm_memory(self, client, mock_supabase_client):
        """Test GET /api/memory/longterm."""
        mock_supabase_client.table().select().eq().gte().order().limit().execute.return_value.data = [
            {
                "id": "1",
                "user_id": "test-user",
                "memory_type": "fact",
                "content": {"fact": "important"},
                "created_at": datetime.utcnow().isoformat(),
                "importance_score": 0.9,
                "access_count": 5
            }
        ]
        
        response = client.get("/api/memory/longterm?user_id=test-user")
        
        assert response.status_code == 200
        data = response.json()
        assert "entries" in data
    
    def test_get_longterm_memory_with_filters(self, client, mock_supabase_client):
        """Test GET /api/memory/longterm with filters."""
        mock_supabase_client.table().select().eq().gte().order().limit().execute.return_value.data = []
        
        response = client.get(
            "/api/memory/longterm?user_id=test-user&memory_type=fact&min_importance=0.8"
        )
        
        assert response.status_code == 200
    
    def test_get_memory_stats(self, client, mock_supabase_client):
        """Test GET /api/memory/stats/{user_id}."""
        # Mock working memory response
        mock_supabase_client.table().select().eq().order().limit().execute.return_value.data = [
            {"id": "1", "importance_score": 0.5},
            {"id": "2", "importance_score": 0.7}
        ]
        
        response = client.get("/api/memory/stats/test-user")
        
        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert "total_memories" in data
    
    def test_memory_api_pagination(self, client, mock_supabase_client):
        """Test pagination across memory endpoints."""
        mock_supabase_client.table().select().eq().order().limit().execute.return_value.data = []
        
        response = client.get("/api/memory/working?user_id=test-user&page=2&page_size=20")
        
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2
        assert data["page_size"] == 20
    
    def test_memory_api_error_handling(self, client, mock_supabase_client):
        """Test error handling when database fails."""
        # Make Supabase throw an error
        mock_supabase_client.table().select().eq().order().limit().execute.side_effect = Exception("DB Error")
        
        response = client.get("/api/memory/working?user_id=test-user")
        
        assert response.status_code == 500
        data = response.json()
        assert "error" in data
    
    def test_session_memory_circuit_breaker(self, client, mock_supabase_client):
        """Test that circuit breaker works for Redis failures."""
        with patch('src.memory.session_memory.redis.from_url') as mock_redis:
            # Simulate Redis being down
            mock_redis.side_effect = Exception("Redis connection failed")
            
            response = client.get("/api/memory/session/test-session")
            
            # Should get a service unavailable error
            assert response.status_code in [503, 500]
    
    def test_memory_stats_empty_data(self, client, mock_supabase_client):
        """Test memory stats with no data."""
        mock_supabase_client.table().select().eq().order().limit().execute.return_value.data = []
        
        response = client.get("/api/memory/stats/test-user")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_memories"] == 0
    
    def test_invalid_uuid_format(self, client, mock_supabase_client):
        """Test that invalid UUID format is handled."""
        response = client.get("/api/memory/working?user_id=invalid-uuid")
        
        # Should either validate UUID format or return error from DB
        assert response.status_code in [422, 500, 503]
    
    def test_memory_type_filtering(self, client, mock_supabase_client):
        """Test filtering by memory type."""
        mock_supabase_client.table().select().eq().order().limit().execute.return_value.data = []
        
        response = client.get("/api/memory/working?user_id=test-user&memory_type=context")
        
        assert response.status_code == 200
    
    def test_importance_score_filtering(self, client, mock_supabase_client):
        """Test filtering by importance score."""
        mock_supabase_client.table().select().eq().gte().order().limit().execute.return_value.data = []
        
        response = client.get("/api/memory/longterm?user_id=test-user&min_importance=0.9")
        
        assert response.status_code == 200
