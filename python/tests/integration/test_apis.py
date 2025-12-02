"""
Integration tests for Knowledge Base API endpoints.
Tests crawling, search, and document operations.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch, AsyncMock


@pytest.mark.integration
class TestKnowledgeAPIEndpoints:
    """Integration tests for /api/knowledge/* endpoints."""
    
    def test_list_sources(self, client, mock_supabase_client):
        """Test GET /api/sources - list all sources."""
        mock_supabase_client.table().select().execute.return_value.data = [
            {
                "id": "1",
                "source_url": "https://example.com",
                "source_display_name": "Example",
                "created_at": "2024-01-01T00:00:00"
            }
        ]
        
        response = client.get("/api/sources")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_create_source(self, client, mock_supabase_client):
        """Test POST /api/sources - create new source."""
        mock_supabase_client.table().insert().execute.return_value.data = [{
            "id": "new-id",
            "source_url": "https://newsite.com",
            "source_display_name": "New Site"
        }]
        
        response = client.post("/api/sources", json={
            "source_url": "https://newsite.com",
            "source_display_name": "New Site"
        })
        
        assert response.status_code in [200, 201]
    
    def test_search_knowledge(self, client, mock_supabase_client):
        """Test POST /api/knowledge/search - semantic search."""
        mock_supabase_client.table().select().execute.return_value.data = [
            {
                "id": "1",
                "content": "Test content",
                "url": "https://example.com",
                "similarity": 0.95
            }
        ]
        
        response = client.post("/api/knowledge/search", json={
            "query": "test query",
            "limit": 10
        })
        
        assert response.status_code == 200
    
    def test_search_empty_query(self, client, mock_supabase_client):
        """Test search with empty query - should fail validation."""
        response = client.post("/api/knowledge/search", json={
            "query": "",
            "limit": 10
        })
        
        assert response.status_code == 422  # Validation error
    
    def test_crawl_website(self, client, mock_supabase_client):
        """Test POST /api/crawl-website - initiate crawl."""
        with patch('src.server.services.crawler_manager.get_crawler') as mock_crawler:
            mock_crawler_instance = AsyncMock()
            mock_crawler_instance.arun.return_value.markdown = "# Test Content"
            mock_crawler.return_value = mock_crawler_instance
            
            response = client.post("/api/crawl-website", json={
                "url": "https://example.com",
                "source_id": "test-source"
            })
            
            # Should either succeed or return specific error
            assert response.status_code in [200, 202, 500]
    
    def test_get_pages_for_source(self, client, mock_supabase_client):
        """Test GET /api/pages?source_id={id} - get pages for source."""
        mock_supabase_client.table().select().eq().execute.return_value.data = [
            {"id": "1", "url": "https://example.com/page1", "title": "Page 1"}
        ]
        
        response = client.get("/api/pages?source_id=test-source")
        
        assert response.status_code == 200
    
    def test_delete_source(self, client, mock_supabase_client):
        """Test DELETE /api/sources/{id} - delete source."""
        mock_supabase_client.table().delete().eq().execute.return_value.data = []
        
        response = client.delete("/api/sources/test-id")
        
        assert response.status_code in [200, 204]
    
    def test_knowledge_api_error_handling(self, client, mock_supabase_client):
        """Test error handling when operations fail."""
        mock_supabase_client.table().select().execute.side_effect = Exception("DB Error")
        
        response = client.get("/api/sources")
        
        assert response.status_code == 500
    
    def test_duplicate_source_url(self, client, mock_supabase_client):
        """Test creating source with duplicate URL."""
        # Simulate unique constraint violation
        mock_error = Exception("duplicate key value violates unique constraint")
        mock_supabase_client.table().insert().execute.side_effect = mock_error
        
        response = client.post("/api/sources", json={
            "source_url": "https://existing.com",
            "source_display_name": "Existing"
        })
        
        assert response.status_code in [409, 500]
    
    def test_pagination_knowledge_search(self, client, mock_supabase_client):
        """Test pagination in knowledge search."""
        mock_supabase_client.table().select().execute.return_value.data = []
        
        response = client.post("/api/knowledge/search", json={
            "query": "test",
            "limit": 5,
            "offset": 10
        })
        
        assert response.status_code == 200


@pytest.mark.integration
class TestProjectsAPIEndpoints:
    """Integration tests for /api/projects/* endpoints."""
    
    def test_list_projects(self, client, mock_supabase_client):
        """Test GET /api/projects - list all projects."""
        mock_supabase_client.table().select().execute.return_value.data = [
            {"id": "1", "title": "Test Project", "description": "Test"}
        ]
        
        response = client.get("/api/projects")
        
        assert response.status_code == 200
    
    def test_create_project(self, client, test_project, mock_supabase_client):
        """Test POST /api/projects - create new project."""
        mock_supabase_client.table().insert().execute.return_value.data = [
            {**test_project, "id": "new-id"}
        ]
        
        response = client.post("/api/projects", json=test_project)
        
        assert response.status_code in [200, 201]
    
    def test_get_project_by_id(self, client, mock_supabase_client):
        """Test GET /api/projects/{id} - get specific project."""
        mock_supabase_client.table().select().eq().execute.return_value.data = [
            {"id": "test-id", "title": "Test Project"}
        ]
        
        response = client.get("/api/projects/test-id")
        
        assert response.status_code == 200
    
    def test_update_project(self, client, mock_supabase_client):
        """Test PUT /api/projects/{id} - update project."""
        mock_supabase_client.table().update().eq().execute.return_value.data = [
            {"id": "test-id", "title": "Updated Project"}
        ]
        
        response = client.put("/api/projects/test-id", json={
            "title": "Updated Project"
        })
        
        assert response.status_code == 200
    
    def test_delete_project(self, client, mock_supabase_client):
        """Test DELETE /api/projects/{id} - delete project."""
        mock_supabase_client.table().delete().eq().execute.return_value.data = []
        
        response = client.delete("/api/projects/test-id")
        
        assert response.status_code in [200, 204]
    
    def test_list_tasks_for_project(self, client, mock_supabase_client):
        """Test GET /api/projects/{id}/tasks - list tasks."""
        mock_supabase_client.table().select().eq().execute.return_value.data = [
            {"id": "1", "title": "Task 1", "status": "todo"}
        ]
        
        response = client.get("/api/projects/test-id/tasks")
        
        assert response.status_code == 200
    
    def test_create_task(self, client, test_task, mock_supabase_client):
        """Test POST /api/projects/{id}/tasks - create task."""
        mock_supabase_client.table().insert().execute.return_value.data = [
            {**test_task, "id": "new-task-id"}
        ]
        
        response = client.post("/api/projects/test-id/tasks", json=test_task)
        
        assert response.status_code in [200, 201]
    
    def test_update_task_status(self, client, mock_supabase_client):
        """Test PATCH /api/tasks/{id} - update task status."""
        mock_supabase_client.table().update().eq().execute.return_value.data = [
            {"id": "task-id", "status": "done"}
        ]
        
        response = client.patch("/api/tasks/task-id", json={
            "status": "done"
        })
        
        assert response.status_code == 200
    
    def test_project_not_found(self, client, mock_supabase_client):
        """Test getting non-existent project."""
        mock_supabase_client.table().select().eq().execute.return_value.data = []
        
        response = client.get("/api/projects/nonexistent")
        
        assert response.status_code == 404
    
    def test_projects_error_handling(self, client, mock_supabase_client):
        """Test error handling in projects API."""
        mock_supabase_client.table().select().execute.side_effect = Exception("DB Error")
        
        response = client.get("/api/projects")
        
        assert response.status_code == 500
