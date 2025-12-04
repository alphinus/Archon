"""
Archon CLI - Main Command Line Interface

Provides developer-friendly CLI for Archon operations:
- archon dev - Start development server with hot reload
- archon test - Run test suite
- archon new - Create new agent/project
- archon status - Check system status
- archon db - Database operations (seed, migrate, etc.)
"""

import typer
import asyncio
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich import print as rprint
from pathlib import Path

app = typer.Typer(
    name="archon",
    help="Archon AI Agent Platform CLI",
    add_completion=True
)

console = Console()


@app.command()
def dev(
    hot_reload: bool = typer.Option(
        True,
        "--hot-reload/--no-hot-reload",
        help="Enable hot reload for code changes"
    ),
    port: int = typer.Option(
        8000,
        "--port", "-p",
        help="Server port"
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        help="Enable debug mode with verbose logging"
    )
):
    """
    Start Archon development server with hot reload.
    
    This command starts all services (server, agents, UI) in development mode
    with optional hot reload for rapid iteration.
    
    Examples:
        archon dev
        archon dev --no-hot-reload
        archon dev --port 3000 --debug
    """
    console.print("[bold green]Starting Archon development server...[/bold green]")
    
    if hot_reload:
        console.print("[yellow]Hot reload enabled ♻️[/yellow]")
    
    if debug:
        console.print("[yellow]Debug mode enabled 🐛[/yellow]")
    
    # Import here to avoid circular dependencies
    from agents.devex.dev_server import start_dev_server
    
    asyncio.run(start_dev_server(
        hot_reload=hot_reload,
        port=port,
        debug=debug
    ))


@app.command()
def test(
    suite: Optional[str] = typer.Argument(
        None,
        help="Specific test suite to run (e.g., 'memory', 'events')"
    ),
    coverage: bool = typer.Option(
        True,
        "--coverage/--no-coverage",
        help="Generate coverage report"
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose", "-v",
        help="Verbose output"
    ),
    markers: Optional[str] = typer.Option(
        None,
        "--markers", "-m",
        help="Pytest markers to filter tests (e.g., 'unit', 'integration')"
    )
):
    """
    Run Archon test suite.
    
    Examples:
        archon test
        archon test memory
        archon test --no-coverage
        archon test -m unit
        archon test integration --verbose
    """
    console.print("[bold blue]Running Archon tests...[/bold blue]")
    
    from agents.devex.test_runner import run_tests_cli
    
    result = asyncio.run(run_tests_cli(
        suite=suite,
        coverage=coverage,
        verbose=verbose,
        markers=markers
    ))
    
    if result["status"] == "success":
        console.print(f"[bold green]✓ Tests passed: {result['passed']}/{result['total']}[/bold green]")
        if coverage and result.get("coverage"):
            console.print(f"[blue]Coverage: {result['coverage']}%[/blue]")
    else:
        console.print(f"[bold red]✗ Tests failed: {result['failed']}/{result['total']}[/bold red]")
        raise typer.Exit(code=1)


@app.command()
def new(
    name: str = typer.Argument(..., help="Project or agent name"),
    template: str = typer.Option(
        "agent",
        "--template", "-t",
        help="Template type: 'agent', 'project', 'skill'"
    ),
    path: Optional[Path] = typer.Option(
        None,
        "--path", "-p",
        help="Target directory (defaults to current directory)"
    )
):
    """
    Create new Archon project, agent, or skill.
    
    Templates:
        agent   - New agent from template
        project - New Archon project
        skill   - New skill module
    
    Examples:
        archon new my-agent
        archon new my-project --template project
        archon new data-processor --template agent --path ./agents/
    """
    console.print(f"[bold green]Creating new {template}: {name}[/bold green]")
    
    from agents.devex.project_scaffold import create_from_template
    
    result = create_from_template(
        name=name,
        template_type=template,
        target_path=path or Path.cwd()
    )
    
    if result["status"] == "success":
        console.print(f"[green]✓ Created {template} at: {result['path']}[/green]")
        console.print("\n[blue]Next steps:[/blue]")
        for step in result["next_steps"]:
            console.print(f"  • {step}")
    else:
        console.print(f"[red]✗ Error: {result['error']}[/red]")
        raise typer.Exit(code=1)


@app.command()
def status(
    detailed: bool = typer.Option(
        False,
        "--detailed", "-d",
        help="Show detailed status for each component"
    ),
    watch: bool = typer.Option(
        False,
        "--watch", "-w",
        help="Watch mode - continuously update status"
    )
):
    """
    Check Archon system status.
    
    Shows status of all services, agents, and infrastructure components.
    
    Examples:
        archon status
        archon status --detailed
        archon status --watch
    """
    from agents.devex.status_checker import get_system_status
    
    if watch:
        console.print("[yellow]Watch mode - Press Ctrl+C to exit[/yellow]\n")
        
        while True:
            try:
                status_data = asyncio.run(get_system_status(detailed=detailed))
                console.clear()
                _display_status(status_data, detailed)
                import time
                time.sleep(2)
            except KeyboardInterrupt:
                console.print("\n[yellow]Exiting watch mode[/yellow]")
                break
    else:
        status_data = asyncio.run(get_system_status(detailed=detailed))
        _display_status(status_data, detailed)


@app.command()
def db(
    operation: str = typer.Argument(
        ...,
        help="Database operation: 'seed', 'migrate', 'reset', 'backup'"
    ),
    environment: str = typer.Option(
        "dev",
        "--env", "-e",
        help="Environment: 'dev', 'staging', 'prod'"
    ),
    confirm: bool = typer.Option(
        False,
        "--confirm", "-y",
        help="Skip confirmation prompts"
    )
):
    """
    Database operations.
    
    Operations:
        seed    - Seed database with test data
        migrate - Run database migrations
        reset   - Reset database (DESTRUCTIVE)
        backup  - Create database backup
    
    Examples:
        archon db seed
        archon db seed --env staging
        archon db reset --confirm
        archon db backup
    """
    from agents.devex.db_operations import run_db_operation
    
    if operation == "reset" and not confirm:
        confirmed = typer.confirm(
            f"⚠️  This will DELETE ALL DATA in {environment} environment. Continue?"
        )
        if not confirmed:
            console.print("[yellow]Operation cancelled[/yellow]")
            raise typer.Exit()
    
    console.print(f"[bold blue]Running database operation: {operation}[/bold blue]")
    
    result = asyncio.run(run_db_operation(
        operation=operation,
        environment=environment
    ))
    
    if result["status"] == "success":
        console.print(f"[green]✓ {operation} completed successfully[/green]")
        if result.get("details"):
            console.print(f"[blue]{result['details']}[/blue]")
    else:
        console.print(f"[red]✗ Error: {result['error']}[/red]")
        raise typer.Exit(code=1)


@app.command()
def inspect(
    component: str = typer.Argument(
        ...,
        help="Component to inspect: 'memory', 'events', 'agents', 'sessions'"
    ),
    filter_by: Optional[str] = typer.Option(
        None,
        "--filter", "-f",
        help="Filter criteria (e.g., 'session_id=abc123')"
    ),
    limit: int = typer.Option(
        20,
        "--limit", "-n",
        help="Number of results to show"
    )
):
    """
    Inspect Archon components in real-time.
    
    Components:
        memory   - Memory system (session, working, long-term)
        events   - Event stream
        agents   - Agent status and skills
        sessions - Active sessions
    
    Examples:
        archon inspect memory
        archon inspect events --filter "severity=error"
        archon inspect sessions --limit 10
    """
    console.print(f"[bold blue]Inspecting: {component}[/bold blue]\n")
    
    from agents.devex.inspector import inspect_component
    
    data = asyncio.run(inspect_component(
        component=component,
        filter_by=filter_by,
        limit=limit
    ))
    
    _display_inspection_results(component, data)


def _display_status(status_data: dict, detailed: bool):
    """Display system status in formatted table."""
    table = Table(title="Archon System Status", show_header=True)
    table.add_column("Component", style="cyan", no_wrap=True)
    table.add_column("Status", style="green")
    
    if detailed:
        table.add_column("Details", style="blue")
    
    for component, info in status_data.items():
        status_emoji = "✓" if info["status"] == "healthy" else "✗"
        status_color = "green" if info["status"] == "healthy" else "red"
        
        row = [
            component,
            f"[{status_color}]{status_emoji} {info['status']}[/{status_color}]"
        ]
        
        if detailed:
            row.append(str(info.get("details", "")))
        
        table.add_row(*row)
    
    console.print(table)


def _display_inspection_results(component: str, data: dict):
    """Display inspection results."""
    if not data.get("items"):
        console.print("[yellow]No items found[/yellow]")
        return
    
    table = Table(title=f"{component.capitalize()} Inspection")
    
    # Add columns based on first item
    if data["items"]:
        first_item = data["items"][0]
        for key in first_item.keys():
            table.add_column(key.replace("_", " ").title(), style="cyan")
        
        # Add rows
        for item in data["items"]:
            table.add_row(*[str(v) for v in item.values()])
    
    console.print(table)
    console.print(f"\n[blue]Showing {len(data['items'])} of {data.get('total', len(data['items']))} items[/blue]")


@app.command()
def logs(
    service: Optional[str] = typer.Argument(
        None,
        help="Service to show logs for (e.g., 'server', 'data', 'testing')"
    ),
    follow: bool = typer.Option(
        False,
        "--follow", "-f",
        help="Follow log output"
    ),
    tail: int = typer.Option(
        100,
        "--tail", "-n",
        help="Number of lines to show"
    ),
    level: Optional[str] = typer.Option(
        None,
        "--level", "-l",
        help="Filter by log level (DEBUG, INFO, WARNING, ERROR)"
    )
):
    """
    Show logs for Archon services.
    
    Examples:
        archon logs
        archon logs server
        archon logs data --follow
        archon logs --level ERROR
    """
    from agents.devex.log_viewer import show_logs
    
    asyncio.run(show_logs(
        service=service,
        follow=follow,
        tail=tail,
        level=level
    ))


@app.command()
def version():
    """Show Archon version information."""
    from agents import __version__ as agents_version
    
    console.print(f"[bold]Archon AI Agent Platform[/bold]")
    console.print(f"Version: {agents_version}")
    console.print(f"7-Agent Architecture")
    console.print(f"\n[blue]Agents:[/blue]")
    agents = [
        "1. Testing & Validation",
        "2. Developer Experience (DevEx)",
        "3. UI/Frontend",
        "4. Documentation",
        "5. Orchestration",
        "6. Infrastructure",
        "7. Data & Mock"
    ]
    for agent in agents:
        console.print(f"  {agent}")


if __name__ == "__main__":
    app()
