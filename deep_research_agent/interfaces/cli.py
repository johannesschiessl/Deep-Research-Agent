from typing import Optional
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt
import traceback
import sys
import json

from agents.planner_agent import PlannerAgent, ResearchPlan
from agents.search_agent import SearchAgent
from agents.report_agent import ReportAgent

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

def display_search_results(search_summary_path):
    """Display the search results summary"""
    try:
        with open(search_summary_path, "r", encoding="utf-8") as f:
            summary = f.read()
        
        console.print(Panel(
            Markdown(summary),
            title="Research Summary",
            border_style="green"
        ))
    except Exception as e:
        console.print(f"[bold red]Error displaying search results: {e}[/bold red]")

def display_markdown_file(file_path):
    """Display the contents of a markdown file"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        console.print(Panel(
            Markdown(content),
            title="Research Report",
            border_style="green"
        ))
    except Exception as e:
        console.print(f"[bold red]Error displaying markdown file: {e}[/bold red]")

@app.command()
def research():
    """Start a new research session"""
    console.print(Panel.fit(
        "[bold blue]Deep Research Agent[/bold blue]\n"
        "Let me help you conduct thorough research on any topic.",
        border_style="blue"
    ))

    try:
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
        
        execute = Prompt.ask(
            "\n[bold blue]Would you like to execute this research plan?[/bold blue]",
            choices=["y", "n"],
            default="y"
        )
        
        if execute.lower() == "y":
            try:
                search_agent = SearchAgent()
                
                search_dir = run_dir / "search_results"
                search_dir.mkdir(exist_ok=True)
                
                total_steps = len(plan.steps)
                console.print(f"\n[bold cyan]Starting research with {total_steps} steps...[/bold cyan]")
                
                search_results = []
                
                for i, step in enumerate(plan.steps, 1):
                    try:
                        console.print(f"\n[bold cyan]Step {i}/{total_steps}:[/bold cyan] {step.instruction[:80]}...")
                        
                        with Progress(
                            SpinnerColumn(),
                            TextColumn("[progress.description]{task.description}"),
                            transient=True,
                        ) as progress:
                            progress.add_task(description=f"Researching step {i}...", total=None)
                            result = search_agent.execute_search_step(step, i)
                            search_results.append(result)
                        
                        result_path = search_dir / f"step_{i}_result.json"
                        with open(result_path, "w", encoding="utf-8") as f:
                            json.dump(result.model_dump(), f, indent=2, ensure_ascii=False)
                            
                        summary_path = search_dir / f"step_{i}_summary.txt"
                        with open(summary_path, "w", encoding="utf-8") as f:
                            f.write(f"RESEARCH STEP {i}: {step.instruction}\n\n")
                            f.write(f"SEARCH QUERY: {result.search_query}\n\n")
                            f.write(f"SUMMARY:\n{result.summary}\n\n")
                            f.write("CITATIONS:\n")
                            for citation in result.citations:
                                f.write(f"- {citation.get('title', 'No title')}: {citation.get('url', 'No URL')}\n")
                        
                        console.print(f"[green]✓[/green] Step {i} completed")
                        
                    except Exception as e:
                        console.print(f"[bold red]Error in step {i}:[/bold red] {str(e)}")
                        traceback.print_exc()
                        console.print("[yellow]Continuing with next step...[/yellow]")
                
                try:
                    console.print("\n[bold cyan]Creating research summary...[/bold cyan]")
                    combined_summary_path = run_dir / "research_summary.txt"
                    with open(combined_summary_path, "w", encoding="utf-8") as f:
                        f.write(f"RESEARCH SUMMARY FOR: {plan.query}\n\n")
                        f.write(f"REASONING: {plan.reasoning}\n\n")
                        
                        for result in search_results:
                            f.write(f"STEP {result.step_number}: {result.step_instruction}\n\n")
                            f.write(f"SUMMARY:\n{result.summary}\n\n")
                            f.write("---\n\n")
                    
                    console.print(f"\n[bold green]Research completed![/bold green]")
                    console.print(f"[bold cyan]Results saved to:[/bold cyan] {run_dir}")
                    
                    console.print(f"\n[bold cyan]Research Summary:[/bold cyan]")
                    display_search_results(combined_summary_path)
                    
                    generate_report = Prompt.ask(
                        "\n[bold blue]Would you like to generate a comprehensive research report?[/bold blue]",
                        choices=["y", "n"],
                        default="y"
                    )
                    
                    if generate_report.lower() == "y":
                        try:
                            console.print("\n[bold cyan]Generating comprehensive research report...[/bold cyan]")
                            
                            with Progress(
                                SpinnerColumn(),
                                TextColumn("[progress.description]{task.description}"),
                                transient=True,
                            ) as progress:
                                progress.add_task(description="Generating report...", total=None)
                                report_agent = ReportAgent()
                                report_path = report_agent.generate_and_save_report(plan, search_results, run_dir)
                            
                            console.print(f"\n[bold green]Research report generated![/bold green]")
                            console.print(f"[bold cyan]Report saved to:[/bold cyan] {report_path}")
                            
                            console.print(f"\n[bold cyan]Research Report:[/bold cyan]")
                            display_markdown_file(report_path)
                        except Exception as e:
                            console.print(f"[bold red]Error generating research report:[/bold red] {str(e)}")
                            traceback.print_exc()
                    else:
                        console.print("\n[bold yellow]Report generation skipped.[/bold yellow]")
                    
                except Exception as e:
                    console.print(f"[bold red]Error creating research summary:[/bold red] {str(e)}")
                    traceback.print_exc()
            
            except Exception as e:
                console.print(f"\n[bold red]Error executing research plan:[/bold red] {str(e)}")
                traceback.print_exc()
        else:
            console.print("\n[bold yellow]Research plan execution cancelled.[/bold yellow]")
    
    except Exception as e:
        console.print(f"\n[bold red]An error occurred:[/bold red] {str(e)}")
        traceback.print_exc()
        console.print("\n[bold red]Research session terminated due to an error.[/bold red]")

def main():
    try:
        app()
    except Exception as e:
        console.print(f"\n[bold red]Critical error:[/bold red] {str(e)}")
        traceback.print_exc()
        sys.exit(1)
