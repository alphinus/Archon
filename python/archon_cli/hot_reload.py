"""
Hot Reload Development Server

Watches for file changes and automatically restarts the Archon server.
Provides instant feedback for code changes during development.
"""

import time
import subprocess
import sys
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from rich.console import Console
from rich.panel import Panel

console = Console()


class ArchonReloadHandler(FileSystemEventHandler):
    """Handles file system events and triggers server restart."""
    
    def __init__(self, server_process, restart_callback):
        self.server_process = server_process
        self.restart_callback = restart_callback
        self.last_restart = 0
        self.debounce_seconds = 1  # Avoid multiple restarts
        
    def on_modified(self, event):
        """Called when a file is modified."""
        if event.is_directory:
            return
            
        # Only watch Python files
        if not event.src_path.endswith('.py'):
            return
            
        # Debounce rapid changes
        now = time.time()
        if now - self.last_restart < self.debounce_seconds:
            return
            
        self.last_restart = now
        
        # Show which file changed
        changed_file = Path(event.src_path).relative_to(Path.cwd())
        console.print(f"\n[yellow]📝 File changed: {changed_file}[/yellow]")
        
        # Restart server
        self.restart_callback()


class HotReloadServer:
    """Development server with hot reload capability."""
    
    def __init__(self, host='0.0.0.0', port=8181, watch_dir='src'):
        self.host = host
        self.port = port
        self.watch_dir = Path(watch_dir)
        self.server_process = None
        self.observer = None
        
    def start_server(self):
        """Start the Uvicorn server."""
        if self.server_process:
            self.stop_server()
            
        console.print(f"[bold green]🚀 Starting server on {self.host}:{self.port}[/bold green]")
        
        cmd = [
            "uvicorn",
            "src.server.main:app",
            "--host", self.host,
            "--port", str(self.port),
        ]
        
        self.server_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
    def stop_server(self):
        """Stop the running server."""
        if self.server_process:
            console.print("[yellow]⏹️  Stopping server...[/yellow]")
            self.server_process.terminate()
            try:
                self.server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.server_process.kill()
            self.server_process = None
            
    def restart_server(self):
        """Restart the server."""
        console.print("[bold cyan]🔄 Reloading...[/bold cyan]")
        self.stop_server()
        time.sleep(0.5)  # Brief pause
        self.start_server()
        console.print("[bold green]✓ Server reloaded[/bold green]")
        
    def start_watching(self):
        """Start watching for file changes."""
        if not self.watch_dir.exists():
            console.print(f"[red]Error: Watch directory {self.watch_dir} does not exist[/red]")
            return
            
        console.print(f"[cyan]👀 Watching {self.watch_dir}/ for changes...[/cyan]")
        console.print("[dim]Press Ctrl+C to stop[/dim]\n")
        
        # Create event handler
        event_handler = ArchonReloadHandler(
            self.server_process,
            self.restart_server
        )
        
        # Create observer
        self.observer = Observer()
        self.observer.schedule(event_handler, str(self.watch_dir), recursive=True)
        self.observer.start()
        
    def run(self):
        """Run the hot reload server."""
        console.print(Panel.fit(
            "[bold]🔥 Archon Hot Reload Dev Server[/bold]\n"
            f"Server: http://{self.host}:{self.port}\n"
            f"Watching: {self.watch_dir}/",
            border_style="blue"
        ))
        
        try:
            # Start server
            self.start_server()
            
            # Start watching
            self.start_watching()
            
            # Keep running
            while True:
                time.sleep(1)
                
                # Check if server is still running
                if self.server_process and self.server_process.poll() is not None:
                    console.print("[red]Server crashed! Restarting...[/red]")
                    self.start_server()
                    
        except KeyboardInterrupt:
            console.print("\n[yellow]Shutting down...[/yellow]")
            
        finally:
            if self.observer:
                self.observer.stop()
                self.observer.join()
            self.stop_server()
            console.print("[green]✓ Stopped[/green]")


def main(host='0.0.0.0', port=8181, watch_dir='src'):
    """Main entry point."""
    server = HotReloadServer(host, port, watch_dir)
    server.run()


if __name__ == '__main__':
    import sys
    
    host = sys.argv[1] if len(sys.argv) > 1 else '0.0.0.0'
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8181
    watch_dir = sys.argv[3] if len(sys.argv) > 3 else 'src'
    
    main(host, port, watch_dir)
