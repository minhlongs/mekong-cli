# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Autonomous Memory Federation & Semantic Associative Recall Engine.

Provides multi-domain federated memory (episodic execution logs, architectural
decisions, codebase knowledge graph symbols, and self-repair patterns) with
pure standard-library hybrid BM25 / vector cosine search and SQLite persistence.

STRICT INVARIANT: Provider-neutral and standard-library-only. Zero external vendor
SDKs, heavy ML frameworks, or vector DB dependencies (complies with tests/test_core_boundary.py).
"""

from __future__ import annotations

import ast
import hashlib
import json
import logging
import math
import os
import re
import sqlite3
import threading
import time
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)

# Default database location in .mekong/memory_federation.db
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_DB = _PROJECT_ROOT / ".mekong" / "memory_federation.db"

_STOP_WORDS: Set[str] = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being",
    "below", "between", "both", "but", "by", "can", "can't", "cannot", "could",
    "couldn't", "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down",
    "during", "each", "few", "for", "from", "further", "had", "hadn't", "has",
    "hasn't", "have", "haven't", "having", "he", "he'd", "he'll", "he's", "her",
    "here", "here's", "hers", "herself", "him", "himself", "his", "how", "how's",
    "i", "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it",
    "it's", "its", "itself", "let's", "me", "more", "most", "mustn't", "my",
    "myself", "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other",
    "ought", "our", "ours", "ourselves", "out", "over", "own", "same", "shan't",
    "she", "she'd", "she'll", "she's", "should", "shouldn't", "so", "some", "such",
    "than", "that", "that's", "the", "their", "theirs", "them", "themselves",
    "then", "there", "there's", "these", "they", "they'd", "they'll", "they're",
    "they've", "this", "those", "through", "to", "too", "under", "until", "up",
    "very", "was", "wasn't", "we", "we'd", "we'll", "we're", "we've", "were",
    "weren't", "what", "what's", "when", "when's", "where", "where's", "which",
    "while", "who", "who's", "whom", "why", "why's", "with", "won't", "would",
    "wouldn't", "you", "you'd", "you'll", "you're", "you've", "your", "yours",
    "yourself", "yourselves",
}

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS federated_memory_items (
    item_id         TEXT    NOT NULL PRIMARY KEY,
    domain          TEXT    NOT NULL,
    title           TEXT    NOT NULL,
    content         TEXT    NOT NULL,
    tags            TEXT    NOT NULL DEFAULT '[]',
    metadata_json   TEXT    NOT NULL DEFAULT '{}',
    tokens_json     TEXT    NOT NULL DEFAULT '[]',
    created_at      REAL    NOT NULL
);

CREATE TABLE IF NOT EXISTS knowledge_nodes (
    node_id         TEXT    NOT NULL PRIMARY KEY,
    name            TEXT    NOT NULL,
    node_type       TEXT    NOT NULL,
    metadata_json   TEXT    NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS knowledge_edges (
    edge_id         TEXT    NOT NULL PRIMARY KEY,
    source_id       TEXT    NOT NULL,
    target_id       TEXT    NOT NULL,
    relation        TEXT    NOT NULL,
    weight          REAL    NOT NULL DEFAULT 1.0
);

CREATE INDEX IF NOT EXISTS idx_mem_domain ON federated_memory_items (domain);
CREATE INDEX IF NOT EXISTS idx_mem_created_at ON federated_memory_items (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_nodes_type ON knowledge_nodes (node_type);
CREATE INDEX IF NOT EXISTS idx_edges_source ON knowledge_edges (source_id);
CREATE INDEX IF NOT EXISTS idx_edges_target ON knowledge_edges (target_id);
"""


def _tokenize(text: str) -> List[str]:
    """Extract clean lowercase alphabetic and alphanumeric search tokens."""
    tokens = re.findall(r"[a-zA-Z0-9_\-\.]{2,}", text.lower())
    return [t for t in tokens if t not in _STOP_WORDS]


def _compute_tf(tokens: List[str]) -> Dict[str, float]:
    """Compute term frequency vector normalized by token count."""
    counts = Counter(tokens)
    total = float(len(tokens))
    if total == 0.0:
        return {}
    return {k: v / total for k, v in counts.items()}


def _cosine_similarity(vec1: Dict[str, float], vec2: Dict[str, float]) -> float:
    """Compute cosine similarity between two term frequency dictionaries."""
    intersection = set(vec1.keys()) & set(vec2.keys())
    if not intersection:
        return 0.0
    dot_product = sum(vec1[k] * vec2[k] for k in intersection)
    mag1 = math.sqrt(sum(v * v for v in vec1.values()))
    mag2 = math.sqrt(sum(v * v for v in vec2.values()))
    if mag1 == 0.0 or mag2 == 0.0:
        return 0.0
    return dot_product / (mag1 * mag2)


@dataclass
class FederatedMemoryItem:
    """An atomic memory unit across episodic, decision, entity, or pattern domains."""

    item_id: str
    domain: str  # "episodic", "decisions", "entities", "patterns"
    title: str
    content: str
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    relevance_score: float = 0.0
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        """Convert item to dictionary."""
        return {
            "item_id": self.item_id,
            "domain": self.domain,
            "title": self.title,
            "content": self.content,
            "tags": self.tags,
            "metadata": self.metadata,
            "relevance_score": round(self.relevance_score, 4),
            "created_at": self.created_at,
        }


@dataclass
class GraphNode:
    """A node in the codebase and architectural knowledge graph."""

    node_id: str
    name: str
    node_type: str  # "file", "class", "function", "agent", "decision"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert node to dictionary."""
        return asdict(self)


@dataclass
class GraphEdge:
    """A directional relationship between two nodes in the knowledge graph."""

    edge_id: str
    source_id: str
    target_id: str
    relation: str  # "defines", "imports", "calls", "modifies", "voted_on"
    weight: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        """Convert edge to dictionary."""
        return asdict(self)


@dataclass
class MemoryMeshStats:
    """Summary metrics of the federated memory subsystem."""

    total_items: int = 0
    items_by_domain: Dict[str, int] = field(default_factory=dict)
    total_nodes: int = 0
    total_edges: int = 0
    db_path: str = ""
    last_indexed: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        """Convert stats to dictionary."""
        return {
            "total_items": self.total_items,
            "items_by_domain": self.items_by_domain,
            "total_nodes": self.total_nodes,
            "total_edges": self.total_edges,
            "db_path": self.db_path,
            "last_indexed": self.last_indexed,
        }


class MemoryFederationEngine:
    """Coordinates multi-domain indexing, hybrid semantic recall, and graph queries."""

    def __init__(self, db_path: Optional[Path] = None) -> None:
        raw_env = os.environ.get("MEKONG_MEMORY_FEDERATION_DB")
        if db_path:
            self.db_path = Path(db_path).resolve()
        elif raw_env:
            self.db_path = Path(raw_env).resolve()
        else:
            self.db_path = _DEFAULT_DB.resolve()

        self._lock = threading.Lock()
        self._ensure_db()

    def _ensure_db(self) -> None:
        """Create database parent directories and initialize schema."""
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            with sqlite3.connect(str(self.db_path), timeout=10.0) as conn:
                conn.execute("PRAGMA journal_mode=WAL;")
                conn.executescript(_SCHEMA_SQL)
                conn.commit()
        except Exception as exc:
            logger.warning(f"Error initializing memory federation database: {exc}")

    def _broadcast_gateway_event(self, event_type: str, data: dict[str, Any]) -> None:
        """Stream memory lifecycle events over Gateway broker if available."""
        try:
            from src.core.gateway.streaming import StreamEvent, get_streaming_broker
            broker = get_streaming_broker()
            broker.publish(StreamEvent(
                mission_id="memory_federation",
                event_type=event_type,
                data=data,
            ))
        except Exception:
            pass

    def store_item(
        self,
        domain: str,
        title: str,
        content: str,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        item_id: Optional[str] = None,
    ) -> FederatedMemoryItem:
        """Insert or update a memory item in the federated store."""
        domain_norm = domain.lower().strip()
        if domain_norm not in ("episodic", "decisions", "entities", "patterns"):
            domain_norm = "episodic"

        now = time.time()
        uid = item_id or f"mem_{domain_norm}_{int(now * 1000)}_{os.urandom(3).hex()}"
        item_tags = tags or []
        meta = metadata or {}
        tokens = _tokenize(f"{title} {content} {' '.join(item_tags)}")

        item = FederatedMemoryItem(
            item_id=uid,
            domain=domain_norm,
            title=title,
            content=content,
            tags=item_tags,
            metadata=meta,
            created_at=now,
        )

        with self._lock:
            try:
                with sqlite3.connect(str(self.db_path), timeout=10.0) as conn:
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO federated_memory_items
                        (item_id, domain, title, content, tags, metadata_json, tokens_json, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            uid,
                            domain_norm,
                            title,
                            content,
                            json.dumps(item_tags),
                            json.dumps(meta),
                            json.dumps(tokens),
                            now,
                        ),
                    )
                    conn.commit()
            except Exception as exc:
                logger.warning(f"Error persisting memory item {uid}: {exc}")

        self._broadcast_gateway_event("memory_indexed", {
            "item_id": uid,
            "domain": domain_norm,
            "title": title,
        })

        return item

    def store_graph_node(self, name: str, node_type: str, metadata: Optional[Dict[str, Any]] = None, node_id: Optional[str] = None) -> GraphNode:
        """Register a node in the relational knowledge graph."""
        uid = node_id or f"{node_type}:{name}"
        meta = metadata or {}
        node = GraphNode(node_id=uid, name=name, node_type=node_type, metadata=meta)

        with self._lock:
            try:
                with sqlite3.connect(str(self.db_path), timeout=10.0) as conn:
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO knowledge_nodes (node_id, name, node_type, metadata_json)
                        VALUES (?, ?, ?, ?)
                        """,
                        (uid, name, node_type, json.dumps(meta)),
                    )
                    conn.commit()
            except Exception as exc:
                logger.warning(f"Error storing knowledge node {uid}: {exc}")
        return node

    def store_graph_edge(self, source_id: str, target_id: str, relation: str, weight: float = 1.0) -> GraphEdge:
        """Register a directional relationship edge in the knowledge graph."""
        edge_id = f"{source_id}->{relation}->{target_id}"
        edge = GraphEdge(edge_id=edge_id, source_id=source_id, target_id=target_id, relation=relation, weight=weight)

        with self._lock:
            try:
                with sqlite3.connect(str(self.db_path), timeout=10.0) as conn:
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO knowledge_edges (edge_id, source_id, target_id, relation, weight)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (edge_id, source_id, target_id, relation, weight),
                    )
                    conn.commit()
            except Exception as exc:
                logger.warning(f"Error storing knowledge edge {edge_id}: {exc}")
        return edge

    def query(
        self,
        query_text: str,
        domain: str = "all",
        limit: int = 5,
        min_score: float = 0.01,
    ) -> List[FederatedMemoryItem]:
        """Hybrid search combining BM25 term weighting and vector cosine similarity."""
        query_tokens = _tokenize(query_text)
        if not query_tokens:
            return []

        query_tf = _compute_tf(query_tokens)
        query_terms = set(query_tokens)

        domain_filter = domain.lower().strip()
        sql = "SELECT item_id, domain, title, content, tags, metadata_json, tokens_json, created_at FROM federated_memory_items"
        params: List[Any] = []
        if domain_filter != "all":
            sql += " WHERE domain = ?"
            params.append(domain_filter)

        candidates: List[Tuple[FederatedMemoryItem, List[str]]] = []
        try:
            with sqlite3.connect(str(self.db_path), timeout=10.0) as conn:
                cursor = conn.execute(sql, params)
                for row in cursor.fetchall():
                    item_id, dom, title, content, tags_raw, meta_raw, tokens_raw, created_at = row
                    tokens = json.loads(tokens_raw) if tokens_raw else []
                    item = FederatedMemoryItem(
                        item_id=item_id,
                        domain=dom,
                        title=title,
                        content=content,
                        tags=json.loads(tags_raw) if tags_raw else [],
                        metadata=json.loads(meta_raw) if meta_raw else {},
                        created_at=created_at,
                    )
                    candidates.append((item, tokens))
        except Exception as exc:
            logger.warning(f"Error loading candidates during memory recall: {exc}")
            return []

        if not candidates:
            return []

        # 1. Compute Document Frequencies for BM25 IDF
        total_docs = len(candidates)
        doc_freqs: Counter[str] = Counter()
        for _, tokens in candidates:
            doc_freqs.update(set(tokens))

        avg_doc_len = sum(len(t) for _, t in candidates) / float(total_docs) if total_docs > 0 else 1.0
        k1 = 1.5
        b = 0.75

        scored_items: List[FederatedMemoryItem] = []
        for item, doc_tokens in candidates:
            doc_len = len(doc_tokens)
            doc_term_counts = Counter(doc_tokens)
            doc_tf = _compute_tf(doc_tokens)

            # BM25 score calculation
            bm25_score = 0.0
            for term in query_terms:
                if term in doc_term_counts:
                    freq = doc_term_counts[term]
                    df = doc_freqs.get(term, 0)
                    idf = math.log(1.0 + (total_docs - df + 0.5) / (df + 0.5))
                    num = freq * (k1 + 1.0)
                    den = freq + k1 * (1.0 - b + b * (doc_len / avg_doc_len))
                    bm25_score += idf * (num / den)

            # Vector cosine similarity
            cosine_score = _cosine_similarity(query_tf, doc_tf)

            # Combined hybrid score (70% BM25 normalized + 30% cosine)
            norm_bm25 = min(1.0, bm25_score / 5.0)
            hybrid_score = (0.7 * norm_bm25) + (0.3 * cosine_score)

            if hybrid_score >= min_score or (set(query_tokens) & set(doc_tokens)):
                item.relevance_score = max(hybrid_score, 0.05 if (set(query_tokens) & set(doc_tokens)) else 0.0)
                scored_items.append(item)

        scored_items.sort(key=lambda x: x.relevance_score, reverse=True)
        top_results = scored_items[:max(1, limit)]

        if top_results:
            self._broadcast_gateway_event("memory_associative_hit", {
                "query": query_text,
                "domain": domain,
                "hits_count": len(top_results),
                "top_hit": top_results[0].title,
            })

        return top_results

    def query_knowledge_graph(self, entity: str, depth: int = 2) -> Dict[str, Any]:
        """Traverse connected entities in the knowledge graph up to specified depth."""
        entity_norm = entity.lower().strip()
        nodes_found: Dict[str, Dict[str, Any]] = {}
        edges_found: List[Dict[str, Any]] = []

        visited_nodes: Set[str] = set()
        frontier: Set[str] = set()

        try:
            with sqlite3.connect(str(self.db_path), timeout=10.0) as conn:
                # Find matching seed nodes
                cursor = conn.execute(
                    "SELECT node_id, name, node_type, metadata_json FROM knowledge_nodes WHERE LOWER(name) LIKE ? OR node_id LIKE ?",
                    (f"%{entity_norm}%", f"%{entity_norm}%"),
                )
                for nid, name, ntype, meta_raw in cursor.fetchall():
                    frontier.add(nid)
                    nodes_found[nid] = {
                        "node_id": nid,
                        "name": name,
                        "node_type": ntype,
                        "metadata": json.loads(meta_raw) if meta_raw else {},
                    }

                # Breadth-first traversal up to depth
                current_depth = 0
                max_depth = max(1, min(depth, 4))
                while frontier and current_depth < max_depth:
                    current_depth += 1
                    next_frontier: Set[str] = set()

                    for nid in list(frontier):
                        visited_nodes.add(nid)
                        # Query outgoing and incoming edges
                        edge_cur = conn.execute(
                            """
                            SELECT edge_id, source_id, target_id, relation, weight
                            FROM knowledge_edges
                            WHERE source_id = ? OR target_id = ?
                            """,
                            (nid, nid),
                        )
                        for eid, src, tgt, rel, w in edge_cur.fetchall():
                            if not any(e["edge_id"] == eid for e in edges_found):
                                edges_found.append({
                                    "edge_id": eid,
                                    "source_id": src,
                                    "target_id": tgt,
                                    "relation": rel,
                                    "weight": w,
                                })
                            neighbor = tgt if src == nid else src
                            if neighbor not in visited_nodes:
                                next_frontier.add(neighbor)

                    # Fetch node definitions for discovered neighbors
                    if next_frontier:
                        placeholders = ",".join("?" for _ in next_frontier)
                        node_cur = conn.execute(
                            f"SELECT node_id, name, node_type, metadata_json FROM knowledge_nodes WHERE node_id IN ({placeholders})",
                            list(next_frontier),
                        )
                        for nid, name, ntype, meta_raw in node_cur.fetchall():
                            nodes_found[nid] = {
                                "node_id": nid,
                                "name": name,
                                "node_type": ntype,
                                "metadata": json.loads(meta_raw) if meta_raw else {},
                            }

                    frontier = next_frontier
        except Exception as exc:
            logger.warning(f"Error querying knowledge graph for '{entity}': {exc}")

        return {
            "entity": entity,
            "depth": depth,
            "total_nodes": len(nodes_found),
            "total_edges": len(edges_found),
            "nodes": list(nodes_found.values()),
            "edges": edges_found,
        }

    def get_stats(self) -> MemoryMeshStats:
        """Compute aggregated statistics of the federated memory subsystem."""
        stats = MemoryMeshStats(db_path=str(self.db_path))
        try:
            with sqlite3.connect(str(self.db_path), timeout=10.0) as conn:
                # Items by domain
                cur = conn.execute("SELECT domain, COUNT(*) FROM federated_memory_items GROUP BY domain")
                domain_counts: Dict[str, int] = {}
                total_items = 0
                for dom, count in cur.fetchall():
                    domain_counts[dom] = count
                    total_items += count
                stats.total_items = total_items
                stats.items_by_domain = domain_counts

                # Total nodes
                n_cur = conn.execute("SELECT COUNT(*) FROM knowledge_nodes")
                stats.total_nodes = n_cur.fetchone()[0]

                # Total edges
                e_cur = conn.execute("SELECT COUNT(*) FROM knowledge_edges")
                stats.total_edges = e_cur.fetchone()[0]
        except Exception as exc:
            logger.warning(f"Error reading memory stats: {exc}")
        return stats

    def index_all(self, project_root: Optional[Path] = None) -> MemoryMeshStats:
        """Scan project codebase, historical ballots, and evals to populate federated memory."""
        root = Path(project_root or _PROJECT_ROOT).resolve()

        # 1. Index Seed Core Patterns
        seed_patterns = [
            ("AST Syntax Auto-Repair", "Automatically detects missing colons on block statements and unbalanced delimiters.", ["ast", "self_repair", "syntax"]),
            ("Atomic Checkpoint Rollback", "Restores damaged or unparseable source files from SQLite snapshot storage upon severe corruption.", ["checkpoint", "rollback", "resilience"]),
            ("Sliding-Window Rate Limiting", "Enforces token-bucket quotas (free, pro, enterprise) with standard RFC headers and Retry-After backoff.", ["rate_limit", "gateway", "quota"]),
            ("Quorum Consensus Resolution", "Coordinates multi-agent voting (majority, supermajority, unanimous, weighted) with SHA-256 ballots.", ["consensus", "voting", "debate"]),
            ("Multi-Stage Docker Synthesis", "Generates minimal Python 3.11 slim runtime container with Gateway healthchecks.", ["docker", "container", "packaging"]),
        ]
        for title, content, tags in seed_patterns:
            self.store_item(domain="patterns", title=title, content=content, tags=tags)

        # 2. Index Architectural Decisions from .mekong/consensus.db if present
        consensus_db = root / ".mekong" / "consensus.db"
        if consensus_db.exists():
            try:
                with sqlite3.connect(str(consensus_db), timeout=5.0) as conn:
                    cur = conn.execute("SELECT proposal, quorum_type, passed, payload_json FROM consensus_ballots LIMIT 50")
                    for prop, q_type, passed, payload_raw in cur.fetchall():
                        status = "PASSED" if passed else "REJECTED"
                        self.store_item(
                            domain="decisions",
                            title=f"Consensus Decision: {prop[:50]}",
                            content=f"Proposal '{prop}' under {q_type} quorum evaluated to {status}.",
                            tags=["consensus", "ballot", q_type, status.lower()],
                        )
            except Exception as exc:
                logger.debug(f"Could not index consensus ballots: {exc}")

        # 3. Index Codebase Entities via AST
        src_dir = root / "src"
        if src_dir.exists():
            for py_file in src_dir.rglob("*.py"):
                rel = py_file.relative_to(root)
                f_node = self.store_graph_node(name=str(rel), node_type="file")
                try:
                    tree = ast.parse(py_file.read_text(encoding="utf-8", errors="ignore"), filename=str(rel))
                    for node in tree.body:
                        if isinstance(node, ast.ClassDef):
                            c_node = self.store_graph_node(name=node.name, node_type="class", metadata={"file": str(rel)})
                            self.store_graph_edge(source_id=f_node.node_id, target_id=c_node.node_id, relation="defines")
                            self.store_item(
                                domain="entities",
                                title=f"Class {node.name}",
                                content=f"Class {node.name} defined in {rel}. Docstring: {ast.get_docstring(node) or 'None'}",
                                tags=["class", node.name.lower(), str(rel)],
                            )
                        elif isinstance(node, ast.FunctionDef):
                            fn_node = self.store_graph_node(name=node.name, node_type="function", metadata={"file": str(rel)})
                            self.store_graph_edge(source_id=f_node.node_id, target_id=fn_node.node_id, relation="defines")
                except Exception:
                    pass

        return self.get_stats()


# Global singleton instance
_GLOBAL_MEMORY_ENGINE: Optional[MemoryFederationEngine] = None
_GLOBAL_MEMORY_LOCK = threading.Lock()


def get_memory_federation_engine() -> MemoryFederationEngine:
    """Get or initialize singleton MemoryFederationEngine."""
    global _GLOBAL_MEMORY_ENGINE
    with _GLOBAL_MEMORY_LOCK:
        if _GLOBAL_MEMORY_ENGINE is None:
            _GLOBAL_MEMORY_ENGINE = MemoryFederationEngine()
        return _GLOBAL_MEMORY_ENGINE
