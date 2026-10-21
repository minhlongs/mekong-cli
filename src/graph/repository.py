# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Graph Repository Layer - PostgreSQL JSONB operations for behavior graph."""

from typing import Optional

from src.db.database import DatabaseConnection, get_database
from src.graph.repository_analytics import GraphAnalyticsRepoMixin
from src.graph.repository_behaviors import GraphBehaviorTrustRepoMixin
from src.graph.repository_entities import GraphEntityEdgeRepoMixin


class GraphRepository(
    GraphEntityEdgeRepoMixin,
    GraphBehaviorTrustRepoMixin,
    GraphAnalyticsRepoMixin,
):
    """Repository for behavior graph data operations with PostgreSQL JSONB."""

    def __init__(self, db: Optional[DatabaseConnection] = None) -> None:
        self._db = db or get_database()


_repository: Optional[GraphRepository] = None


def get_graph_repository() -> GraphRepository:
    """Get global graph repository instance."""
    global _repository
    if _repository is None:
        _repository = GraphRepository()
    return _repository


async def init_graph_repository() -> GraphRepository:
    """Initialize repository with database connection."""
    from src.db.database import init_database

    await init_database()
    return get_graph_repository()


__all__ = [
    "GraphRepository",
    "get_graph_repository",
    "init_graph_repository",
]
