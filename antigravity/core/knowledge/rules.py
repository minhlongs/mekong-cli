"""
Rule Registry - Scalable rule management and semantic retrieval.
"""
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Set

# Set up logging
logger = logging.getLogger(__name__)

RULES_DIR = Path(".claude/rules")
GLOBAL_RULES_DIR = Path.home() / ".claude" / "rules"

class RuleRegistry:
    """
    Manages indexing and retrieval of rules for agents.
    Supports scaling to 500+ atomic rules with strict error handling.
    """
    def __init__(self, rules_dir: Path = RULES_DIR):
        self.rules_dir = rules_dir
        self.rules: Dict[str, Dict[str, Any]] = {}
        self.tag_index: Dict[str, Set[str]] = {}
        self.agent_index: Dict[str, Set[str]] = {}
        self.refresh()

    def refresh(self):
        """Rebuilds the rule index by parsing files recursively."""
        self.rules = {}
        self.tag_index = {}
        self.agent_index = {}

        # Collect all rule directories to scan (project-level + global fallback)
        dirs_to_scan = []
        if self.rules_dir.exists():
            dirs_to_scan.append(self.rules_dir)
        if GLOBAL_RULES_DIR.exists() and GLOBAL_RULES_DIR != self.rules_dir.resolve():
            dirs_to_scan.append(GLOBAL_RULES_DIR)

        if not dirs_to_scan:
            logger.warning(f"No rules directories found: {self.rules_dir}, {GLOBAL_RULES_DIR}")
            return

        for scan_dir in dirs_to_scan:
            for rule_file in scan_dir.rglob("*.md"):
                try:
                    metadata = self._parse_rule(rule_file)
                    # Use relative path as name — try scan_dir first, fallback to filename
                    try:
                        name = str(rule_file.relative_to(scan_dir))
                    except ValueError:
                        name = rule_file.name

                    self.rules[name] = metadata

                    # Index by tags
                    for tag in metadata.get("tags", []):
                        tag = tag.strip().lower()
                        if tag not in self.tag_index:
                            self.tag_index[tag] = set()
                        self.tag_index[tag].add(name)

                    # Index by agents
                    agents = metadata.get("agents", [])
                    if not agents:
                        agents = ["*"]

                    for agent in agents:
                        agent = agent.strip().lower()
                        if agent not in self.agent_index:
                            self.agent_index[agent] = set()
                        self.agent_index[agent].add(name)
                except Exception as e:
                    logger.error(f"❌ Failed to parse rule {rule_file}: {e}")

    def _parse_rule(self, rule_file: Path) -> Dict[str, Any]:
        """Parses metadata from rule file content (Frontmatter or Headers)."""
        try:
            content = rule_file.read_text(encoding="utf-8")
        except Exception as e:
            logger.error(f"Failed to read {rule_file}: {e}")
            return {}
            
        metadata = {
            "title": rule_file.stem,
            "priority": "P2",
            "tags": [],
            "agents": ["*"],
            "path": str(rule_file.absolute())
        }

        # Try to find Frontmatter
        fm_match = re.search(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
        if fm_match:
            fm_content = fm_match.group(1)
            for line in fm_content.split("\n"):
                if ":" in line:
                    key, val = line.split(":", 1)
                    key = key.strip().lower()
                    val = val.strip()
                    if key in ["tags", "agents"]:
                        # Handle [tag1, tag2] or simple csv
                        val = val.strip("[]")
                        metadata[key] = [v.strip() for v in val.split(",") if v.strip()]
                    else:
                        metadata[key] = val
        else:
            # Fallback to searching for specific markers in text if frontmatter is missing
            tags_match = re.search(r"tags:\s*\[(.*?)\]", content, re.I)
            if tags_match:
                metadata["tags"] = [t.strip() for t in tags_match.group(1).split(",") if t.strip()]

            agents_match = re.search(r"agents:\s*\[(.*?)\]", content, re.I)
            if agents_match:
                metadata["agents"] = [a.strip() for a in agents_match.group(1).split(",") if a.strip()]

            priority_match = re.search(r"priority:\s*(P[0-3])", content, re.I)
            if priority_match:
                metadata["priority"] = priority_match.group(1).upper()

        return metadata

    def get_rules_for_agent(self, agent_name: str) -> List[str]:
        """Retrieves all rules applicable to a specific agent."""
        agent_name = agent_name.lower()
        rules = self.agent_index.get(agent_name, set()).copy()
        rules.update(self.agent_index.get("*", set()))
        return sorted(list(rules))

    def get_relevant_rules(self, tags: List[str]) -> List[str]:
        """Retrieves rules matching any of the provided tags."""
        results = set()
        for tag in tags:
            tag = tag.strip().lower()
            results.update(self.tag_index.get(tag, set()))
        return sorted(list(results))

    def search_rules(self, query: str) -> List[str]:
        """Simple keyword search across titles and tags."""
        query = query.lower()
        results = set()
        for name, meta in self.rules.items():
            if query in name.lower() or query in meta.get("title", "").lower():
                results.add(name)
            for tag in meta.get("tags", []):
                if query in tag.lower():
                    results.add(name)
        return sorted(list(results))

# Global instance
rule_registry = RuleRegistry()
