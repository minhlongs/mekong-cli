"""BMAD Workflow Loader."""

from pathlib import Path
from typing import List, Optional
import yaml
from .models import BMADWorkflow, WorkflowCatalog


class BMADWorkflowLoader:
    """Loads and manages BMAD workflows."""

    def __init__(self, bmad_path: str = "_bmad"):
        """Initialize loader.

        Args:
            bmad_path: Path to BMAD directory
        """
        self.bmad_path = Path(bmad_path)
        self.catalog: WorkflowCatalog
        self._load_catalog()

    def _load_catalog(self) -> None:
        """Scan BMAD directory and build workflow catalog."""
        workflows: List[BMADWorkflow] = []

        # Scan all workflow files
        if not self.bmad_path.exists():
            self.catalog = WorkflowCatalog(
                workflows=[],
                total_count=0,
                agent_types=[]
            )
            return

        for workflow_file in self.bmad_path.rglob("*.md"):
            workflow = self._parse_workflow(workflow_file)
            if workflow:
                workflows.append(workflow)

        agent_types = list(set(w.agent_type for w in workflows))
        self.catalog = WorkflowCatalog(
            workflows=workflows,
            total_count=len(workflows),
            agent_types=agent_types
        )

    def _parse_workflow(self, file_path: Path) -> Optional[BMADWorkflow]:
        """Parse workflow markdown file and extract metadata.

        Args:
            file_path: Path to workflow file

        Returns:
            BMADWorkflow instance or None if parsing fails
        """
        try:
            content = file_path.read_text()

            # Extract YAML frontmatter if present
            metadata = {}
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    try:
                        metadata = yaml.safe_load(parts[1]) or {}
                    except yaml.YAMLError:
                        metadata = {}

            # Determine agent type from path
            parts = file_path.parts
            agent_type = "general"
            if "agents" in parts:
                idx = parts.index("agents")
                if idx + 1 < len(parts):
                    agent_type = parts[idx + 1]

            workflow_id = file_path.stem

            return BMADWorkflow(
                id=workflow_id,
                name=metadata.get("name", workflow_id.replace("-", " ").title()),
                description=metadata.get("description", ""),
                agent_type=agent_type,
                file_path=file_path,
                parameters=metadata.get("parameters", {}),
                prerequisites=metadata.get("prerequisites", []),
                outputs=metadata.get("outputs", [])
            )
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            return None

    def list_workflows(self, agent_type: Optional[str] = None) -> List[BMADWorkflow]:
        """List all workflows, optionally filtered by agent type.

        Args:
            agent_type: Optional agent type filter

        Returns:
            List of matching workflows
        """
        if not agent_type:
            return self.catalog.workflows

        return [
            w for w in self.catalog.workflows
            if w.agent_type == agent_type
        ]

    def get_workflow(self, workflow_id: str) -> Optional[BMADWorkflow]:
        """Get specific workflow by ID.

        Args:
            workflow_id: Workflow identifier

        Returns:
            BMADWorkflow instance or None if not found
        """
        for workflow in self.catalog.workflows:
            if workflow.id == workflow_id:
                return workflow
        return None

    def search_workflows(self, query: str) -> List[BMADWorkflow]:
        """Search workflows by name or description.

        Args:
            query: Search query string

        Returns:
            List of matching workflows
        """
        query_lower = query.lower()
        return [
            w for w in self.catalog.workflows
            if query_lower in w.name.lower() or
               query_lower in w.description.lower()
        ]
