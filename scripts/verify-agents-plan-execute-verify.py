import sys
import os
from rich.console import Console

# Add project root to sys.path
sys.path.append(os.getcwd())

from src.agents import LeadHunter, ContentWriter, RecipeCrawler

console = Console()

def test_agent(agent_class, input_data, agent_name):
    console.print(f"\n[bold blue]Testing {agent_name}...[/bold blue]")
    try:
        agent = agent_class()
        console.print(f"[dim]Initialized {agent_name}[/dim]")

        # Test Plan
        tasks = agent.plan(input_data)
        console.print(f"[green]Plan created:[/green] {len(tasks)} tasks")

        # Test Execute (first task)
        if tasks:
            first_task = tasks[0]
            console.print(f"[dim]Executing task: {first_task.description}[/dim]")
            result = agent.execute(first_task)

            if result.success:
                console.print(f"[bold green]✅ Task '{first_task.id}' passed[/bold green]")
                console.print(f"Output: {result.output}")
            else:
                console.print(f"[bold red]❌ Task '{first_task.id}' failed[/bold red]")
                console.print(f"Error: {result.error}")
                return False

        return True
    except Exception as e:
        console.print(f"[bold red]❌ Exception testing {agent_name}:[/bold red] {e}")
        return False

def main():
    success = True

    # Test LeadHunter
    if not test_agent(LeadHunter, "example.com", "LeadHunter"):
        success = False

    # Test ContentWriter
    if not test_agent(ContentWriter, "AI Agents", "ContentWriter"):
        success = False

    # Test RecipeCrawler
    if not test_agent(RecipeCrawler, "marketing", "RecipeCrawler"):
        success = False

    if success:
        console.print("\n[bold green]✨ All agents verified successfully![/bold green]")
        sys.exit(0)
    else:
        console.print("\n[bold red]❌ Some agents failed verification.[/bold red]")
        sys.exit(1)

if __name__ == "__main__":
    main()
