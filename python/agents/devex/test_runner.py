"""
Test Runner for Archon

Manages test execution with coverage reporting and result aggregation.
"""

import subprocess
import json
from typing import Dict, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


async def run_tests_cli(
    suite: Optional[str] = None,
    coverage: bool = True,
    verbose: bool = False,
    markers: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run tests via CLI.
    
    Args:
        suite: Specific test suite (e.g., 'memory', 'events')
        coverage: Generate coverage report
        verbose: Verbose output
        markers: Pytest markers
    
    Returns:
        Test results dictionary
    """
    # Build pytest command
    cmd = ["pytest"]
    
    # Add test path
    if suite:
        test_path = Path("tests") / f"test_{suite}.py"
        if test_path.exists():
            cmd.append(str(test_path))
        else:
            # Try as module
            cmd.append(f"tests/{suite}")
    else:
        cmd.append("tests/")
    
    # Add coverage
    if coverage:
        cmd.extend(["--cov=src", "--cov=agents", "--cov-report=term-missing"])
    
    # Add verbose
    if verbose:
        cmd.append("-v")
    
    # Add markers
    if markers:
        cmd.extend(["-m", markers])
    
    # Add JSON output for parsing
    cmd.extend(["--json-report", "--json-report-file=test-results.json"])
    
    logger.info(f"Running: {' '.join(cmd)}")
    
    try:
        # Run tests
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=Path.cwd()
        )
        
        # Parse results
        results_file = Path("test-results.json")
        if results_file.exists():
            with open(results_file) as f:
                test_data = json.load(f)
            
            return {
                "status": "success" if result.returncode == 0 else "failed",
                "total": test_data.get("summary", {}).get("total", 0),
                "passed": test_data.get("summary", {}).get("passed", 0),
                "failed": test_data.get("summary", {}).get("failed", 0),
                "skipped": test_data.get("summary", {}).get("skipped", 0),
                "coverage": _parse_coverage(result.stdout) if coverage else None,
                "duration": test_data.get("duration", 0),
                "output": result.stdout
            }
        else:
            # Fallback parsing from stdout
            return {
                "status": "success" if result.returncode == 0 else "failed",
                "total": _parse_test_count(result.stdout),
                "passed": _parse_passed_count(result.stdout),
                "failed": _parse_failed_count(result.stdout),
                "output": result.stdout
            }
            
    except Exception as e:
        logger.error(f"Error running tests: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "total": 0,
            "passed": 0,
            "failed": 0
        }


def _parse_coverage(output: str) -> Optional[int]:
    """Parse coverage percentage from output."""
    import re
    match = re.search(r"TOTAL\s+\d+\s+\d+\s+(\d+)%", output)
    if match:
        return int(match.group(1))
    return None


def _parse_test_count(output: str) -> int:
    """Parse total test count from output."""
    import re
    match = re.search(r"(\d+) passed", output)
    if match:
        return int(match.group(1))
    return 0


def _parse_passed_count(output: str) -> int:
    """Parse passed test count."""
    import re
    match = re.search(r"(\d+) passed", output)
    return int(match.group(1)) if match else 0


def _parse_failed_count(output: str) -> int:
    """Parse failed test count."""
    import re
    match = re.search(r"(\d+) failed", output)
    return int(match.group(1)) if match else 0
