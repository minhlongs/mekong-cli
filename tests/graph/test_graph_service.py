"""
Tests for Behavior Graph Service.

Simplified unit tests using mock repository pattern.
"""

from __future__ import annotations

import sys
from pathlib import Path
from datetime import datetime, timezone

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.graph.models import (
    Entity,
    EntityCreate,
    Behavior,
    BehaviorCreate,
    Trust,
    TrustCreate,
    Intent,
    Prediction,
    Action,
    ActionCreate,
)
from src.graph.service import BehaviorGraphService


# ============================================================================
# Mock Repository Class
# ============================================================================

class MockGraphRepository:
    """Mock repository for testing service layer."""

    def __init__(self):
        self.entities: dict[str, dict] = {}
        self.behaviors: list[dict] = []
        self.trust_rels: dict[tuple[str, str], dict] = {}
        self.intents: list[dict] = []
        self.predictions: list[dict] = []
        self.actions: list[dict] = []
        self.edges: list[dict] = []

    async def create_entity(self, entity_type, name, entity_id=None, description=None, properties=None):
        eid = entity_id or f"entity-{len(self.entities)+1}"
        data = {
            "id": eid,
            "type": entity_type,
            "name": name,
            "description": description,
            "properties": properties or {},
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        self.entities[eid] = data
        return data

    async def get_entity(self, entity_id):
        return self.entities.get(entity_id)

    async def update_entity(self, entity_id, updates):
        if entity_id not in self.entities:
            return False
        self.entities[entity_id].update(updates)
        self.entities[entity_id]["updated_at"] = datetime.now(timezone.utc)
        return True

    async def delete_entity(self, entity_id):
        if entity_id not in self.entities:
            return False
        del self.entities[entity_id]
        # Cascade delete related records
        self.edges = [e for e in self.edges if e["source_id"] != entity_id and e["target_id"] != entity_id]
        self.behaviors = [b for b in self.behaviors if b["entity_id"] != entity_id]
        self.intents = [i for i in self.intents if i["entity_id"] != entity_id]
        self.predictions = [p for p in self.predictions if p["entity_id"] != entity_id]
        self.actions = [a for a in self.actions if a["entity_id"] != entity_id]
        return True

    async def list_entities(self, entity_type=None, name_contains=None, limit=100, offset=0):
        entities = list(self.entities.values())
        if entity_type:
            entities = [e for e in entities if e["type"] == entity_type]
        if name_contains:
            entities = [e for e in entities if name_contains.lower() in e["name"].lower()]
        return entities[offset:offset+limit]

    async def create_edge(self, source_id, target_id, edge_type, weight=1.0, properties=None):
        edge = {
            "source_id": source_id,
            "target_id": target_id,
            "edge_type": edge_type,
            "weight": weight,
            "properties": properties or {},
            "created_at": datetime.now(timezone.utc),
        }
        self.edges.append(edge)
        return edge

    async def get_neighbors(self, entity_id, edge_type=None, direction="outgoing"):
        neighbors = []
        for edge in self.edges:
            if direction == "outgoing" and edge["source_id"] == entity_id:
                if edge_type and edge["edge_type"] != edge_type:
                    continue
                target_id = edge["target_id"]
                if target_id in self.entities:
                    neighbors.append({**self.entities[target_id], "edge_type": edge["edge_type"], "weight": edge["weight"]})
            elif direction == "incoming" and edge["target_id"] == entity_id:
                if edge_type and edge["edge_type"] != edge_type:
                    continue
                source_id = edge["source_id"]
                if source_id in self.entities:
                    neighbors.append({**self.entities[source_id], "edge_type": edge["edge_type"], "weight": edge["weight"]})
        return neighbors

    async def get_multi_hop_neighbors(self, entity_id, max_depth=2, edge_types=None):
        nodes = []
        visited = {entity_id}
        queue = [(entity_id, 1)]

        while queue:
            current, depth = queue.pop(0)
            if depth > max_depth:
                continue

            for edge in self.edges:
                if edge["source_id"] == current:
                    next_id = edge["target_id"]
                    if next_id not in visited:
                        visited.add(next_id)
                        queue.append((next_id, depth + 1))
                        if next_id in self.entities:
                            nodes.append({
                                "id": next_id,
                                "type": self.entities[next_id]["type"],
                                "name": self.entities[next_id]["name"],
                                "properties": self.entities[next_id]["properties"],
                                "edge_type": edge["edge_type"],
                                "weight": edge["weight"],
                                "depth": depth
                            })

        return {"center": entity_id, "max_depth": max_depth, "nodes": nodes, "count": len(nodes)}

    async def record_behavior(self, entity_id, action_type, behavior_id=None, context=None, outcome=None, confidence=1.0, metadata=None):
        bid = behavior_id or f"behavior-{len(self.behaviors)+1}"
        data = {
            "id": bid,
            "entity_id": entity_id,
            "action_type": action_type,
            "context": context or {},
            "outcome": outcome,
            "confidence": confidence,
            "metadata": metadata or {},
            "timestamp": datetime.now(timezone.utc),
        }
        self.behaviors.append(data)
        return data

    async def get_behaviors(self, entity_id=None, action_type=None, start_date=None, end_date=None, limit=100):
        results = self.behaviors
        if entity_id:
            results = [b for b in results if b["entity_id"] == entity_id]
        if action_type:
            results = [b for b in results if b["action_type"] == action_type]
        if start_date:
            results = [b for b in results if b["timestamp"] >= start_date]
        if end_date:
            results = [b for b in results if b["timestamp"] <= end_date]
        return sorted(results, key=lambda x: x["timestamp"], reverse=True)[:limit]

    async def get_entity_behavior_stats(self, entity_id, days=30):
        entity_behaviors = [b for b in self.behaviors if b["entity_id"] == entity_id]
        if not entity_behaviors:
            return {"total_behaviors": 0, "unique_action_types": 0, "first_seen": None, "last_seen": None, "action_types": []}
        action_types = list(set(b["action_type"] for b in entity_behaviors))
        return {
            "total_behaviors": len(entity_behaviors),
            "unique_action_types": len(action_types),
            "first_seen": min(b["timestamp"] for b in entity_behaviors),
            "last_seen": max(b["timestamp"] for b in entity_behaviors),
            "action_types": action_types,
        }

    async def set_trust(self, source_id, target_id, score, weight=1.0, rationale=None, evidence=None, trust_id=None):
        key = (source_id, target_id)
        data = {
            "id": trust_id or f"trust-{len(self.trust_rels)+1}",
            "source_id": source_id,
            "target_id": target_id,
            "score": score,
            "weight": weight,
            "rationale": rationale,
            "evidence": evidence or [],
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        self.trust_rels[key] = data
        return data

    async def get_trust(self, source_id, target_id):
        return self.trust_rels.get((source_id, target_id))

    async def get_trust_network(self, entity_id, direction="both"):
        result = {"entity_id": entity_id, "trusted_by": [], "trusts": []}

        for (src, tgt), trust in self.trust_rels.items():
            if tgt == entity_id and direction in ["incoming", "both"]:
                result["trusted_by"].append({**trust, "source_name": self.entities.get(src, {}).get("name", "Unknown"), "source_type": self.entities.get(src, {}).get("type", "unknown")})
            if src == entity_id and direction in ["outgoing", "both"]:
                result["trusts"].append({**trust, "target_name": self.entities.get(tgt, {}).get("name", "Unknown"), "target_type": self.entities.get(tgt, {}).get("type", "unknown")})

        incoming_avg = sum(t["score"] for t in result["trusted_by"]) / max(1, len(result["trusted_by"]))
        outgoing_avg = sum(t["score"] for t in result["trusts"]) / max(1, len(result["trusts"]))
        result["aggregated_score"] = (incoming_avg + outgoing_avg) / 2
        return result

    async def create_intent(self, entity_id, intent_type, description, intent_id=None, confidence=1.0, related_entities=None, expires_at=None, status="active"):
        iid = intent_id or f"intent-{len(self.intents)+1}"
        data = {
            "id": iid,
            "entity_id": entity_id,
            "intent_type": intent_type,
            "description": description,
            "confidence": confidence,
            "status": status,
            "related_entities": related_entities or [],
            "expires_at": expires_at,
            "created_at": datetime.now(timezone.utc),
        }
        self.intents.append(data)
        return data

    async def update_intent_status(self, intent_id, status):
        for intent in self.intents:
            if intent["id"] == intent_id:
                intent["status"] = status
                return True
        return False

    async def get_active_intents(self, entity_id=None, intent_type=None):
        results = [i for i in self.intents if i["status"] == "active"]
        if entity_id:
            results = [i for i in results if i["entity_id"] == entity_id]
        if intent_type:
            results = [i for i in results if i["intent_type"] == intent_type]
        return sorted(results, key=lambda x: x["confidence"], reverse=True)

    async def create_prediction(self, entity_id, prediction_type, value, confidence, model_version, prediction_id=None, features=None, expires_at=None):
        pid = prediction_id or f"prediction-{len(self.predictions)+1}"
        data = {
            "id": pid,
            "entity_id": entity_id,
            "prediction_type": prediction_type,
            "value": value,
            "confidence": confidence,
            "features": features or {},
            "model_version": model_version,
            "validated": False,
            "created_at": datetime.now(timezone.utc),
            "expires_at": expires_at,
        }
        self.predictions.append(data)
        return data

    async def validate_prediction(self, prediction_id, actual_outcome):
        for pred in self.predictions:
            if pred["id"] == prediction_id:
                pred["validated"] = True
                pred["actual_outcome"] = actual_outcome
                return True
        return False

    async def get_predictions(self, entity_id=None, prediction_type=None, validated=None, limit=100):
        results = self.predictions
        if entity_id:
            results = [p for p in results if p["entity_id"] == entity_id]
        if prediction_type:
            results = [p for p in results if p["prediction_type"] == prediction_type]
        if validated is not None:
            results = [p for p in results if p["validated"] == validated]
        return sorted(results, key=lambda x: x["created_at"], reverse=True)[:limit]

    async def create_action(self, entity_id, action_type, description, action_id=None, parameters=None, priority=1, status="pending", context=None, reasoning=None):
        aid = action_id or f"action-{len(self.actions)+1}"
        data = {
            "id": aid,
            "entity_id": entity_id,
            "action_type": action_type,
            "description": description,
            "parameters": parameters or {},
            "priority": priority,
            "status": status,
            "context": context or {},
            "reasoning": reasoning,
            "created_at": datetime.now(timezone.utc),
            "executed_at": None,
        }
        self.actions.append(data)
        return data

    async def update_action_status(self, action_id, status, reasoning=None, executed_at=None):
        for action in self.actions:
            if action["id"] == action_id:
                action["status"] = status
                if reasoning:
                    action["reasoning"] = reasoning
                if executed_at:
                    action["executed_at"] = executed_at
                return True
        return False

    async def get_pending_actions(self, entity_id=None, min_priority=1, limit=50):
        results = [a for a in self.actions if a["status"] == "pending" and a["priority"] >= min_priority]
        if entity_id:
            results = [a for a in results if a["entity_id"] == entity_id]
        return sorted(results, key=lambda x: (x["priority"], x["created_at"]), reverse=True)[:limit]

    async def get_entity_centrality(self, entity_id):
        out_degree = sum(1 for e in self.edges if e["source_id"] == entity_id)
        in_degree = sum(1 for e in self.edges if e["target_id"] == entity_id)
        return {"out_degree": out_degree, "in_degree": in_degree, "total_degree": out_degree + in_degree}

    async def get_graph_stats(self):
        return {
            "entities": len(self.entities),
            "edges": len(self.edges),
            "behaviors": len(self.behaviors),
            "trust_rels": len(self.trust_rels),
            "intents": len(self.intents),
            "predictions": len(self.predictions),
            "actions": len(self.actions),
            "entity_types": {},
        }

    async def find_similar_entities(self, entity_id, similarity_threshold=0.5, limit=10):
        """Find entities with overlapping behavior types."""
        if entity_id not in self.entities:
            return []

        ref_behaviors = [b for b in self.behaviors if b["entity_id"] == entity_id]
        ref_action_types = set(b["action_type"] for b in ref_behaviors)

        if not ref_action_types:
            return []

        results = []
        for eid, entity in self.entities.items():
            if eid == entity_id:
                continue
            entity_behaviors = [b for b in self.behaviors if b["entity_id"] == eid]
            entity_action_types = set(b["action_type"] for b in entity_behaviors)
            shared = ref_action_types.intersection(entity_action_types)
            if shared:
                similarity = len(shared) / len(ref_action_types)
                if similarity >= similarity_threshold:
                    results.append({
                        "id": eid,
                        "type": entity["type"],
                        "name": entity["name"],
                        "properties": entity["properties"],
                        "similarity_score": similarity,
                        "action_types": list(shared)
                    })

        return sorted(results, key=lambda x: x["similarity_score"], reverse=True)[:limit]


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture()
def mock_repo():
    """Fresh mock repository for each test."""
    return MockGraphRepository()


@pytest.fixture()
def graph_service(mock_repo):
    """Service with mock repository."""
    return BehaviorGraphService(repository=mock_repo)


# ============================================================================
# Entity Tests
# ============================================================================

class TestEntityOperations:
    """Tests for entity CRUD operations."""

    @pytest.mark.asyncio()
    async def test_create_entity(self, graph_service, mock_repo):
        result = await graph_service.upsert_entity(
            entity_type="user",
            name="Test User",
            description="A test entity",
            properties={"role": "admin"}
        )
        assert isinstance(result, Entity)
        assert result.name == "Test User"
        assert result.type == "user"
        assert result.properties["role"] == "admin"
        assert len(mock_repo.entities) == 1

    async def test_get_entity_found(self, graph_service, mock_repo):
        await mock_repo.create_entity(entity_type="user", name="Find Me", entity_id="find-me-id")
        result = await graph_service.get_entity("find-me-id")
        assert result is not None
        assert result.id == "find-me-id"
        assert result.name == "Find Me"

    @pytest.mark.asyncio()
    async def test_get_entity_not_found(self, graph_service, mock_repo):
        result = await graph_service.get_entity("non-existent")
        assert result is None

    @pytest.mark.asyncio()
    async def test_delete_entity(self, graph_service, mock_repo):
        await mock_repo.create_entity(entity_type="user", name="Delete Me", entity_id="delete-me-id")
        assert "delete-me-id" in mock_repo.entities
        success = await graph_service.delete_entity("delete-me-id")
        assert success is True
        assert "delete-me-id" not in mock_repo.entities

    @pytest.mark.asyncio()
    async def test_link_entities(self, graph_service, mock_repo):
        user = await mock_repo.create_entity(entity_type="user", name="User")
        agent = await mock_repo.create_entity(entity_type="agent", name="Agent")
        edge = await graph_service.link_entities(
            source_id=user["id"],
            target_id=agent["id"],
            edge_type="trusts",
            weight=0.9
        )
        assert edge.source_id == user["id"]
        assert edge.target_id == agent["id"]
        assert edge.edge_type == "trusts"
        assert edge.weight == 0.9
        assert len(mock_repo.edges) == 1


# ============================================================================
# Behavior Tests
# ============================================================================

class TestBehaviorOperations:
    """Tests for behavior operations."""

    @pytest.mark.asyncio()
    async def test_record_behavior(self, graph_service, mock_repo):
        entity = await mock_repo.create_entity(entity_type="user", name="Behavior User")
        behavior = await graph_service.record_behavior(
            entity_id=entity["id"],
            action_type="login",
            context={"ip": "127.0.0.1"},
            outcome={"success": True},
            confidence=0.95
        )
        assert isinstance(behavior, Behavior)
        assert behavior.action_type == "login"
        assert behavior.entity_id == entity["id"]
        assert len(mock_repo.behaviors) == 1

    @pytest.mark.asyncio()
    async def test_get_behavior_history(self, graph_service, mock_repo):
        entity = await mock_repo.create_entity(entity_type="user", name="History User")
        for i in range(5):
            await mock_repo.record_behavior(
                entity_id=entity["id"],
                action_type=f"action_{i % 3}",
                confidence=0.8
            )
        history = await graph_service.get_behavior_history(entity["id"], days=30)
        assert history.entity.id == entity["id"]
        assert history.total_actions == 5
        assert len(history.behaviors) == 5

    @pytest.mark.asyncio()
    async def test_empty_behavior_history(self, graph_service, mock_repo):
        entity = await mock_repo.create_entity(entity_type="user", name="No Behavior User")
        history = await graph_service.get_behavior_history(entity["id"], days=30)
        assert history.total_actions == 0
        assert history.behaviors == []


# ============================================================================
# Trust Tests
# ============================================================================

class TestTrustOperations:
    """Tests for trust relationship operations."""

    @pytest.mark.asyncio()
    async def test_set_trust(self, graph_service, mock_repo):
        user = await mock_repo.create_entity(entity_type="user", name="Trusting User")
        agent = await mock_repo.create_entity(entity_type="agent", name="Trusted Agent")
        trust = await graph_service.update_trust(
            source_id=user["id"],
            target_id=agent["id"],
            score=0.85,
            rationale="Excellent performance"
        )
        assert isinstance(trust, Trust)
        assert trust.score == 0.85
        assert trust.source_id == user["id"]
        assert trust.target_id == agent["id"]

    @pytest.mark.asyncio()
    async def test_get_trust_network(self, graph_service, mock_repo):
        user = await mock_repo.create_entity(entity_type="user", name="Network User")
        agent1 = await mock_repo.create_entity(entity_type="agent", name="Agent 1")
        agent2 = await mock_repo.create_entity(entity_type="agent", name="Agent 2")

        await mock_repo.set_trust(user["id"], agent1["id"], 0.9)
        await mock_repo.set_trust(user["id"], agent2["id"], 0.7)
        await mock_repo.set_trust(agent1["id"], user["id"], 0.95)

        network = await graph_service.get_trust_network(user["id"])
        assert network.entity.id == user["id"]
        assert len(network.trusts) == 2
        assert len(network.trusted_by) == 1
        assert 0.85 < network.trust_score < 0.9  # Average

    @pytest.mark.asyncio()
    async def test_trust_bounds(self):
        from src.graph.models import TrustCreate
        from pydantic import ValidationError
        # Valid trust
        trust = TrustCreate(source_id="u1", target_id="u2", score=0.5)
        assert trust.score == 0.5
        # Invalid scores
        with pytest.raises(ValidationError):
            TrustCreate(source_id="u1", target_id="u2", score=1.5)
        with pytest.raises(ValidationError):
            TrustCreate(source_id="u1", target_id="u2", score=-1.5)


# ============================================================================
# Intent Tests
# ============================================================================

class TestIntentOperations:
    """Tests for intent operations."""

    @pytest.mark.asyncio()
    async def test_create_intent(self, graph_service, mock_repo):
        entity = await mock_repo.create_entity(entity_type="user", name="Intent User")
        intent = await graph_service.create_intent(
            entity_id=entity["id"],
            intent_type="purchase",
            description="Wants to buy premium plan",
            confidence=0.9,
            related_entities=["plan-premium"]
        )
        assert isinstance(intent, Intent)
        assert intent.intent_type == "purchase"
        assert intent.status == "active"
        assert "plan-premium" in intent.related_entities

    @pytest.mark.asyncio()
    async def test_get_active_intents(self, graph_service, mock_repo):
        user = await mock_repo.create_entity(entity_type="user", name="Intent User")
        await mock_repo.create_intent(user["id"], "explore", "Browse", status="active")
        await mock_repo.create_intent(user["id"], "purchase", "Buy", status="satisfied")
        await mock_repo.create_intent(user["id"], "delegate", "Delegate", status="active")

        active = await graph_service._repo.get_active_intents(entity_id=user["id"])
        assert len(active) == 2
        assert all(i["status"] == "active" for i in active)


# ============================================================================
# Prediction Tests
# ============================================================================

class TestPredictionOperations:
    """Tests for prediction operations."""

    @pytest.mark.asyncio()
    async def test_create_prediction(self, graph_service, mock_repo):
        entity = await mock_repo.create_entity(entity_type="user", name="Prediction User")
        prediction = await graph_service.record_prediction(
            entity_id=entity["id"],
            prediction_type="churn_risk",
            value={"risk_score": 0.3, "category": "low"},
            confidence=0.85,
            model_version="churn-v1.2",
            features={"login_frequency": "daily"}
        )
        assert isinstance(prediction, Prediction)
        assert prediction.prediction_type == "churn_risk"
        assert prediction.validated is False

    @pytest.mark.asyncio()
    async def test_validate_prediction(self, graph_service, mock_repo):
        entity = await mock_repo.create_entity(entity_type="user", name="Validate User")
        pred = await mock_repo.create_prediction(
            entity_id=entity["id"],
            prediction_type="churn_risk",
            value={"risk_score": 0.3},
            confidence=0.8,
            model_version="v1"
        )
        result = await graph_service.validate_prediction(pred["id"], {"risk_score": 0.35})
        assert result is True
        updated = mock_repo.predictions[-1]
        assert updated["validated"] is True
        assert updated["actual_outcome"]["risk_score"] == 0.35


# ============================================================================
# Action Tests
# ============================================================================

class TestActionOperations:
    """Tests for action operations."""

    @pytest.mark.asyncio()
    async def test_create_action(self, graph_service, mock_repo):
        entity = await mock_repo.create_entity(entity_type="user", name="Action User")
        action = await graph_service.create_action(
            entity_id=entity["id"],
            action_type="send_notification",
            description="Send welcome email",
            parameters={"template": "welcome"},
            priority=5
        )
        assert isinstance(action, Action)
        assert action.action_type == "send_notification"
        assert action.priority == 5
        assert action.status == "pending"

    @pytest.mark.asyncio()
    async def test_get_pending_actions(self, graph_service, mock_repo):
        user = await mock_repo.create_entity(entity_type="user", name="Action User")
        await mock_repo.create_action(user["id"], "notify", "Low priority", priority=1)
        await mock_repo.create_action(user["id"], "alert", "High priority", priority=8)
        await mock_repo.create_action(user["id"], "remind", "Medium priority", priority=5)

        recommendations = await graph_service.get_pending_actions(min_priority=3)
        assert len(recommendations) == 2  # high and medium
        assert recommendations[0].action.priority >= recommendations[1].action.priority

    @pytest.mark.asyncio()
    async def test_update_action_status(self, graph_service, mock_repo):
        entity = await mock_repo.create_entity(entity_type="user", name="Status User")
        action = await mock_repo.create_action(entity["id"], "test", "Test action")
        await graph_service._repo.update_action_status(action["id"], "executed")
        updated = mock_repo.actions[-1]
        assert updated["status"] == "executed"


# ============================================================================
# Graph Traversal Tests
# ============================================================================

class TestGraphTraversal:
    """Tests for graph traversal operations."""

    @pytest.mark.asyncio()
    async def test_get_entity_graph(self, graph_service, mock_repo):
        user = await mock_repo.create_entity(entity_type="user", name="Graph User")
        tool1 = await mock_repo.create_entity(entity_type="tool", name="Tool 1")
        tool2 = await mock_repo.create_entity(entity_type="tool", name="Tool 2")

        await mock_repo.create_edge(user["id"], tool1["id"], "uses", weight=0.9)
        await mock_repo.create_edge(user["id"], tool2["id"], "owns", weight=0.8)
        await mock_repo.create_edge(tool1["id"], user["id"], "depends_on", weight=0.7)

        result = await graph_service.get_entity_with_graph(user["id"], depth=2)
        assert result is not None
        assert result.entity.id == user["id"]
        assert len(result.edges) >= 2
        assert "total_degree" in result.metrics

    @pytest.mark.asyncio()
    async def test_get_neighborhood(self, graph_service, mock_repo):
        center = await mock_repo.create_entity(entity_type="concept", name="Center")
        neighbor1 = await mock_repo.create_entity(entity_type="concept", name="Neighbor 1")
        neighbor2 = await mock_repo.create_entity(entity_type="concept", name="Neighbor 2")

        await mock_repo.create_edge(center["id"], neighbor1["id"], "related_to")
        await mock_repo.create_edge(center["id"], neighbor2["id"], "similar_to")

        result = await graph_service.get_neighborhood(center["id"], max_depth=1)
        assert result.center_entity.id == center["id"]
        assert result.total_nodes == 3  # center + 2 neighbors

    @pytest.mark.asyncio()
    async def test_find_similar_entities(self, graph_service, mock_repo):
        user1 = await mock_repo.create_entity(entity_type="user", name="User 1")
        user2 = await mock_repo.create_entity(entity_type="user", name="User 2")
        user3 = await mock_repo.create_entity(entity_type="user", name="User 3")

        # User 1 shares behavior types with User 2
        await mock_repo.record_behavior(user1["id"], "login")
        await mock_repo.record_behavior(user1["id"], "purchase")
        await mock_repo.record_behavior(user2["id"], "login")
        await mock_repo.record_behavior(user2["id"], "purchase")
        await mock_repo.record_behavior(user3["id"], "view")  # Different behavior

        similar = await graph_service.find_similar_entities(user1["id"], min_similarity=0.3)
        similar_ids = [s.entity.id for s in similar]
        assert user2["id"] in similar_ids
        assert user3["id"] not in similar_ids


# ============================================================================
# GraphRAG Tests
# ============================================================================

class TestGraphRAGIntegration:
    """Tests for GraphRAG integration points."""

    @pytest.mark.asyncio()
    async def test_enrich_query_with_graph(self, graph_service, mock_repo):
        user = await mock_repo.create_entity(entity_type="user", name="RAG User")
        await mock_repo.record_behavior(user["id"], "login")
        await mock_repo.create_intent(user["id"], "explore", "Browse products")

        result = await graph_service.enrich_query_with_graph(
            query="What are user preferences?",
            entity_id=user["id"],
            max_entities=5
        )
        assert result.query == "What are user preferences?"
        assert len(result.relevant_entities) >= 1
        assert result.relevant_entities[0].id == user["id"]
        assert len(result.relevant_behaviors) >= 1
        assert len(result.related_intents) >= 1
        assert result.context_string != ""

    @pytest.mark.asyncio()
    async def test_get_llm_context(self, graph_service, mock_repo):
        user = await mock_repo.create_entity(entity_type="user", name="Context User")
        await mock_repo.record_behavior(user["id"], "purchase", outcome={"item": "book"})
        await mock_repo.create_intent(user["id"], "learn", "Learn new skills")

        context = await graph_service.get_context_for_llm(
            query="Recommend content",
            entity_ids=[user["id"]],
            max_items=10
        )
        assert "query" in context
        assert "entities" in context
        assert "behaviors" in context
        assert "intents" in context
        assert "summary" in context
        assert len(context["behaviors"]) >= 1
        assert "Behaviors:" in context["summary"]

    @pytest.mark.asyncio()
    async def test_get_entity_rag_context_empty(self, graph_service, mock_repo):
        entity = await mock_repo.create_entity(entity_type="user", name="Empty Context")
        result = await graph_service.get_context_for_llm(query="", entity_ids=[entity["id"]])
        # When no behaviors/trust/intents, summary only shows entities
        assert result["summary"] == "Entities: 1"


# ============================================================================
# Metrics Tests
# ============================================================================

class TestMetrics:
    """Tests for entity metrics calculation."""

    @pytest.mark.asyncio()
    async def test_calculate_entity_metrics(self, graph_service, mock_repo):
        user = await mock_repo.create_entity(entity_type="user", name="Metrics User")
        # Create trust relationships
        await mock_repo.set_trust(user["id"], "other-1", 0.8)
        await mock_repo.set_trust("other-2", user["id"], 0.9)
        # Also create corresponding edges for centrality (trust edges)
        await mock_repo.create_edge(user["id"], "other-1", "trusts", weight=0.8)
        await mock_repo.create_edge("other-2", user["id"], "trusts", weight=0.9)
        for i in range(5):
            await mock_repo.record_behavior(user["id"], "action")

        metrics = await graph_service.calculate_entity_metrics(user["id"])

        assert "centrality" in metrics
        assert metrics["centrality"]["out_degree"] == 1
        assert metrics["centrality"]["in_degree"] == 1
        assert "trust_score" in metrics
        assert "activity_score" in metrics
        assert "engagement_score" in metrics
        assert metrics["total_behaviors"] == 5
        assert "days_active" in metrics


# ============================================================================
# Model Validation Tests
# ============================================================================

class TestModelValidation:
    """Tests for Pydantic model validation."""

    def test_entity_create(self):
        entity = EntityCreate(type="user", name="Test", properties={"key": "value"})
        assert entity.type == "user"
        assert entity.name == "Test"

    def test_behavior_create(self):
        behavior = BehaviorCreate(entity_id="e1", action_type="click", confidence=0.9)
        assert behavior.entity_id == "e1"
        assert behavior.action_type == "click"

    def test_trust_validation_bounds(self):
        from pydantic import ValidationError
        # Valid
        TrustCreate(source_id="u1", target_id="u2", score=0.5)
        # Invalid scores
        with pytest.raises(ValidationError):
            TrustCreate(source_id="u1", target_id="u2", score=1.5)
        with pytest.raises(ValidationError):
            TrustCreate(source_id="u1", target_id="u2", score=-1.5)

    def test_action_priority_validation(self):
        from pydantic import ValidationError
        ActionCreate(entity_id="e1", action_type="test", description="Test", priority=5)
        with pytest.raises(ValidationError):
            ActionCreate(entity_id="e1", action_type="test", description="Test", priority=11)
        with pytest.raises(ValidationError):
            ActionCreate(entity_id="e1", action_type="test", description="Test", priority=0)


# ============================================================================
# Graph Statistics Tests
# ============================================================================

class TestGraphStatistics:
    """Tests for graph statistics."""

    @pytest.mark.asyncio()
    async def test_get_graph_stats(self, graph_service, mock_repo):
        await mock_repo.create_entity(entity_type="user", name="User 1")
        await mock_repo.create_entity(entity_type="agent", name="Agent 1")
        await mock_repo.create_edge("entity-1", "entity-2", "trusts")
        await mock_repo.record_behavior("entity-1", "login")

        stats = await graph_service.get_graph_statistics()
        assert stats["entities"] == 2
        assert stats["edges"] == 1
        assert stats["behaviors"] == 1


__all__ = [
    "TestEntityOperations",
    "TestBehaviorOperations",
    "TestTrustOperations",
    "TestIntentOperations",
    "TestPredictionOperations",
    "TestActionOperations",
    "TestGraphTraversal",
    "TestGraphRAGIntegration",
    "TestMetrics",
    "TestGraphStatistics",
    "TestModelValidation",
]
