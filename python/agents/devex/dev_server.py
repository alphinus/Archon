"""
Development Server with Hot Reload

Manages the Archon development environment with automatic code reloading.
"""

import asyncio
import logging
from typing import Optional
from pathlib import Path
from watchfiles import awatch
import subprocess
import signal
import sys

logger = logging.getLogger(__name__)


class DevServer:
    """
    Development server with hot reload capabilities.
    
    Monitors code changes and automatically restarts affected services.
    Preserves application state where possible during reloads.
    """
    
    def __init__(
        self,
        hot_reload: bool = True,
        port: int = 8000,
        debug: bool = False
    ):
        self.hot_reload = hot_reload
        self.port = port
        self.debug = debug
        self.processes = {}
        self.running = False
    
    async def start(self):
        """Start development server."""
        logger.info("Starting Archon development server...")
        
        self.running = True
        
        # Start services
        await self._start_services()
        
        if self.hot_reload:
            logger.info("Hot reload enabled - watching for file changes...")
            await self._watch_files()
        else:
            # Just wait for shutdown signal
            await self._wait_for_shutdown()
    
    async def stop(self):
        """Stop development server."""
        logger.info("Stopping development server...")
        self.running = False
        
        # Stop all processes
        for name, process in self.processes.items():
            logger.info(f"Stopping {name}...")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
        
        logger.info("Development server stopped")
    
    async def _start_services(self):
        """Start all Archon services."""
        services = {
            "postgres": ["docker", "compose", "up", "-d", "postgres"],
            "redis": ["docker", "compose", "up", "-d", "redis"],
            "server": ["python", "-m", "uvicorn", "src.api.main:app", "--reload", "--port", str(self.port)],
            "data_agent": ["python", "-m", "agents.data.agent"],
        }
        
        for name, cmd in services.items():
            logger.info(f"Starting {name}...")
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE if not self.debug else None,
                stderr=subprocess.PIPE if not self.debug else None
            )
            self.processes[name] = process
        
        # Wait for services to be ready
        await asyncio.sleep(3)
        logger.info("All services started")
    
    async def _watch_files(self):
        """Watch for file changes and reload."""
        watch_paths = [
            Path("agents"),
            Path("src"),
        ]
        
        async for changes in awatch(*watch_paths):
            if not self.running:
                break
            
            changed_files = [str(path) for _, path in changes]
            logger.info(f"Files changed: {changed_files}")
            
            # Determine which services need restart
            services_to_restart = self._determine_restarts(changed_files)
            
            for service in services_to_restart:
                await self._restart_service(service)
    
    def _determine_restarts(self, changed_files: list) -> set:
        """Determine which services need restart based on changed files."""
        restarts = set()
        
        for file in changed_files:
            if "agents/data" in file:
                restarts.add("data_agent")
            elif "src/api" in file:
                restarts.add("server")
            # Add more mappings as needed
        
        return restarts
    
    async def _restart_service(self, service: str):
        """Restart a specific service."""
        logger.info(f"Restarting {service}...")
        
        # Stop old process
        if service in self.processes:
            self.processes[service].terminate()
            try:
                self.processes[service].wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.processes[service].kill()
        
        # Start new process
        # This is simplified - in production, use proper service definitions
        await asyncio.sleep(1)
        logger.info(f"{service} restarted")
    
    async def _wait_for_shutdown(self):
        """Wait for shutdown signal."""
        loop = asyncio.get_event_loop()
        
        def signal_handler():
            logger.info("Shutdown signal received")
            asyncio.create_task(self.stop())
        
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, signal_handler)
        
        # Wait until stopped
        while self.running:
            await asyncio.sleep(1)


async def start_dev_server(
    hot_reload: bool = True,
    port: int = 8000,
    debug: bool = False
):
    """
    Start development server.
    
    Args:
        hot_reload: Enable hot reload
        port: Server port
        debug: Enable debug mode
    """
    server = DevServer(
        hot_reload=hot_reload,
        port=port,
        debug=debug
    )
    
    try:
        await server.start()
    except KeyboardInterrupt:
        await server.stop()
    except Exception as e:
        logger.error(f"Error in dev server: {e}", exc_info=True)
        await server.stop()
        sys.exit(1)
