"""
Archon CLI - Command Line Interface for Archon Development

Provides commands for:
- Project initialization
- Development server
- Testing
- Memory management
- Agent operations
- Worker control
- Database operations
"""

import click
from rich.console import Console
from rich.table import Table
from rich.progress import track
from rich import print as rprint

console = Console()

@click.group()
@click.version_option(version="1.0.0")
def cli():
    """
    🏗️ Archon CLI - Your Development Companion
    
    Manage your Archon development workflow from the command line.
    """
    pass


# ============================================================================
# CORE COMMANDS
# ============================================================================

@cli.command()
@click.option('--path', default='.', help='Path to initialize project')
def init(path):
    """Initialize a new Archon agent project."""
    console.print(f"[bold green]🚀 Initializing Archon project at {path}[/bold green]")
    
    # TODO: Create project structure
    console.print("[yellow]⚠️  Project initialization coming soon[/yellow]")


@cli.command()
@click.option('--host', default='0.0.0.0', help='Host to bind to')
@click.option('--port', default=8181, type=int, help='Port to bind to')
@click.option('--reload', is_flag=True, default=True, help='Auto-reload on file changes (hot reload)')
@click.option('--no-reload', is_flag=True, help='Disable auto-reload')
@click.option('--watch-dir', default='src', help='Directory to watch for changes')
def dev(host, port, reload, no_reload, watch_dir):
    """Start development server with hot reload."""
    import subprocess
    import sys
    from pathlib import Path
    
    # Disable reload if --no-reload is set
    if no_reload:
        reload = False
    
    if reload:
        # Use hot reload server
        console.print(f"\n[bold blue]🔥 Starting Archon with Hot Reload[/bold blue]")
        console.print(f"[cyan]   Host: {host}:{port}[/cyan]")
        console.print(f"[cyan]   Watching: {watch_dir}/[/cyan]")
        console.print(f"[cyan]   Auto-reload: enabled[/cyan]\n")
        
        try:
            from archon_cli.hot_reload import HotReloadServer
            
            server = HotReloadServer(host, port, watch_dir)
            server.run()
            
        except ImportError:
            console.print("[red]Hot reload requires watchdog library[/red]")
            console.print("[yellow]Install with: uv add --dev watchdog[/yellow]")
            sys.exit(1)
        except KeyboardInterrupt:
            console.print("\n[yellow]Server stopped[/yellow]")
    else:
        # No reload - standard uvicorn
        console.print(f"\n[bold blue]🔧 Starting Archon server[/bold blue]")
        console.print(f"[cyan]   Host: {host}:{port}[/cyan]")
        console.print(f"[cyan]   Auto-reload: disabled[/cyan]\n")
        
        try:
            cmd = [
                "uvicorn",
                "src.server.main:app",
                "--host", host,
                "--port", str(port),
            ]
            
            console.print(f"[dim]Running: {' '.join(cmd)}[/dim]\n")
            
            result = subprocess.run(cmd, cwd=Path(__file__).parent.parent)
            sys.exit(result.returncode)
            
        except KeyboardInterrupt:
            console.print("\n[yellow]Server stopped[/yellow]")
        except Exception as e:
            console.print(f"[bold red]Error: {e}[/bold red]")
            import traceback
            console.print(f"[dim]{traceback.format_exc()}[/dim]")
            sys.exit(1)


@cli.command()
@click.option('--coverage', is_flag=True, help='Run with coverage report')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.option('--markers', '-m', help='Run tests matching expression')
@click.option('--keyword', '-k', help='Run tests matching keyword')
@click.option('--file', help='Run specific test file')
def test(coverage, verbose, markers, keyword, file):
    """Run tests with pytest."""
    import subprocess
    import sys
    from pathlib import Path
    
    console.print("\n[bold green]🧪 Running Archon tests[/bold green]\n")
    
    try:
        # Build pytest command
        cmd = ["pytest"]
        
        if verbose:
            cmd.append("-v")
        else:
            cmd.append("-q")
        
        if coverage:
            cmd.extend(["--cov=src", "--cov-report=term-missing", "--cov-report=html"])
            console.print("[cyan]Coverage report will be generated[/cyan]")
        
        if markers:
            cmd.extend(["-m", markers])
            console.print(f"[cyan]Running tests with marker: {markers}[/cyan]")
        
        if keyword:
            cmd.extend(["-k", keyword])
            console.print(f"[cyan]Running tests matching: {keyword}[/cyan]")
        
        if file:
            cmd.append(file)
            console.print(f"[cyan]Running test file: {file}[/cyan]")
        else:
            cmd.append("tests/")
        
        console.print(f"[dim]Command: {' '.join(cmd)}[/dim]\n")
        
        # Run pytest
        result = subprocess.run(cmd, cwd=Path(__file__).parent.parent)
        
        if result.returncode == 0:
            console.print("\n[bold green]✓ All tests passed![/bold green]")
        else:
            console.print(f"\n[bold red]✗ Tests failed (exit code: {result.returncode})[/bold red]")
        
        if coverage:
            console.print("\n[cyan]Coverage report: htmlcov/index.html[/cyan]")
        
        sys.exit(result.returncode)
        
    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        sys.exit(1)


# ============================================================================
# MEMORY COMMANDS
# ============================================================================

@cli.group()
def memory():
    """Memory management commands."""
    pass


@memory.command('list')
@click.option('--user-id', required=True, help='User ID')
@click.option('--type', type=click.Choice(['session', 'working', 'longterm', 'all']), default='all', help='Memory type')
@click.option('--limit', default=10, help='Number of items to show')
def memory_list(user_id, type, limit):
    """List memories for a user."""
    import asyncio
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    
    async def _list_memories():
        try:
            from src.memory import SessionMemory, WorkingMemory, LongTermMemory
            
            console.print(f"\n[bold cyan]💭 Memories for user: {user_id}[/bold cyan]\n")
            
            if type in ['session', 'all']:
                try:
                    sm = SessionMemory()
                    # TODO: Need session_id parameter
                    console.print("[yellow]⚠️  Session memory requires session_id[/yellow]")
                except Exception as e:
                    console.print(f"[red]Session Memory error: {e}[/red]")
            
            if type in ['working', 'all']:
                try:
                    wm = WorkingMemory()
                    memories = await wm.get_recent(user_id, limit=limit)
                    
                    if memories:
                        table = Table(show_header=True, header_style="bold magenta")
                        table.add_column("Type", style="cyan", width=12)
                        table.add_column("Content", style="green", width=50)
                        table.add_column("Created", style="yellow", width=20)
                        
                        for mem in memories[:limit]:
                            content_preview = str(mem.content)[:47] + "..." if len(str(mem.content)) > 50 else str(mem.content)
                            table.add_row(
                                mem.memory_type,
                                content_preview,
                                mem.created_at.strftime("%Y-%m-%d %H:%M")
                            )
                        
                        console.print(f"[bold]Working Memory ({len(memories)} total)[/bold]")
                        console.print(table)
                    else:
                        console.print("[yellow]No working memories found[/yellow]")
                except Exception as e:
                    console.print(f"[red]Working Memory error: {e}[/red]")
            
            if type in ['longterm', 'all']:
                try:
                    ltm = LongTermMemory()
                    facts = await ltm.get_important(user_id, min_score=0.5, limit=limit)
                    
                    if facts:
                        table = Table(show_header=True, header_style="bold magenta")
                        table.add_column("Type", style="cyan", width=12)
                        table.add_column("Content", style="green", width=40)
                        table.add_column("Importance", style="blue", width=12)
                        table.add_column("Access Count", style="yellow", width=12)
                        
                        for fact in facts[:limit]:
                            content_preview = str(fact.content)[:37] + "..." if len(str(fact.content)) > 40 else str(fact.content)
                            table.add_row(
                                fact.memory_type,
                                content_preview,
                                f"{fact.importance:.2f}",
                                str(fact.access_count)
                            )
                        
                        console.print(f"\n[bold]Long-Term Memory ({len(facts)} total)[/bold]")
                        console.print(table)
                    else:
                        console.print("[yellow]No long-term memories found[/yellow]")
                except Exception as e:
                    console.print(f"[red]Long-Term Memory error: {e}[/red]")
                    
        except Exception as e:
            console.print(f"[bold red]Error: {e}[/bold red]")
            import traceback
            console.print(f"[dim]{traceback.format_exc()}[/dim]")
    
    asyncio.run(_list_memories())


@memory.command('clear')
@click.option('--user-id', required=True, help='User ID')
@click.option('--type', type=click.Choice(['working', 'longterm', 'all']), default='all', help='Memory type to clear')
@click.confirmation_option(prompt='Are you sure you want to clear memories?')
def memory_clear(user_id, type):
    """Clear memories for a user."""
    import asyncio
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    
    async def _clear_memories():
        try:
            from src.memory import WorkingMemory, LongTermMemory
            
            console.print(f"\n[bold red]🗑️  Clearing {type} memories for user: {user_id}[/bold red]\n")
            
            deleted_count = 0
            
            if type in ['working', 'all']:
                try:
                    wm = WorkingMemory()
                    # TODO: Implement clear method
                    console.print("[yellow]Working Memory clear: Not yet implemented[/yellow]")
                except Exception as e:
                    console.print(f"[red]Error clearing working memory: {e}[/red]")
            
            if type in ['longterm', 'all']:
                try:
                    ltm = LongTermMemory()
                    # TODO: Implement clear method
                    console.print("[yellow]Long-Term Memory clear: Not yet implemented[/yellow]")
                except Exception as e:
                    console.print(f"[red]Error clearing long-term memory: {e}[/red]")
            
            console.print(f"\n[green]✓ Cleared {deleted_count} memories[/green]")
                    
        except Exception as e:
            console.print(f"[bold red]Error: {e}[/bold red]")
    
    asyncio.run(_clear_memories())


@memory.command('export')
@click.option('--user-id', required=True, help='User ID')
@click.option('--output', default='memories.json', help='Output file')
def memory_export(user_id, output):
    """Export memories to JSON."""
    import asyncio
    import json
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    
    async def _export_memories():
        try:
            from src.memory import WorkingMemory, LongTermMemory
            
            console.print(f"[bold green]📦 Exporting memories to {output}[/bold green]")
            
            data = {
                "user_id": user_id,
                "exported_at": str(asyncio.get_event_loop().time()),
                "working_memory": [],
                "longterm_memory": []
            }
            
            # Export working memory
            try:
                wm = WorkingMemory()
                memories = await wm.get_recent(user_id, limit=1000)
                data["working_memory"] = [
                    {
                        "id": mem.id,
                        "type": mem.memory_type,
                        "content": mem.content,
                        "metadata": mem.metadata,
                        "created_at": mem.created_at.isoformat(),
                        "expires_at": mem.expires_at.isoformat() if mem.expires_at else None
                    }
                    for mem in memories
                ]
                console.print(f"[green]✓ Exported {len(memories)} working memories[/green]")
            except Exception as e:
                console.print(f"[yellow]Warning: Could not export working memory: {e}[/yellow]")
            
            # Export long-term memory
            try:
                ltm = LongTermMemory()
                facts = await ltm.get_important(user_id, min_score=0.0, limit=10000)
                data["longterm_memory"] = [
                    {
                        "id": fact.id,
                        "type": fact.memory_type,
                        "content": fact.content,
                        "importance": fact.importance,
                        "metadata": fact.metadata,
                        "created_at": fact.created_at.isoformat(),
                        "access_count": fact.access_count
                    }
                    for fact in facts
                ]
                console.print(f"[green]✓ Exported {len(facts)} long-term facts[/green]")
            except Exception as e:
                console.print(f"[yellow]Warning: Could not export long-term memory: {e}[/yellow]")
            
            # Write to file
            with open(output, 'w') as f:
                json.dump(data, f, indent=2)
            
            console.print(f"\n[bold green]✓ Successfully exported to {output}[/bold green]")
            console.print(f"[dim]Total: {len(data['working_memory'])} working + {len(data['longterm_memory'])} long-term[/dim]")
                    
        except Exception as e:
            console.print(f"[bold red]Error: {e}[/bold red]")
            import traceback
            console.print(f"[dim]{traceback.format_exc()}[/dim]")
    
    asyncio.run(_export_memories())


# ============================================================================
# AGENT COMMANDS
# ============================================================================

@cli.group()
def agent():
    """Agent management commands."""
    pass


@agent.command('create')
@click.argument('template')
@click.option('--name', help='Agent name')
def agent_create(template, name):
    """Create a new agent from template."""
    console.print(f"[bold green]🤖 Creating agent from template: {template}[/bold green]")
    
    # TODO: Create agent
    console.print("[yellow]⚠️  Agent creation coming soon[/yellow]")


@agent.command('list')
def agent_list():
    """List all registered agents."""
    console.print("[bold cyan]🤖 Registered Agents[/bold cyan]\n")
    
    # TODO: List agents
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Type", style="yellow")
    table.add_column("Status", style="blue")
    
    # Sample data
    table.add_row("agent_001", "Customer Support", "ChatAgent", "active")
    table.add_row("agent_002", "Code Reviewer", "ChatAgent", "active")
    
    console.print(table)


# ============================================================================
# WORKER COMMANDS
# ============================================================================

@cli.group()
def worker():
    """Worker management commands."""
    pass


@worker.command('status')
def worker_status():
    """Check worker health status."""
    console.print("[bold cyan]⚙️  Worker Status[/bold cyan]\n")
    
    # TODO: Get real worker status
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Worker", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Last Run", style="yellow")
    table.add_column("Next Run", style="blue")
    
    # Sample data
    table.add_row("MemoryConsolidator", "running", "2 min ago", "58 min")
    table.add_row("CleanupWorker", "running", "1 hour ago", "23 hours")
    table.add_row("EventRetryWorker", "running", "30 sec ago", "4 min 30s")
    
    console.print(table)


@worker.command('restart')
@click.argument('worker_name')
@click.confirmation_option(prompt='Are you sure you want to restart this worker?')
def worker_restart(worker_name):
    """Restart a specific worker."""
    console.print(f"\n[bold yellow]🔄 Restarting worker: {worker_name}[/bold yellow]\n")
    
    # TODO: Implement actual worker restart
    console.print("[yellow]Worker restart functionality pending WorkerSupervisor integration[/yellow]")
    console.print(f"[dim]Would restart: {worker_name}[/dim]")


@worker.command('logs')
@click.argument('worker_name', required=False)
@click.option('--follow', '-f', is_flag=True, help='Follow log output')
@click.option('--lines', '-n', default=50, help='Number of lines to show')
def worker_logs(worker_name, follow, lines):
    """Stream worker logs."""
    import subprocess
    
    if worker_name:
        console.print(f"\n[bold cyan]📜 Logs for worker: {worker_name}[/bold cyan]\n")
    else:
        console.print("\n[bold cyan]📜 All worker logs[/bold cyan]\n")
    
    # TODO: Implement actual log streaming
    console.print("[yellow]Worker log streaming pending implementation[/yellow]")
    
    if follow:
        console.print("[dim]Would follow logs with tail -f[/dim]")
    else:
        console.print(f"[dim]Would show last {lines} lines[/dim]")


# ============================================================================
# DATABASE COMMANDS
# ============================================================================

@cli.group()
def db():
    """Database management commands."""
    pass


@db.command('migrate')
def db_migrate():
    """Run database migrations."""
    console.print("[bold green]🔄 Running migrations...[/bold green]")
    
    # TODO: Run migrations
    console.print("[yellow]⚠️  Migration execution coming soon[/yellow]")


@db.command('seed')
@click.option('--scenario', type=click.Choice(['customer_support', 'code_review', 'data_analysis', 'content_creation', 'multi_agent']), help='Specific scenario to seed')
@click.option('--all', 'seed_all', is_flag=True, help='Seed all scenarios')
def db_seed(scenario, seed_all):
    """Seed database with mock data."""
    import asyncio
    import subprocess
    import sys
    
    console.print("[bold green]🌱 Seeding database with mock data...[/bold green]\n")
    
    try:
        # Run the seeding script
        cmd = ["python", "seed_test_database.py"]
        
        if scenario:
            cmd.append(scenario)
        elif not seed_all:
            # If neither scenario nor --all specified, ask
            console.print("[yellow]No scenario specified. Use --all to seed all scenarios or specify one:[/yellow]")
            console.print("  - customer_support")
            console.print("  - code_review")
            console.print("  - data_analysis")
            console.print("  - content_creation")
            console.print("  - multi_agent")
            sys.exit(1)
        
        # Run seeder
        result = subprocess.run(cmd, capture_output=False, text=True)
        
        if result.returncode == 0:
            console.print("\n[bold green]✓ Database seeded successfully[/bold green]")
        else:
            console.print(f"\n[bold red]✗ Seeding failed with exit code {result.returncode}[/bold red]")
            sys.exit(result.returncode)
            
    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")


@db.command('reset')
@click.confirmation_option(prompt='Are you sure you want to reset the database?')
def db_reset():
    """Reset database (dangerous!)."""
    console.print("[bold red]⚠️  Resetting database...[/bold red]")
    
    # TODO: Reset database
    console.print("[yellow]⚠️  Database reset coming soon[/yellow]")


# ============================================================================
# ENTRY POINT
# ============================================================================

def main():
    """Main entry point."""
    cli()


if __name__ == '__main__':
    main()
