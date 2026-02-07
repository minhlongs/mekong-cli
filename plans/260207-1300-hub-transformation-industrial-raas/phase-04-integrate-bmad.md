---
phase: 04
title: "Integrate BMAD Workflows"
priority: P1
status: pending
effort: 3h
---

# Phase 04: Integrate BMAD Workflows

## Context Links

- BMAD Source: `_bmad/` (169 workflows)
- Target: `packages/core/bmad/`
- Engine: `src/core/orchestrator.py`
- Dependencies: Phase 03 (working engine required)

## Overview

**Priority:** P1
**Status:** Pending
**Effort:** 3h

Integrate 169 BMAD workflows into the mekong-cli by creating a symlink or copy strategy, ensuring they are accessible via the Plan-Execute-Verify engine and CLI commands.

## Key Insights

- BMAD contains 169 production-ready workflows
- Workflows organized by agent type (PM, Architect, Dev, QA, etc.)
- Need to preserve BMAD structure while making accessible to engine
- Some workflows may need adaptation for mekong-cli context
- Symlink preferred for live updates, copy for stability

## Requirements

### Functional Requirements
- All 169 BMAD workflows accessible via CLI
- Workflow discovery mechanism (list, search)
- Integration with RecipeOrchestrator
- Support for workflow parameters/context
- Workflow validation before execution
- Error handling for missing/invalid workflows

### Non-Functional Requirements
- Zero modification to original BMAD files
- Fast workflow loading (<100ms)
- Clear documentation for each workflow
- Version compatibility checks
- Graceful degradation if workflows unavailable

## Architecture

### Integration Strategy

```
_bmad/                           packages/core/bmad/
├── agents/                      ├── workflows/     (symlink or copy)
│   ├── pm/                      │   ├── pm/
│   ├── architect/               │   ├── architect/
│   ├── developer/               │   ├── developer/
│   └── ...                      │   └── ...
└── workflows/                   ├── loader.py      (workflow discovery)
                                 ├── validator.py   (workflow validation)
                                 └── catalog.py     (workflow metadata)
```

### Workflow Loader Architecture

```python
class BMADWorkflowLoader:
    def __init__(self, bmad_path: str):
        self.bmad_path = Path(bmad_path)
        self.catalog = self._build_catalog()

    def list_workflows(self, agent_type: str = None) -> List[Workflow]:
        # Return available workflows

    def get_workflow(self, workflow_id: str) -> Workflow:
        # Load specific workflow

    def validate_workflow(self, workflow: Workflow) -> bool:
        # Validate workflow structure
```

### CLI Integration

```python
# mekong bmad list
# mekong bmad run <workflow-id> --context <json>
# mekong bmad info <workflow-id>
```

## Related Code Files

### Files to Create
- `packages/core/bmad/__init__.py` - Package initialization
- `packages/core/bmad/loader.py` - Workflow loading logic
- `packages/core/bmad/validator.py` - Workflow validation
- `packages/core/bmad/catalog.py` - Workflow metadata/index
- `packages/core/bmad/models.py` - BMAD workflow Pydantic models
- `src/cli/bmad_commands.py` - CLI commands for BMAD
- `tests/core/test_bmad_loader.py` - Loader tests
- `tests/core/test_bmad_workflows.py` - Workflow execution tests

### Files to Modify
- `src/core/orchestrator.py` - Add BMAD workflow support
- `src/cli/main.py` - Register BMAD commands
- `pyproject.toml` - Add bmad dependencies if needed

### Files to Reference
- `_bmad/workflows/**/*.md` - All BMAD workflow files
- `_bmad/agents/*/` - Agent-specific workflows
- `.claude/rules/binh-phap-workflow.md` - BMAD integration rules

## Implementation Steps

### Step 1: Create Symlink Strategy
```bash
# Create symlink from _bmad to packages/core/bmad/workflows
mkdir -p packages/core/bmad
cd packages/core/bmad
ln -s ../../../_bmad workflows

# Verify symlink
ls -la workflows/
```

**Alternative (Copy Strategy for Stability):**
```bash
# Copy BMAD workflows
mkdir -p packages/core/bmad/workflows
cp -r _bmad/* packages/core/bmad/workflows/

# Add .gitignore entry
echo "packages/core/bmad/workflows/" >> .gitignore
```

### Step 2: Create Workflow Models
```python
# packages/core/bmad/models.py
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from pathlib import Path

class BMADWorkflow(BaseModel):
    id: str
    name: str
    description: str
    agent_type: str  # pm, architect, developer, qa, etc.
    file_path: Path
    parameters: Dict[str, any] = {}
    prerequisites: List[str] = []
    outputs: List[str] = []

class WorkflowCatalog(BaseModel):
    workflows: List[BMADWorkflow]
    total_count: int
    agent_types: List[str]

    @classmethod
    def build_from_directory(cls, bmad_path: Path):
        # Scan directory and build catalog
        pass
```

### Step 3: Implement Workflow Loader
```python
# packages/core/bmad/loader.py
from pathlib import Path
from typing import List, Optional
import yaml
from .models import BMADWorkflow, WorkflowCatalog

class BMADWorkflowLoader:
    def __init__(self, bmad_path: str = "_bmad"):
        self.bmad_path = Path(bmad_path)
        self.catalog = None
        self._load_catalog()

    def _load_catalog(self):
        """Scan BMAD directory and build workflow catalog."""
        workflows = []

        # Scan all workflow files
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
        """Parse workflow markdown file and extract metadata."""
        try:
            content = file_path.read_text()

            # Extract YAML frontmatter if present
            if content.startswith("---"):
                _, frontmatter, body = content.split("---", 2)
                metadata = yaml.safe_load(frontmatter)
            else:
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
        """List all workflows, optionally filtered by agent type."""
        if not agent_type:
            return self.catalog.workflows

        return [
            w for w in self.catalog.workflows
            if w.agent_type == agent_type
        ]

    def get_workflow(self, workflow_id: str) -> Optional[BMADWorkflow]:
        """Get specific workflow by ID."""
        for workflow in self.catalog.workflows:
            if workflow.id == workflow_id:
                return workflow
        return None

    def search_workflows(self, query: str) -> List[BMADWorkflow]:
        """Search workflows by name or description."""
        query_lower = query.lower()
        return [
            w for w in self.catalog.workflows
            if query_lower in w.name.lower() or
               query_lower in w.description.lower()
        ]
```

### Step 4: Create Workflow Validator
```python
# packages/core/bmad/validator.py
from .models import BMADWorkflow
from typing import Dict, List

class WorkflowValidator:
    @staticmethod
    def validate(workflow: BMADWorkflow) -> Dict:
        """Validate workflow structure and prerequisites."""
        errors = []
        warnings = []

        # Check file exists
        if not workflow.file_path.exists():
            errors.append(f"Workflow file not found: {workflow.file_path}")

        # Check prerequisites
        for prereq in workflow.prerequisites:
            # Validate prerequisite exists
            pass

        # Check required parameters
        if workflow.parameters:
            # Validate parameter types
            pass

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
```

### Step 5: Create Workflow Catalog
```python
# packages/core/bmad/catalog.py
from pathlib import Path
import json
from .loader import BMADWorkflowLoader

class WorkflowCatalog:
    """Persistent catalog of BMAD workflows."""

    def __init__(self, cache_path: str = ".mekong/bmad_catalog.json"):
        self.cache_path = Path(cache_path)
        self.loader = BMADWorkflowLoader()

    def build_catalog(self):
        """Build and cache workflow catalog."""
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

    def load_catalog(self):
        """Load cached catalog."""
        if self.cache_path.exists():
            return json.loads(self.cache_path.read_text())
        return self.build_catalog()
```

### Step 6: Integrate with Orchestrator
```python
# src/core/orchestrator.py (modify)
from packages.core.bmad.loader import BMADWorkflowLoader

class RecipeOrchestrator:
    def __init__(self):
        self.planner = RecipePlanner()
        self.executor = RecipeExecutor()
        self.verifier = RecipeVerifier()
        self.bmad_loader = BMADWorkflowLoader()  # NEW

    def run_bmad_workflow(self, workflow_id: str, context: dict = None):
        """Execute BMAD workflow via orchestrator."""
        workflow = self.bmad_loader.get_workflow(workflow_id)

        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_id}")

        # Load workflow content
        workflow_content = workflow.file_path.read_text()

        # Convert BMAD workflow to Recipe
        recipe = self._bmad_to_recipe(workflow, workflow_content, context)

        # Execute via normal flow
        results = self.executor.execute(recipe)
        verification = self.verifier.verify(results, recipe)

        return {
            "workflow": workflow,
            "results": results,
            "verification": verification
        }

    def _bmad_to_recipe(self, workflow, content, context):
        """Convert BMAD workflow to Recipe format."""
        # Parse BMAD markdown to extract tasks
        # Create Recipe object
        pass
```

### Step 7: Add CLI Commands
```python
# src/cli/bmad_commands.py
import typer
from rich.console import Console
from rich.table import Table
from packages.core.bmad.loader import BMADWorkflowLoader
from packages.core.bmad.catalog import WorkflowCatalog
from src.core.orchestrator import RecipeOrchestrator

app = typer.Typer(name="bmad", help="BMAD workflow management")
console = Console()

@app.command("list")
def list_workflows(
    agent_type: str = typer.Option(None, help="Filter by agent type")
):
    """List available BMAD workflows."""
    loader = BMADWorkflowLoader()
    workflows = loader.list_workflows(agent_type)

    table = Table(title=f"BMAD Workflows ({len(workflows)} total)")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Agent", style="yellow")
    table.add_column("Description")

    for workflow in workflows:
        table.add_row(
            workflow.id,
            workflow.name,
            workflow.agent_type,
            workflow.description[:60] + "..." if len(workflow.description) > 60 else workflow.description
        )

    console.print(table)

@app.command("info")
def workflow_info(workflow_id: str):
    """Show detailed workflow information."""
    loader = BMADWorkflowLoader()
    workflow = loader.get_workflow(workflow_id)

    if not workflow:
        console.print(f"[red]Workflow not found: {workflow_id}[/red]")
        raise typer.Exit(1)

    console.print(f"[bold]Workflow:[/bold] {workflow.name}")
    console.print(f"[bold]ID:[/bold] {workflow.id}")
    console.print(f"[bold]Agent Type:[/bold] {workflow.agent_type}")
    console.print(f"[bold]Description:[/bold] {workflow.description}")
    console.print(f"[bold]File:[/bold] {workflow.file_path}")

    if workflow.prerequisites:
        console.print(f"[bold]Prerequisites:[/bold] {', '.join(workflow.prerequisites)}")

    if workflow.parameters:
        console.print("[bold]Parameters:[/bold]")
        for key, value in workflow.parameters.items():
            console.print(f"  - {key}: {value}")

@app.command("run")
def run_workflow(
    workflow_id: str,
    context: str = typer.Option(None, help="Context as JSON string")
):
    """Execute a BMAD workflow."""
    orchestrator = RecipeOrchestrator()

    context_dict = {}
    if context:
        import json
        context_dict = json.loads(context)

    console.print(f"[bold]Executing workflow:[/bold] {workflow_id}")

    result = orchestrator.run_bmad_workflow(workflow_id, context_dict)

    if result["verification"]["overall_passed"]:
        console.print("[green]✅ Workflow completed successfully[/green]")
    else:
        console.print("[red]❌ Workflow failed[/red]")
        for rec in result["verification"]["recommendations"]:
            console.print(f"  - {rec}")

@app.command("catalog")
def build_catalog():
    """Build and cache workflow catalog."""
    catalog = WorkflowCatalog()
    data = catalog.build_catalog()

    console.print(f"[green]Catalog built:[/green]")
    console.print(f"  - Total workflows: {data['total_count']}")
    console.print(f"  - Agent types: {', '.join(data['agent_types'])}")
    console.print(f"  - Cache: {catalog.cache_path}")

@app.command("search")
def search_workflows(query: str):
    """Search workflows by name or description."""
    loader = BMADWorkflowLoader()
    results = loader.search_workflows(query)

    console.print(f"[bold]Search results for '{query}':[/bold] {len(results)} found")

    for workflow in results:
        console.print(f"  [cyan]{workflow.id}[/cyan] - {workflow.name} ({workflow.agent_type})")
```

### Step 8: Register BMAD Commands
```python
# src/cli/main.py (modify)
from .bmad_commands import app as bmad_app

app = typer.Typer()
app.add_typer(bmad_app, name="bmad")

# Now: mekong bmad list, mekong bmad run <id>, etc.
```

### Step 9: Write Tests
```python
# tests/core/test_bmad_loader.py
from packages.core.bmad.loader import BMADWorkflowLoader

def test_load_workflows():
    loader = BMADWorkflowLoader()
    assert loader.catalog.total_count == 169
    assert len(loader.catalog.workflows) == 169

def test_list_workflows_by_agent():
    loader = BMADWorkflowLoader()
    pm_workflows = loader.list_workflows(agent_type="pm")
    assert len(pm_workflows) > 0
    assert all(w.agent_type == "pm" for w in pm_workflows)

def test_get_workflow():
    loader = BMADWorkflowLoader()
    workflow = loader.get_workflow("create-prd")
    assert workflow is not None
    assert workflow.agent_type == "pm"

def test_search_workflows():
    loader = BMADWorkflowLoader()
    results = loader.search_workflows("architecture")
    assert len(results) > 0
```

### Step 10: Integration Test
```bash
# Build catalog
mekong bmad catalog

# List all workflows
mekong bmad list

# List PM workflows
mekong bmad list --agent-type pm

# Get workflow info
mekong bmad info create-prd

# Run workflow
mekong bmad run create-prd --context '{"product": "API Gateway"}'

# Search workflows
mekong bmad search architecture
```

### Step 11: Commit Checkpoint
```bash
git add packages/core/bmad/
git add src/cli/bmad_commands.py
git add tests/core/test_bmad_*.py
git commit -m "feat: integrate 169 BMAD workflows with CLI engine"
```

## Todo List

- [ ] Create symlink or copy BMAD to packages/core/bmad/
- [ ] Pydantic models for workflows
- [ ] Workflow loader implementation
- [ ] Workflow validator
- [ ] Workflow catalog builder
- [ ] Integrate with orchestrator
- [ ] CLI commands (list, info, run, search, catalog)
- [ ] Register commands in main CLI
- [ ] Unit tests for loader
- [ ] Unit tests for workflows
- [ ] Integration test all commands
- [ ] Documentation for BMAD usage
- [ ] Git checkpoint

## Success Criteria

### Definition of Done
- ✅ All 169 BMAD workflows discoverable via `mekong bmad list`
- ✅ Workflows executable via `mekong bmad run <id>`
- ✅ Workflow search functional
- ✅ Workflow info shows metadata
- ✅ Catalog cached for fast access
- ✅ Integration with orchestrator seamless
- ✅ All tests pass
- ✅ Zero errors in workflow loading

### Validation Methods
```bash
# Workflow discovery
mekong bmad catalog
mekong bmad list | wc -l  # Should be ~169

# Agent filtering
mekong bmad list --agent-type pm
mekong bmad list --agent-type architect

# Search
mekong bmad search "PRD"
mekong bmad search "architecture"

# Info
mekong bmad info create-prd
mekong bmad info dev-story

# Execution (if safe workflow)
mekong bmad run brainstorm --context '{"topic": "AI features"}'

# Tests
pytest tests/core/test_bmad_*.py
```

## Risk Assessment

### Potential Issues
1. **BMAD structure mismatch** - Workflows not in expected format
   - Mitigation: Flexible parser, graceful degradation
2. **Missing workflows** - Some of 169 not found
   - Mitigation: Catalog reports missing, warnings logged
3. **Execution incompatibility** - BMAD workflows need Claude Code
   - Mitigation: Document prerequisites, skip unsupported workflows
4. **Performance** - Loading 169 workflows slow
   - Mitigation: Catalog caching, lazy loading

### Mitigation Strategies
- Robust error handling in loader
- Clear logging for missing/invalid workflows
- Catalog cache for performance
- Documentation for workflow adaptation

## Security Considerations

- Validate workflow files before execution
- Never execute arbitrary code from workflows
- Sanitize workflow parameters
- Audit workflow content for malicious commands

## Next Steps

**Dependencies:** Phase 03 (engine must be operational)

**Blocks:** Phase 05 (quality verification)

**Follow-up:** After completion, proceed to Phase 05 (Verify Quality) to ensure the integrated system meets all quality gates and production standards.
