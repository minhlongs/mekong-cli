"""
Integration tests for Behavior Graph API endpoints.

Tests the FastAPI graph_router with real database operations.
Requires PostgreSQL connection configured via DATABASE_URL.
"""

from __future__ import annotations

import sys
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.api.graph_router import graph_router
from src.graph.service import get_graph_service


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def should_skip_integration():
    """Check if integration tests should be skipped."""
    import os
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        pytest.skip("DATABASE_URL not set - skipping integration tests")
    return False


@pytest.fixture()
async def graph_app_with_db(should_skip_integration):
    """Create FastAPI app with real database connection."""
    from src.db.database import init_database, close_database
    from src.graph.repository import init_graph_repository

    if should_skip_integration:
        pytest.skip("Integration tests disabled")

    # Initialize database
    await init_database()

    # Run migrations if needed
    try:
        from src.db.migrate import MigrationRunner
        runner = MigrationRunner()
        await runner.run_migrations()
    except Exception as e:
        pytest.skip(f"Migration failed: {e}")

    # Initialize graph repository
    await init_graph_repository()

    # Create app with graph router
    app = FastAPI()
    app.include_router(graph_router)

    yield app

    # Cleanup
    await close_database()


@pytest.fixture()
def graph_client(graph_app_with_db):
    """TestClient for graph API."""
    return TestClient(graph_app_with_db, raise_server_exceptions=False)


@pytest.fixture()
async def graph_service_real():
    """Real service instance for direct testing."""
    from src.db.database import init_database, close_database
    await init_database()
    service = get_graph_service()
    yield service
    await close_database()


# ============================================================================
# Entity API Tests
# ============================================================================

class TestEntityAPI:
    """Tests for entity endpoints."""

    def test_create_entity(self, graph_client):
        """Test POST /api/v1/graph/entities."""
        response = graph_client.post(
            "/api/v1/graph/entities",
            json={
                "type": "user",
                "name": "Integration Test User",
                "description": "Created by integration test",
                "properties": {"test": True, "source": "integration"}
            }
        )

        assert response.status_code == 201, f"Failed: {response.text}"
        data = response.json()
        assert data["id"] is not None
        assert data["type"] == "user"
        assert data["name"] == "Integration Test User"
        assert data["properties"]["test"] is True

        # Cleanup
        graph_client.delete(f"/api/v1/graph/entities/{data['id']}")

    def test_get_entity(self, graph_client):
        """Test GET /api/v1/graph/entities/{id}."""
        # First create
        create_response = graph_client.post(
            "/api/v1/graph/entities",
            json={
                "type": "agent",
                "name": "GetTest Agent",
                "properties": {"capabilities": ["test"]}
            }
        )
        assert create_response.status_code == 201
        entity_id = create_response.json()["id"]

        # Then get
        response = graph_client.get(f"/api/v1/graph/entities/{entity_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == entity_id
        assert data["type"] == "agent"

        # Cleanup
        graph_client.delete(f"/api/v1/graph/entities/{entity_id}")

    def test_list_entities(self, graph_client):
        """Test GET /api/v1/graph/entities."""
        # Create multiple entities
        for i in range(3):
            graph_client.post(
                "/api/v1/graph/entities",
                json={
                    "type": "tool" if i % 2 == 0 else "concept",
                    "name": f"List Test {i}",
                }
            )

        response = graph_client.get("/api/v1/graph/entities?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3

    def test_update_entity(self, graph_client):
        """Test PUT /api/v1/graph/entities/{id}."""
        # Create entity
        create_response = graph_client.post(
            "/api/v1/graph/entities",
            json={
                "type": "user",
                "name": "Update Test User",
                "description": "Original description"
            }
        )
        entity_id = create_response.json()["id"]

        # Update
        response = graph_client.put(
            f"/api/v1/graph/entities/{entity_id}",
            json={
                "name": "Updated User Name",
                "properties": {"updated": True}
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated User Name"
        assert data["properties"]["updated"] is True

        # Cleanup
        graph_client.delete(f"/api/v1/graph/entities/{entity_id}")

    def test_delete_entity(self, graph_client):
        """Test DELETE /api/v1/graph/entities/{id}."""
        # Create entity
        create_response = graph_client.post(
            "/api/v1/graph/entities",
            json={"type": "concept", "name": "To Delete"}
        )
        entity_id = create_response.json()["id"]

        # Delete
        response = graph_client.delete(f"/api/v1/graph/entities/{entity_id}")
        assert response.status_code == 204

        # Verify deleted
        get_response = graph_client.get(f"/api/v1/graph/entities/{entity_id}")
        assert get_response.status_code == 404


# ============================================================================
# Behavior API Tests
# ============================================================================

class TestBehaviorAPI:
    """Tests for behavior endpoints."""

    def test_record_behavior(self, graph_client):
        """Test POST /api/v1/graph/behaviors."""
        # Create entity first
        entity_response = graph_client.post(
            "/api/v1/graph/entities",
            json={"type": "user", "name": "Behavior Test User"}
        )
        entity_id = entity_response.json()["id"]

        # Record behavior
        response = graph_client.post(
            "/api/v1/graph/behaviors",
            json={
                "entity_id": entity_id,
                "action_type": "test_action",
                "context": {"test": True},
                "outcome": {"result": "success"},
                "confidence": 0.95
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["entity_id"] == entity_id
        assert data["action_type"] == "test_action"

        # Cleanup
        graph_client.delete(f"/api/v1/graph/entities/{entity_id}")

    def test_get_entity_behaviors(self, graph_client):
        """Test GET /api/v1/graph/entities/{id}/behaviors."""
        entity_response = graph_client.post(
            "/api/v1/graph/entities",
            json={"type": "agent", "name": "Behavior Query Agent"}
        )
        entity_id = entity_response.json()["id"]

        # Record multiple behaviors
        for i in range(3):
            graph_client.post(
                "/api/v1/graph/behaviors",
                json={
                    "entity_id": entity_id,
                    "action_type": f"action_{i}",
                    "confidence": 0.8 + (i * 0.05)
                }
            )

        response = graph_client.get(f"/api/v1/graph/entities/{entity_id}/behaviors?days=30")
        assert response.status_code == 200
        data = response.json()
        assert "behaviors" in data
        assert len(data["behaviors"]) >= 3
        assert data["total_actions"] >= 3

        # Cleanup
        graph_client.delete(f"/api/v1/graph/entities/{entity_id}")


# ============================================================================
# Trust API Tests
# ============================================================================

class TestTrustAPI:
    """Tests for trust endpoints."""

    def test_set_trust(self, graph_client):
        """Test POST /api/v1/graph/trust."""
        # Create entities
        user_response = graph_client.post(
            "/api/v1/graph/entities",
            json={"type": "user", "name": "Trusting User"}
        )
        agent_response = graph_client.post(
            "/api/v1/graph/entities",
            json={"type": "agent", "name": "Trusted Agent"}
        )
        user_id = user_response.json()["id"]
        agent_id = agent_response.json()["id"]

        # Set trust
        response = graph_client.post(
            "/api/v1/graph/trust",
            json={
                "source_id": user_id,
                "target_id": agent_id,
                "score": 0.85,
                "rationale": "Reliable performance"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["source_id"] == user_id
        assert data["target_id"] == agent_id
        assert data["score"] == 0.85

        # Cleanup
        graph_client.delete(f"/api/v1/graph/entities/{user_id}")
        graph_client.delete(f"/api/v1/graph/entities/{agent_id}")

    def test_get_trust_network(self, graph_client):
        """Test GET /api/v1/graph/entities/{id}/trust."""
        response = graph_client.get("/api/v1/graph/entities/non-existent/trust")
        assert response.status_code == 404


# ============================================================================
# Intent API Tests
# ============================================================================

class TestIntentAPI:
    """Tests for intent endpoints."""

    def test_create_intent(self, graph_client):
        """Test POST /api/v1/graph/intents."""
        entity_response = graph_client.post(
            "/api/v1/graph/entities",
            json={"type": "user", "name": "Intent User"}
        )
        entity_id = entity_response.json()["id"]

        response = graph_client.post(
            "/api/v1/graph/intents",
            json={
                "entity_id": entity_id,
                "intent_type": "purchase",
                "description": "Wants to buy premium plan",
                "confidence": 0.9,
                "related_entities": ["plan-premium"]
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["intent_type"] == "purchase"
        assert data["status"] == "active"

        # Cleanup
        graph_client.delete(f"/api/v1/graph/entities/{entity_id}")

    def test_get_active_intents(self, graph_client):
        """Test GET /api/v1/graph/intents/active."""
        response = graph_client.get("/api/v1/graph/intents/active")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


# ============================================================================
# Prediction API Tests
# ============================================================================

class TestPredictionAPI:
    """Tests for prediction endpoints."""

    def test_create_prediction(self, graph_client):
        """Test POST /api/v1/graph/predictions."""
        entity_response = graph_client.post(
            "/api/v1/graph/entities",
            json={"type": "user", "name": "Prediction User"}
        )
        entity_id = entity_response.json()["id"]

        response = graph_client.post(
            "/api/v1/graph/predictions",
            json={
                "entity_id": entity_id,
                "prediction_type": "churn_risk",
                "value": {"risk_score": 0.3, "category": "low"},
                "confidence": 0.85,
                "model_version": "churn-v1.0",
                "features": {"login_frequency": "daily"}
            }
        )
        assert response.status_code == 201

        # Cleanup
        graph_client.delete(f"/api/v1/graph/entities/{entity_id}")

    def test_get_predictions(self, graph_client):
        """Test GET /api/v1/graph/predictions."""
        response = graph_client.get("/api/v1/graph/predictions?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert "predictions" in data
        assert isinstance(data["predictions"], list)


# ============================================================================
# Action API Tests
# ============================================================================

class TestActionAPI:
    """Tests for action endpoints."""

    def test_create_action(self, graph_client):
        """Test POST /api/v1/graph/actions."""
        entity_response = graph_client.post(
            "/api/v1/graph/entities",
            json={"type": "user", "name": "Action User"}
        )
        entity_id = entity_response.json()["id"]

        response = graph_client.post(
            "/api/v1/graph/actions",
            json={
                "entity_id": entity_id,
                "action_type": "send_notification",
                "description": "Send welcome email",
                "parameters": {"template": "welcome"},
                "priority": 5
            }
        )
        assert response.status_code == 201

        # Cleanup
        graph_client.delete(f"/api/v1/graph/entities/{entity_id}")

    def test_get_pending_actions(self, graph_client):
        """Test GET /api/v1/graph/actions/pending."""
        response = graph_client.get("/api/v1/graph/actions/pending?min_priority=1")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


# ============================================================================
# GraphRAG API Tests
# ============================================================================

class TestGraphRAGAPI:
    """Tests for GraphRAG endpoints."""

    def test_enrich_query(self, graph_client):
        """Test POST /api/v1/graph/rag/enrich."""
        response = graph_client.post(
            "/api/v1/graph/rag/enrich",
            json={
                "query": "What are user preferences?",
                "max_entities": 5,
                "max_behaviors": 20
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "query" in data
        assert "relevant_entities" in data
        assert "context_string" in data

    def test_get_llm_context(self, graph_client):
        """Test POST /api/v1/graph/rag/context."""
        response = graph_client.post(
            "/api/v1/graph/rag/context",
            json={
                "query": "Recommend products",
                "max_entities": 3
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert isinstance(data["summary"], str)


# ============================================================================
# Graph Statistics API Tests
# ============================================================================

class TestGraphStatsAPI:
    """Tests for graph statistics endpoint."""

    def test_get_graph_stats(self, graph_client):
        """Test GET /api/v1/graph/stats."""
        response = graph_client.get("/api/v1/graph/stats")
        assert response.status_code == 200
        data = response.json()
        assert "entities" in data
        assert "edges" in data
        assert isinstance(data["entities"], (int, type(None)))


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestErrorHandling:
    """Tests for error handling."""

    def test_entity_not_found(self, graph_client):
        """Test 404 for non-existent entity."""
        response = graph_client.get("/api/v1/graph/entities/does-not-exist")
        assert response.status_code == 404

    def test_invalid_trust_score(self, graph_client):
        """Test validation error for invalid trust score."""
        response = graph_client.post(
            "/api/v1/graph/trust",
            json={
                "source_id": "user-001",
                "target_id": "agent-001",
                "score": 2.0  # Invalid: > 1.0
            }
        )
        assert response.status_code == 422  # Validation error

    def test_missing_required_fields(self, graph_client):
        """Test validation error for missing required fields."""
        response = graph_client.post(
            "/api/v1/graph/entities",
            json={"type": "user"}  # Missing name
        )
        assert response.status_code == 422


__all__ = [
    "TestEntityAPI",
    "TestBehaviorAPI",
    "TestTrustAPI",
    "TestIntentAPI",
    "TestPredictionAPI",
    "TestActionAPI",
    "TestGraphRAGAPI",
    "TestGraphStatsAPI",
    "TestErrorHandling",
]
