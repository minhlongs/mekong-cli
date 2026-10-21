# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Mekong CLI - Vector Memory Store (AGI v2)."""

import hashlib
import json
import math
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class MemoryType(str, Enum):
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"


@dataclass
class VectorEntry:
    id: str
    vector: List[float]
    payload: Dict[str, Any]
    memory_type: MemoryType = MemoryType.EPISODIC
    created_at: float = field(default_factory=time.time)


@dataclass
class VectorCollection:
    name: str
    dimension: int
    entries: Dict[str, VectorEntry] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class VectorMemoryStore:
    """Persistent vector store with cosine similarity search."""

    def __init__(self, persist_path: Optional[str] = None) -> None:
        self._collections: Dict[str, VectorCollection] = {}
        self._persist_path: Optional[Path] = Path(persist_path) if persist_path else None
        if self._persist_path:
            self._load_snapshot()

    def create_collection(self, name: str, dimension: int) -> VectorCollection:
        if name in self._collections:
            raise ValueError(f"Collection '{name}' already exists.")
        col = VectorCollection(name=name, dimension=dimension)
        self._collections[name] = col
        self._auto_persist()
        return col

    def get_or_create_collection(self, name: str, dimension: int) -> VectorCollection:
        return self._collections[name] if name in self._collections else self.create_collection(name, dimension)

    def delete_collection(self, name: str) -> None:
        if name not in self._collections:
            raise KeyError(f"Collection '{name}' not found.")
        del self._collections[name]
        self._auto_persist()

    def upsert(self, collection: str, id: str, vector: List[float], payload: Optional[Dict[str, Any]] = None, memory_type: MemoryType = MemoryType.EPISODIC) -> VectorEntry:
        col = self._get_collection(collection)
        if len(vector) != col.dimension:
            raise ValueError(f"Vector dimension {len(vector)} != collection dimension {col.dimension}.")
        entry = VectorEntry(id=id, vector=vector, payload=payload or {}, memory_type=memory_type)
        col.entries[id] = entry
        self._auto_persist()
        return entry

    def search(self, collection: str, query_vector: List[float], top_k: int = 5, memory_type: Optional[MemoryType] = None) -> List[Tuple[VectorEntry, float]]:
        col = self._get_collection(collection)
        if len(query_vector) != col.dimension:
            raise ValueError(f"Query dimension {len(query_vector)} != collection dimension {col.dimension}.")
        entries = [e for e in col.entries.values() if memory_type is None or e.memory_type == memory_type]
        scored = sorted([(e, self._cosine_similarity(query_vector, e.vector)) for e in entries], key=lambda x: x[1], reverse=True)
        return scored[:top_k]

    def search_by_payload(self, collection: str, filters: Dict[str, Any], limit: int = 10) -> List[VectorEntry]:
        col = self._get_collection(collection)
        return [e for e in col.entries.values() if all(e.payload.get(k) == v for k, v in filters.items())][:limit]

    def delete_point(self, collection: str, id: str) -> None:
        col = self._get_collection(collection)
        if id not in col.entries:
            raise KeyError(f"Entry '{id}' not found in collection '{collection}'.")
        del col.entries[id]
        self._auto_persist()

    def count(self, collection: str) -> int:
        return len(self._get_collection(collection).entries)

    def get_collection_info(self, name: str) -> Dict[str, Any]:
        col = self._get_collection(name)
        type_counts: Dict[str, int] = {}
        for e in col.entries.values():
            type_counts[e.memory_type.value] = type_counts.get(e.memory_type.value, 0) + 1
        return {"name": col.name, "dimension": col.dimension, "count": len(col.entries), "memory_types": type_counts, "metadata": col.metadata}

    def list_collections(self) -> List[str]:
        return list(self._collections.keys())

    def save_snapshot(self, path: Optional[str] = None) -> str:
        save_path = Path(path) if path else (self._persist_path or Path(".mekong/vector_store.json"))
        save_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            name: {
                "dimension": col.dimension, "metadata": col.metadata,
                "entries": [{"id": e.id, "vector": e.vector, "payload": e.payload, "memory_type": e.memory_type.value, "created_at": e.created_at} for e in col.entries.values()],
            }
            for name, col in self._collections.items()
        }
        save_path.write_text(json.dumps(data, indent=2))
        return str(save_path)

    def _load_snapshot(self) -> None:
        if not self._persist_path or not self._persist_path.exists():
            return
        try:
            for col_name, col_data in json.loads(self._persist_path.read_text()).items():
                col = VectorCollection(name=col_name, dimension=col_data["dimension"], metadata=col_data.get("metadata", {}))
                for ed in col_data.get("entries", []):
                    try:
                        mem_type = MemoryType(ed.get("memory_type", "episodic"))
                    except ValueError:
                        mem_type = MemoryType.EPISODIC
                    col.entries[ed["id"]] = VectorEntry(ed["id"], ed["vector"], ed.get("payload", {}), mem_type, ed.get("created_at", time.time()))
                self._collections[col_name] = col
        except (json.JSONDecodeError, KeyError):
            self._collections = {}

    def _auto_persist(self) -> None:
        if self._persist_path:
            self.save_snapshot(str(self._persist_path))

    @staticmethod
    def text_to_hash_vector(text: str, dimension: int = 64) -> List[float]:
        tl = text.lower().strip().encode()
        ext = hashlib.sha256(tl).digest()
        while len(ext) < dimension * 4:
            ext += hashlib.sha256(ext + tl).digest()
        vec = [(ext[i] / 127.5) - 1.0 for i in range(dimension)]
        mag = math.sqrt(sum(x * x for x in vec))
        return [x / mag for x in vec] if mag > 0 else vec

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        mag = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(x * x for x in b))
        return sum(x * y for x, y in zip(a, b)) / mag if mag > 0.0 else 0.0

    def _get_collection(self, name: str) -> VectorCollection:
        if name not in self._collections:
            raise KeyError(f"Collection '{name}' not found.")
        return self._collections[name]


__all__ = ["MemoryType", "VectorEntry", "VectorCollection", "VectorMemoryStore"]
