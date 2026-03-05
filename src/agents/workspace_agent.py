from typing import List, Dict, Any, Optional
import subprocess
import json
import os
from src.core.agent_base import AgentBase

class WorkspaceAgent(AgentBase):
    """
    Official Google Workspace Agent powered by @googleworkspace/cli (gws).
    Provides native access to Drive, Gmail, Calendar, Sheets, Docs, Chat, Admin.
    """
    
    def __init__(self):
        # The base agent might have a different signature, adjusting based on standard pattern
        super().__init__()
        self.name = "workspace"
        self.description = "Google Workspace official integration (gws)"
        self._check_gws_installed()

    def _check_gws_installed(self) -> None:
        """Ensure gws CLI is installed and available in PATH."""
        try:
            subprocess.run(
                ["gws", "--version"], 
                capture_output=True, 
                text=True, 
                check=True
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise Exception(
                "❌ @googleworkspace/cli (gws) is not installed or not in PATH.\n"
                "Please run: npm install -g @googleworkspace/cli"
            )

    def plan(self, goal: str) -> List[Dict[str, Any]]:
        """
        Since gws operates as a direct REST-like CLI, many tasks map 1:1.
        For complex goals, we delegate to LLM planner.
        """
        # We rely on the core LLM planner for multi-step Workspace tasks
        # returning an empty list tells the Orchestrator to use the LLM to figure it out
        return []

    def execute(self, steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Execute gws CLI commands based on the steps generated.
        Expects steps with 'command' or 'action' mapping to gws <service> <resource> <method>
        """
        results = []
        for step in steps:
            command = step.get("command", "")
            # Ensure we only run gws commands for security
            if not command.startswith("gws "):
                command = f"gws {command}"
                
            # Add json output flag for structured parsing if not present and not dry-run
            if "--json" not in command and "--dry-run" not in command:
                # Need to be careful here, gws uses `--params` and `--json` for input bodies
                # so we just let the planner do it correctly or parse stdout directly.
                pass

            try:
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                # Try to parse JSON output if possible
                output = result.stdout.strip()
                try:
                    parsed_output = json.loads(output)
                    results.append({"step": step.get("title", ""), "status": "success", "output": parsed_output})
                except json.JSONDecodeError:
                    results.append({"step": step.get("title", ""), "status": "success", "output": output})
                    
            except subprocess.CalledProcessError as e:
                error_msg = e.stderr.strip() or e.stdout.strip()
                if "accessNotConfigured" in error_msg or "invalid_grant" in error_msg:
                    error_msg += "\n💡 Hint: Run 'gws auth setup' or check 'scripts/gws-auth-setup.sh'"
                
                results.append({"step": step.get("title", ""), "status": "failed", "error": error_msg})
                break # Stop on first failure

        success = all(r.get("status") == "success" for r in results)
        return {
            "status": "success" if success else "failed",
            "results": results
        }

    def verify(self, results: Dict[str, Any]) -> bool:
        """Verify the results of the execution."""
        return results.get("status") == "success"
