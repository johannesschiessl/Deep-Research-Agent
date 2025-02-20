from typing import Optional
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt

from agents.planner_agent import PlannerAgent, ResearchPlan

app = typer.Typer()
console = Console()

def display_plan(plan: ResearchPlan) -> None:
    """Display the research plan in a beautiful format"""
    console.print("\n")
    console.print(Panel(
        f"[bold blue]Research Query:[/bold blue]\n{plan.query}\n\n"
        f"[bold green]Reasoning:[/bold green]\n{plan.reasoning}\n\n"
        f"[bold yellow]Run ID:[/bold yellow] {plan.run_id}",
        title="Research Plan",
        border_style="blue"
    ))

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Step", style="dim")
    table.add_column("Instruction")
    table.add_column("Expected Outcome")

    for i, step in enumerate(plan.steps, 1):
        table.add_row(
            str(i),
            step.instruction,
            step.expected_outcome
        )

    console.print("\n")
    console.print(table)
    console.print("\n")

@app.command()
def research():
    """Start a new research session"""
    console.print(Panel.fit(
        "[bold blue]Deep Research Agent[/bold blue]\n"
        "Let me help you conduct thorough research on any topic.",
        border_style="blue"
    ))

    query = Prompt.ask("\n[bold green]What would you like to research?[/bold green]")

    planner = PlannerAgent()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(description="Creating research plan...", total=None)
        plan, run_dir = planner.create_initial_plan(query)

    display_plan(plan)
    
    console.print(f"\n[bold cyan]Plan saved to:[/bold cyan] {run_dir / 'plan.json'}")
    console.print("\n[bold blue]Press Enter to approve the plan[/bold blue]")
    input()

def main():
    app()
