# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Genome Command - Founder Genome capture and analysis CLI."""

import json
from typing import Optional, Dict, Any, List

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from src.services.genome_service import (
    get_sync_genome_service,
    get_genome_analyzer,
    GenomeAnalysisRequest,
    GenomeServiceError,
    EncryptionError,
)

console = Console()


def print_header(title: str) -> None:
    """Print a formatted header."""
    console.print()
    console.print(f"[bold cyan]{'=' * 60}[/bold cyan]")
    console.print(f"[bold cyan]{title.center(60)}[/bold cyan]")
    console.print(f"[bold cyan]{'=' * 60}[/bold cyan]")
    console.print()


def print_section(title: str) -> None:
    """Print a section header."""
    console.print()
    console.print(f"[bold yellow]{title}[/bold yellow]")
    console.print("-" * len(title))


def ask_question(
    question: str,
    default: Optional[str] = None,
    choices: Optional[List[str]] = None,
    password: bool = False,
    required: bool = True
) -> str:
    """Ask a question with validation."""
    while True:
        try:
            if password:
                from getpass import getpass
                answer = getpass(f"{question}: ") or ""
            else:
                if choices:
                    answer = Prompt.ask(
                        question,
                        choices=choices,
                        default=default
                    )
                else:
                    answer = Prompt.ask(question, default=default) or ""

            if not answer and required:
                console.print("[red]This field is required.[/red]")
                continue

            return answer
        except (KeyboardInterrupt, EOFError):
            console.print("\n[yellow]Interrupted.[/yellow]")
            raise typer.Exit(0)
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")


def ask_number(
    question: str,
    min_val: Optional[float] = None,
    max_val: Optional[float] = None,
    default: Optional[float] = None,
    required: bool = True
) -> float:
    """Ask for a numeric value with validation."""
    while True:
        try:
            answer = Prompt.ask(question, default=str(default) if default else None)
            if not answer and not required:
                return 0.0

            value = float(answer)

            if min_val is not None and value < min_val:
                console.print(f"[red]Value must be at least {min_val}[/red]")
                continue
            if max_val is not None and value > max_val:
                console.print(f"[red]Value must be at most {max_val}[/red]")
                continue

            return value
        except ValueError:
            console.print("[red]Please enter a valid number[/red]")
        except (KeyboardInterrupt, EOFError):
            console.print("\n[yellow]Interrupted.[/yellow]")
            raise typer.Exit(0)


def ask_yes_no(question: str, default: bool = False) -> bool:
    """Ask a yes/no question."""
    try:
        return Confirm.ask(question, default=default)
    except (KeyboardInterrupt, EOFError):
        console.print("\n[yellow]Interrupted.[/yellow]")
        raise typer.Exit(0)


def collect_founder_basics() -> Dict[str, Any]:
    """Collect basic founder information."""
    print_section("Founder Basics")

    data = {}

    data["name"] = ask_question("Full name", required=True)
    data["email"] = ask_question("Email address", required=True)
    data["phone"] = ask_question("Phone number (optional)", required=False)

    data["current_role"] = ask_question(
        "Current role/position",
        default="Founder"
    )

    data["years_experience"] = ask_number(
        "Years of professional experience",
        min_val=0,
        max_val=50
    )

    data["domain_experience"] = ask_number(
        "Years in current domain/industry",
        min_val=0,
        max_val=50
    )

    data["previous_ventures"] = ask_number(
        "Number of previous ventures (0 if first-time)",
        min_val=0,
        max_val=20
    )

    return data


def collect_founder_psyche() -> Dict[str, Any]:
    """Collect founder psychological profile."""
    print_section("Founder Psychology")

    console.print(
        "[dim]For each statement, rate from 1 (strongly disagree) to 7 (strongly agree)[/dim]"
    )
    console.print()

    questions = [
        ("I prefer to move fast and iterate rather than plan extensively", "execution_speed"),
        ("I am comfortable with significant uncertainty and risk", "risk_tolerance"),
        ("I can achieve meaningful results with limited resources", "capital_efficiency"),
        ("I have a clear, long-term vision that motivates others", "vision_clarity"),
        ("I enjoy recruiting and developing talented people", "team_building"),
        ("I deeply understand my customers' problems and needs", "customer_obsession"),
        ("I can pivot quickly when data shows my approach is wrong", "adaptability"),
        ("Setbacks energize me to try harder", "resilience"),
        ("I can identify patterns and plan multiple steps ahead", "strategic_thinking"),
        ("My skills and experience are perfectly matched to my market", "founder_market_fit"),
    ]

    scores = {}
    for statement, trait in questions:
        score = ask_number(
            f"[{trait.replace('_', ' ').title()}] {statement} (1-7)",
            min_val=1,
            max_val=7,
            default=4
        )
        # Normalize to 0-1
        scores[trait] = round((score - 1) / 6, 2)

    return scores


def collect_business_context() -> Dict[str, Any]:
    """Collect business context information."""
    print_section("Business Context")

    data = {}

    data["industry"] = ask_question(
        "Primary industry/market",
        choices=[
            "tech/software", "e-commerce", "fintech", "healthtech",
            "edtech", "consumer", "b2b/saas", "marketplace",
            "hardware/iot", "crypto/web3", "other"
        ]
    )

    data["stage"] = ask_question(
        "Current startup stage",
        choices=[
            "idea/pre-mvp", "mvp/early-traction", "pmf/early-revenue",
            "growth/scaling", "mature/scale-up"
        ]
    )

    data["team_size"] = ask_number(
        "Current team size (including yourself)",
        min_val=1,
        max_val=500
    )

    data["capital_raised"] = ask_question(
        "Capital raised to date",
        choices=[
            "0 (bootstrap)", "<$100k", "$100k-$500k",
            "$500k-$2m", "$2m-$10m", "$10m+"
        ]
    )

    data["funding_plan"] = ask_question(
        "Funding plans for next 12 months",
        choices=["bootstrap", "friends-and-family", "angel", "seed", "series-a", "not-sure"]
    )

    data["competitive_background"] = ask_yes_no(
        "Do you have competitive/athletic background?",
        default=False
    )

    data["multiple_ventures"] = ask_yes_no(
        "Is this one of multiple ventures you've founded?",
        default=False
    )

    data["pivots_experienced"] = ask_number(
        "Number of major pivots experienced",
        min_val=0,
        max_val=10
    )

    return data


def collect_goals_priorities() -> Dict[str, Any]:
    """Collect founder goals and priorities."""
    print_section("Goals & Priorities")

    data = {}

    data["primary_goal"] = ask_question(
        "Primary goal for next 18 months",
        choices=[
            "achieve product-market fit",
            "reach first $100k arr",
            "build initial team",
            "raise seed round",
            "acquire first 100 customers",
            "validate technology",
            "other"
        ]
    )

    data["risk_appetite"] = ask_number(
        "Risk appetite for next decisions (1=preserve capital, 7=bet big)",
        min_val=1,
        max_val=7,
        default=4
    )

    data["timeline"] = ask_question(
        "Founder timeline/commitment",
        choices=["all-in (5+ years)", "committed (2-3 years)", "exploring (1 year)"]
    )

    data["exit_expectation"] = ask_question(
        "Exit expectation",
        choices=["10+ years", "5-7 years", "3-5 years", "building forever", "not-sure"]
    )

    data["cofounder_status"] = ask_question(
        "Co-founder situation",
        choices=["solo", "co-founders (2)", "co-founders (3+)", "looking for co-founder"]
    )

    if data["cofounder_status"] in ["co-founders (2)", "co-founders (3+)"]:
        data["cofounder_count"] = ask_number(
            "How many co-founders total?",
            min_val=2,
            max_val=10
        )

    data["hiring_priority"] = ask_question(
        "Top hiring priority",
        choices=["engineering", "product", "sales/marketing", "operations", "design", "none"]
    )

    return data


def run_genome_init_wizard(
    founder_id: Optional[str] = None,
    skip_ai: bool = False,
    output_json: bool = False
) -> Dict[str, Any]:
    """
    Interactive wizard for founder genome capture.

    Args:
        founder_id: Optional founder identifier (generated if not provided)
        skip_ai: Skip AI analysis
        output_json: Return JSON instead of interactive prompts

    Returns:
        Dictionary with genome data and analysis
    """
    console.print()
    console.print(
        Panel.fit(
            "[bold]Founder Genome Capture[/bold]\n"
            "Build your founder DNA profile for AI-powered insights",
            border_style="cyan"
        )
    )

    if output_json and not founder_id:
        console.print("[red]--json requires --founder-id[/red]")
        raise typer.Exit(1)

    # Collect data
    genome_data: Dict[str, Any] = {}

    if not output_json:
        console.print("\n[bold]Let's capture your founder profile.[/bold]")
        console.print("This will take about 5-10 minutes and enable personalized insights.")
        console.print()

        if not ask_yes_no("Continue with genome capture?", default=True):
            raise typer.Exit(0)

        # Interactive collection
        basics = collect_founder_basics()
        genome_data.update(basics)

        psyche = collect_founder_psyche()
        genome_data["trait_scores"] = psyche

        context = collect_business_context()
        genome_data.update(context)

        goals = collect_goals_priorities()
        genome_data.update(goals)

        # Generate founder_id if not provided
        if not founder_id:
            import hashlib
            email_hash = hashlib.sha256(basics["email"].encode()).hexdigest()[:12]
            founder_id = f"founder_{email_hash}"
            genome_data["founder_id"] = founder_id
        else:
            genome_data["founder_id"] = founder_id

        # Optional additional notes
        if ask_yes_no("Add any additional notes about your background or goals?", default=False):
            notes = ask_question("Notes", required=False)
            if notes:
                genome_data["notes"] = notes
    else:
        # JSON mode - read from stdin if not provided as args
        if not founder_id:
            console.print("[red]Founder ID required for JSON mode[/red]")
            raise typer.Exit(1)

        genome_data["founder_id"] = founder_id
        console.print("[yellow]JSON mode requires stdin input - use interactive mode for wizard[/yellow]")

    # Save genome
    service = get_sync_genome_service()

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            progress.add_task(description="Saving encrypted genome...", total=None)
            genome = service.save_genome(
                founder_id=genome_data["founder_id"],
                raw_genome=genome_data
            )

        console.print(f"[green]✓[/green] Genome saved (ID: {genome.id})")

        # AI Analysis
        analysis_result: Optional[Dict[str, Any]] = None

        if not skip_ai:
            console.print()
            if not ask_yes_no("Run AI analysis on your profile?", default=True):
                skip_ai = True

        if not skip_ai:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                progress.add_task(
                    description="Running AI analysis (may take 30-60 seconds)...",
                    total=None
                )

                analyzer = get_genome_analyzer()
                request = GenomeAnalysisRequest(
                    founder_id=genome_data["founder_id"],
                    raw_responses=genome_data,
                    analysis_type="full",
                    include_recommendations=True,
                    context={
                        "industry": genome_data.get("industry"),
                        "stage": genome_data.get("stage"),
                    }
                )

                analysis_result = analyzer.analyze_genome(request, "full")

            # Update genome with analysis
            if analysis_result:
                genome.analysis_summary = analysis_result.get("executive_summary")
                genome.confidence_score = analysis_result.get("confidence")
                genome.trait_scores = analysis_result.get("trait_scores", {})
                genome.cluster_id = _assign_cluster_id(analysis_result.get("cluster"))

                # Re-save to update with analysis
                service.save_genome(
                    founder_id=genome.founder_id,
                    raw_genome=genome.raw_genome or {},
                    analysis_summary=genome.analysis_summary,
                    confidence_score=genome.confidence_score,
                    trait_scores=genome.trait_scores,
                    cluster_id=genome.cluster_id,
                )

                console.print("[green]✓[/green] AI analysis complete")

                # Display summary
                if analysis_result.get("executive_summary"):
                    console.print()
                    console.print(Panel(
                        analysis_result["executive_summary"][:500],
                        title="Executive Summary",
                        border_style="green"
                    ))

                if analysis_result.get("insights"):
                    console.print()
                    print_section("Key Insights")
                    for insight in analysis_result["insights"][:5]:
                        console.print(f"  • {insight}")

                if analysis_result.get("cluster"):
                    console.print()
                    console.print(f"[bold]Cluster:[/bold] {analysis_result['cluster']}")
                    console.print(
                        f"[dim]Confidence: {analysis_result.get('confidence', 0):.1%}[/dim]"
                    )

    except GenomeServiceError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted.[/yellow]")
        raise typer.Exit(0)

    result = {
        "founder_id": genome_data["founder_id"],
        "genome_id": genome.id,
        "genome_hash": genome.genome_hash[:16] + "...",
        "encrypted": True,
        "traits_count": len(genome.trait_scores),
        "overall_rating": genome.overall_rating(),
    }

    if analysis_result:
        result["analysis"] = {
            "cluster": analysis_result.get("cluster"),
            "confidence": analysis_result.get("confidence"),
            "trait_scores": analysis_result.get("trait_scores"),
        }

    return result


def _assign_cluster_id(cluster_name: Optional[str]) -> Optional[int]:
    """Convert cluster name to numeric ID."""
    if not cluster_name:
        return None
    clusters = {
        "Serial Entrepreneur": 1,
        "Visionary": 2,
        "Operator": 3,
        "Experimenter": 4,
        "Specialist": 5,
        "Challenger": 6,
    }
    return clusters.get(cluster_name)


def run_genome_view(
    founder_id: str,
    show_raw: bool = False,
    json_output: bool = False
) -> None:
    """View a stored genome profile."""
    service = get_sync_genome_service()

    try:
        genome = service.load_genome(founder_id)

        if not genome:
            console.print(f"[red]Genome not found for founder: {founder_id}[/red]")
            raise typer.Exit(1)

        if json_output:
            output = {
                "founder_id": genome.founder_id,
                "id": genome.id,
                "analysis_summary": genome.analysis_summary,
                "confidence_score": genome.confidence_score,
                "trait_scores": genome.trait_scores,
                "cluster_id": genome.cluster_id,
                "overall_rating": genome.overall_rating(),
                "dominant_traits": genome.dominant_traits(),
                "created_at": genome.created_at.isoformat() if genome.created_at else None,
            }
            if show_raw and genome.raw_genome:
                output["raw_genome"] = genome.raw_genome
            typer.echo(json.dumps(output, indent=2, default=str))
            return

        console.print()
        console.print(Panel(
            f"[bold]Founder Genome[/bold]\n"
            f"ID: {genome.founder_id}\n"
            f"Record: #{genome.id}\n"
            f"Created: {genome.created_at}",
            border_style="cyan"
        ))

        if genome.analysis_summary:
            console.print()
            console.print(Panel(
                genome.analysis_summary,
                title="AI Analysis",
                border_style="green"
            ))

        if genome.trait_scores:
            console.print()
            print_section("Trait Scores")
            table = Table(show_header=True)
            table.add_column("Trait", style="cyan")
            table.add_column("Score", justify="right")
            table.add_column("Interpretation")

            for trait, score in sorted(genome.trait_scores.items(), key=lambda x: x[1], reverse=True):
                if score >= 0.7:
                    level = "[green]High[/green]"
                elif score >= 0.4:
                    level = "[yellow]Medium[/yellow]"
                else:
                    level = "[red]Low[/red]"
                table.add_row(
                    trait.replace('_', ' ').title(),
                    f"{score:.2f}",
                    level
                )

            console.print(table)

        console.print()
        console.print(f"[bold]Overall Rating:[/bold] {genome.overall_rating():.2%}")
        console.print("[dim]Dominant traits:[/dim] " +
            ", ".join(f"{t[0]} ({t[1]:.2f})" for t in genome.dominant_traits(3))
        )

    except EncryptionError as e:
        console.print(f"[red]Decryption failed: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


def run_genome_list(limit: int = 20, json_output: bool = False) -> None:
    """List all stored genomes."""
    service = get_sync_genome_service()

    try:
        genomes = service.get_all_genomes(limit=limit)

        if json_output:
            output = []
            for genome in genomes:
                output.append({
                    "id": genome.id,
                    "founder_id": genome.founder_id,
                    "analysis_summary": genome.analysis_summary,
                    "confidence_score": genome.confidence_score,
                    "overall_rating": genome.overall_rating(),
                    "created_at": genome.created_at.isoformat() if genome.created_at else None,
                })
            typer.echo(json.dumps(output, indent=2, default=str))
            return

        if not genomes:
            console.print("[yellow]No genomes found.[/yellow]")
            return

        table = Table(title=f"Founder Genomes (showing {len(genomes)})")
        table.add_column("ID", style="cyan")
        table.add_column("Founder")
        table.add_column("Cluster", style="magenta")
        table.add_column("Confidence", justify="right")
        table.add_column("Rating", justify="right")
        table.add_column("Created", style="dim")

        for genome in genomes:
            cluster = "N/A"
            if genome.cluster_id:
                clusters = {1: "Serial", 2: "Visionary", 3: "Operator",
                           4: "Experimenter", 5: "Specialist", 6: "Challenger"}
                cluster = clusters.get(genome.cluster_id, str(genome.cluster_id))

            conf = f"{genome.confidence_score:.1%}" if genome.confidence_score else "N/A"
            rating = f"{genome.overall_rating():.1%}"

            created = genome.created_at.strftime("%Y-%m-%d") if genome.created_at else "N/A"

            table.add_row(
                str(genome.id),
                genome.founder_id[:30],
                cluster,
                conf,
                rating,
                created
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


def run_genome_similarity(
    target_founder: str,
    limit: int = 5
) -> None:
    """Find similar founders."""
    service = get_sync_genome_service()

    try:
        target = service.load_genome(target_founder)
        if not target:
            console.print(f"[red]Target founder not found: {target_founder}[/red]")
            raise typer.Exit(1)

        console.print(f"\n[bold]Finding founders similar to[/bold] {target_founder}")
        console.print(f"[dim]Target traits: {target.trait_scores}[/dim]\n")

        matches = service.find_similar_genomes(
            target.trait_scores,
            limit=limit,
            exclude_founder_id=target_founder
        )

        if not matches:
            console.print("[yellow]No similar founders found.[/yellow]")
            return

        table = Table(title=f"Top {len(matches)} Matches")
        table.add_column("Founder", style="cyan")
        table.add_column("Similarity", justify="right")
        table.add_column("Matching Traits")
        table.add_column("Divergent Traits")
        table.add_column("Insight", style="dim")

        for match in matches:
            matching = ", ".join(match.matching_traits[:3])
            divergent = ", ".join(match.divergent_traits[:2])
            insight = match.insights[:50] + "..." if len(match.insights) > 50 else match.insights

            table.add_row(
                match.founder_genome.founder_id[:20],
                f"{match.similarity_score:.1%}",
                matching,
                divergent,
                insight
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


def run_genome_delete(founder_id: str, force: bool = False) -> None:
    """Delete a genome record."""
    if not force and not Confirm.ask(
        f"Are you sure you want to delete genome for {founder_id}? This cannot be undone."
    ):
        console.print("[yellow]Cancelled.[/yellow]")
        return

    service = get_sync_genome_service()

    if service.delete_genome(founder_id):
        console.print(f"[green]✓[/green] Deleted genome for {founder_id}")
    else:
        console.print(f"[red]Failed to delete genome for {founder_id}[/red]")


def register_genome_command(app: typer.Typer) -> None:
    """Register genome command with main CLI."""

    genome_app = typer.Typer(help="Founder Genome Capture & Analysis")

    @genome_app.command(name="init")
    def genome_init(
        founder_id: Optional[str] = typer.Option(
            None, "--founder-id", help="Founder identifier (generated if not provided)"
        ),
        skip_ai: bool = typer.Option(
            False, "--skip-ai", help="Skip AI analysis"
        ),
        json_output: bool = typer.Option(
            False, "--json", "-j", help="JSON output mode"
        ),
    ):
        """Interactive wizard to capture founder profile and generate genome."""
        try:
            result = run_genome_init_wizard(
                founder_id=founder_id,
                skip_ai=skip_ai,
                output_json=json_output
            )

            if json_output:
                typer.echo(json.dumps(result, indent=2))
            else:
                console.print()
                console.print(Panel(
                    f"[bold green]Genome Capture Complete![/bold green]\n\n"
                    f"Founder ID: {result['founder_id']}\n"
                    f"Genome Hash: {result['genome_hash']}\n"
                    f"Overall Rating: {result['overall_rating']:.1%}\n"
                    f"Traits Captured: {result['traits_count']}/10\n\n"
                    f"Your profile is encrypted and stored securely.\n"
                    f"Use [bold]mekong genome view {result['founder_id']}[/bold] to view.",
                    border_style="green"
                ))
        except typer.Exit:
            raise
        except Exception as e:
            console.print(f"[red]Failed: {e}[/red]")
            raise typer.Exit(1)

    @genome_app.command(name="view")
    def genome_view(
        founder_id: str = typer.Argument(..., help="Founder identifier"),
        show_raw: bool = typer.Option(
            False, "--raw", help="Show raw genome data"
        ),
        json_output: bool = typer.Option(
            False, "--json", "-j", help="JSON output"
        ),
    ):
        """View a stored founder genome."""
        run_genome_view(founder_id, show_raw, json_output)

    @genome_app.command(name="list")
    def genome_list(
        limit: int = typer.Option(
            20, "--limit", "-l", help="Maximum number to show"
        ),
        json_output: bool = typer.Option(
            False, "--json", "-j", help="JSON output"
        ),
    ):
        """List all stored genomes."""
        run_genome_list(limit, json_output)

    @genome_app.command(name="similar")
    def genome_similar(
        founder_id: str = typer.Argument(..., help="Target founder ID"),
        limit: int = typer.Option(
            5, "--limit", "-l", help="Number of matches"
        ),
    ):
        """Find founders with similar profiles."""
        run_genome_similarity(founder_id, limit)

    @genome_app.command(name="delete")
    def genome_delete(
        founder_id: str = typer.Argument(..., help="Founder identifier to delete"),
        force: bool = typer.Option(
            False, "--force", help="Skip confirmation"
        ),
    ):
        """Delete a founder genome."""
        run_genome_delete(founder_id, force)

    @genome_app.command(name="analyze")
    def genome_analyze(
        founder_id: str = typer.Argument(..., help="Founder identifier"),
        analysis_type: str = typer.Option(
            "full", "--type", "-t",
            help="Analysis type: full, quick_traits, cluster, recommendations"
        ),
    ):
        """Run AI analysis on a genome."""
        service = get_sync_genome_service()
        analyzer = get_genome_analyzer()

        try:
            genome = service.load_genome(founder_id)
            if not genome:
                console.print(f"[red]Genome not found: {founder_id}[/red]")
                raise typer.Exit(1)

            if not genome.raw_genome:
                console.print("[red]Cannot analyze - raw genome data not available[/red]")
                raise typer.Exit(1)

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                progress.add_task(
                    description=f"Running {analysis_type} analysis...",
                    total=None
                )

                request = GenomeAnalysisRequest(
                    founder_id=founder_id,
                    raw_responses=genome.raw_genome,
                    analysis_type=analysis_type
                )

                result = analyzer.analyze_genome(request, analysis_type)

            typer.echo(json.dumps(result, indent=2))

        except Exception as e:
            console.print(f"[red]Analysis failed: {e}[/red]")
            raise typer.Exit(1)

    # Register with main app
    app.add_typer(genome_app, name="genome", help="Founder Genome Capture & Analysis")


__all__ = [
    "register_genome_command",
    "run_genome_init_wizard",
]
