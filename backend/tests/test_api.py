"""Basic API tests"""
import pytest
from fastapi.testclient import TestClient
from app.simple_app import app

client = TestClient(app)


class TestHealthCheck:
    """Health check endpoint tests"""
    
    def test_health_check_status_code(self):
        """Test health check returns 200"""
        response = client.get("/health")
        assert response.status_code == 200
    
    def test_health_check_response_body(self):
        """Test health check returns correct JSON structure"""
        response = client.get("/health")
        data = response.json()
        assert "status" in data
        assert data["status"] == "ok"
        assert "message" in data


class TestRootEndpoint:
    """Root endpoint tests"""
    
    def test_root_status_code(self):
        """Test root endpoint returns 200"""
        response = client.get("/")
        assert response.status_code == 200
    
    def test_root_response_body(self):
        """Test root endpoint returns correct data"""
        response = client.get("/")
        data = response.json()
        assert "message" in data
        assert "Stock Analysis System" in data["message"]


class TestDocsEndpoint:
    """Documentation endpoint tests"""
    
    def test_docs_status_code(self):
        """Test docs endpoint returns 200"""
        response = client.get("/docs")
        assert response.status_code == 200
    
    def test_docs_contains_swagger_ui(self):
        """Test docs endpoint returns HTML with Swagger UI"""
        response = client.get("/docs")
        assert response.status_code == 200
        # Swagger UI should be in the response
        assert "swagger-ui" in response.text.lower() or "<!doctype html>" in response.text.lower()


class TestOpenAPI:
    """OpenAPI schema tests"""
    
    def test_openapi_schema_available(self):
        """Test OpenAPI schema endpoint is available"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data or "swagger" in data
