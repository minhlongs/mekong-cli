"""BMAD Workflow Persistent Catalog."""

from pathlib import Path
import json
from .loader import BMADWorkflowLoader


class WorkflowCatalog:
    """Persistent catalog of BMAD workflows with caching."""

    def __init__(self, cache_path: str = ".mekong/bmad_catalog.json"):
        """Initialize catalog.

        Args:
            cache_path: Path to cache file
        """
        self.cache_path = Path(cache_path)
        self.loader = BMADWorkflowLoader()

    def build_catalog(self) -> dict:
        """Build and cache workflow catalog.

        Returns:
            Catalog data dictionary
        """
        catalog_data = {
            "total_count": self.loader.catalog.total_count,
            "agent_types": self.loader.catalog.agent_types,
            "workflows": [
                {
                    "id": w.id,
                    "name": w.name,
                    "description": w.description,
                    "agent_type": w.agent_type,
                    "file_path": str(w.file_path)
                }
                for w in self.loader.catalog.workflows
            ]
        }

        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.cache_path.write_text(json.dumps(catalog_data, indent=2))

        return catalog_data

    def load_catalog(self) -> dict:
        """Load cached catalog.

        Returns:
            Catalog data dictionary
        """
        if self.cache_path.exists():
            return json.loads(self.cache_path.read_text())
        return self.build_catalog()
