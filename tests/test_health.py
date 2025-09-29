from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/api/v1/health")
    # Note: This test assumes Firebase is properly configured
    # In a real scenario, mock the database connection
    assert response.status_code in [200, 503]  # 200 if connected, 503 if not
    data = response.json()
    assert "status" in data
    if response.status_code == 200:
        assert data["status"] == "healthy"
        assert data["database"] == "connected"