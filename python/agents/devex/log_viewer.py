"""
Log Viewer for Archon Services

Provides real-time log viewing and filtering.
"""

import asyncio
from typing import Optional
import logging

logger = logging.getLogger(__name__)


async def show_logs(
    service: Optional[str] = None,
    follow: bool = False,
    tail: int = 100,
    level: Optional[str] = None
):
    """
    Show logs for services.
    
    Args:
        service: Specific service (None for all)
        follow: Follow mode (continuous)
        tail: Number of lines
        level: Log level filter
    """
    import subprocess
    
    if service:
        # Show logs for specific service
        cmd = ["docker", "compose", "logs"]
        if follow:
            cmd.append("-f")
        cmd.extend(["--tail", str(tail)])
        cmd.append(service)
    else:
        # Show logs for all services
        cmd = ["docker", "compose", "logs"]
        if follow:
            cmd.append("-f")
        cmd.extend(["--tail", str(tail)])
    
    # Run docker compose logs
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    try:
        for line in process.stdout:
            # Filter by level if specified
            if level:
                if level.upper() not in line.upper():
                    continue
            
            # Color code by level
            colored_line = _color_code_log(line)
            print(colored_line, end='')
            
    except KeyboardInterrupt:
        process.terminate()
        logger.info("Log viewing stopped")


def _color_code_log(line: str) -> str:
    """Add color coding to log lines based on level."""
    from rich.console import Console
    from rich.text import Text
    
    if "ERROR" in line or "CRITICAL" in line:
        return f"[red]{line}[/red]"
    elif "WARNING" in line:
        return f"[yellow]{line}[/yellow]"
    elif "INFO" in line:
        return f"[blue]{line}[/blue]"
    elif "DEBUG" in line:
        return f"[dim]{line}[/dim]"
    else:
        return line
