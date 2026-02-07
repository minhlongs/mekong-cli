"""
Mekong CLI - Recipe Executor

Executes recipes parsed from Markdown files.
"""

import subprocess
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from src.core.parser import Recipe, RecipeStep

class RecipeExecutor:
    """Executes a Recipe step by step."""

    def __init__(self, recipe: Recipe):
        self.recipe = recipe
        self.console = Console()

    def execute_step(self, step: RecipeStep) -> bool:
        """
        Execute a single step.
        Supports multiple execution modes: shell, llm, api
        """
        self.console.print(f"\n[bold blue]Step {step.order}:[/bold blue] {step.title}")

        # Determine execution mode from step params or description
        step_type = step.params.get("type", "shell") if step.params else "shell"

        # Handle different execution types
        if step_type == "llm":
            return self._execute_llm_step(step)
        elif step_type == "api":
            return self._execute_api_step(step)
        else:
            return self._execute_shell_step(step)

    def _execute_llm_step(self, step: RecipeStep) -> bool:
        """Execute LLM generation step."""
        self.console.print(f"[cyan][LLM] Generating:[/cyan] {step.description}")
        # Placeholder for LLM execution
        # Would integrate with Antigravity Proxy or OpenAI
        self.console.print("[dim]LLM execution not yet fully wired[/dim]")
        return True

    def _execute_api_step(self, step: RecipeStep) -> bool:
        """Execute API call step."""
        url = step.params.get("url", "unknown") if step.params else "unknown"
        self.console.print(f"[cyan][API] Calling:[/cyan] {url}")
        # Placeholder for API execution
        self.console.print("[dim]API execution not yet fully wired[/dim]")
        return True

    def _execute_shell_step(self, step: RecipeStep) -> bool:
        """Execute shell command step."""
        # The description contains the command.
        command = step.description.strip()

        if not command:
            self.console.print("[yellow]Skipping empty step[/yellow]")
            return True

        self.console.print(f"[dim]Running:[/dim] {command}")

        try:
            # Using shell=True to allow simple commands like 'echo "foo"' or pipes.
            # Security warning: This executes arbitrary code from the markdown file.
            process = subprocess.run(
                command,
                shell=True,
                check=True,
                text=True,
                capture_output=True
            )

            if process.stdout:
                self.console.print(Panel(process.stdout.strip(), title="Output", border_style="green", expand=False))

            if process.stderr:
                self.console.print(Panel(process.stderr.strip(), title="Stderr", border_style="yellow", expand=False))

            return True

        except subprocess.CalledProcessError as e:
            self.console.print(f"[bold red]Error executing step {step.order}[/bold red]")
            if e.stdout:
                 self.console.print(Panel(e.stdout.strip(), title="Output (Partial)", border_style="yellow", expand=False))
            if e.stderr:
                self.console.print(Panel(e.stderr.strip(), title="Error Output", border_style="red", expand=False))
            return False
        except Exception as e:
             self.console.print(f"[bold red]Unexpected error:[/bold red] {str(e)}")
             return False

    def run(self) -> bool:
        """Run the full recipe."""
        self.console.print(
            Panel(
                Text(self.recipe.description, style="italic"),
                title=f"🚀 Running: {self.recipe.name}",
                border_style="cyan"
            )
        )

        for step in self.recipe.steps:
            success = self.execute_step(step)
            if not success:
                self.console.print("\n[bold red]❌ Recipe execution failed.[/bold red]")
                return False

        self.console.print(f"\n[bold green]✨ Recipe '{self.recipe.name}' completed successfully![/bold green]")
        return True
