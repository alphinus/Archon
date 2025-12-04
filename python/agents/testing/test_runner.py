"""
Test Runner and Reporter for Archon

Automated test execution with comprehensive reporting.
Integrates with pytest and provides custom test orchestration.
"""

import subprocess
import json
import asyncio
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class TestRunner:
    """
    Automated test runner for Archon test suites.
    
    Features:
    - Parallel test execution
    - Coverage reporting
    - Test result aggregation
    - Flaky test retry
    - Custom test filtering
    - Integration with CI/CD
    
    Example:
        runner = TestRunner()
        results = await runner.run_tests(
            suites=["memory", "events"],
            coverage=True,
            parallel=True
        )
    """
    
    def __init__(self, base_path: Optional[Path] = None):
        """
        Initialize test runner.
        
        Args:
            base_path: Base directory for tests (defaults to current directory)
        """
        self.base_path = base_path or Path.cwd()
        self.results_dir = self.base_path / "test-results"
        self.results_dir.mkdir(exist_ok=True)
    
    async def run_tests(
        self,
        suites: Optional[List[str]] = None,
        coverage: bool = True,
        parallel: bool = False,
        markers: Optional[str] = None,
        verbose: bool = True,
        retry_flaky: bool = True
    ) -> Dict[str, Any]:
        """
        Run test suites.
        
        Args:
            suites: List of test suites (None for all)
            coverage: Generate coverage report
            parallel: Run tests in parallel
            markers: Pytest markers for filtering
            verbose: Verbose output
            retry_flaky: Retry flaky tests
        
        Returns:
            Test results with statistics
        
        Example:
            results = await runner.run_tests(
                suites=["memory", "events"],
                coverage=True,
                parallel=True
            )
        """
        logger.info(f"Running tests: suites={suites}, coverage={coverage}")
        
        # Build pytest command
        cmd = ["pytest"]
        
        # Add test paths
        if suites:
            for suite in suites:
                test_path = self.base_path / "tests" / f"test_{suite}.py"
                if test_path.exists():
                    cmd.append(str(test_path))
        else:
            cmd.append(str(self.base_path / "tests"))
        
        # Add options
        if verbose:
            cmd.append("-v")
        
        if coverage:
            cmd.extend([
                "--cov=src",
                "--cov=agents",
                "--cov-report=term-missing",
                "--cov-report=json",
                "--cov-report=html"
            ])
        
        if parallel:
            import os
            cpu_count = os.cpu_count() or 4
            cmd.extend(["-n", str(cpu_count)])
        
        if markers:
            cmd.extend(["-m", markers])
        
        if retry_flaky:
            cmd.extend(["--reruns", "2", "--reruns-delay", "1"])
        
        # Add JSON report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.results_dir / f"test-report-{timestamp}.json"
        cmd.extend(["--json-report", f"--json-report-file={report_file}"])
        
        # Run tests
        start_time = datetime.now()
        
        try:
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.base_path
            )
            
            stdout, stderr = await result.communicate()
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Parse results
            if report_file.exists():
                with open(report_file) as f:
                    test_data = json.load(f)
                
                summary = test_data.get("summary", {})
                
                return {
                    "status": "success" if result.returncode == 0 else "failed",
                    "total": summary.get("total", 0),
                    "passed": summary.get("passed", 0),
                    "failed": summary.get("failed", 0),
                    "skipped": summary.get("skipped", 0),
                    "errors": summary.get("error", 0),
                    "duration_seconds": duration,
                    "coverage": self._parse_coverage() if coverage else None,
                    "report_path": str(report_file),
                    "timestamp": start_time.isoformat()
                }
            else:
                # Fallback to stdout parsing
                return self._parse_stdout_results(stdout.decode(), duration, start_time)
                
        except Exception as e:
            logger.error(f"Test execution failed: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "timestamp": start_time.isoformat()
            }
    
    async def run_specific_tests(
        self,
        test_paths: List[str],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Run specific test files or functions.
        
        Args:
            test_paths: List of test paths (file::function format)
            **kwargs: Additional options
        
        Returns:
            Test results
        """
        logger.info(f"Running specific tests: {test_paths}")
        
        cmd = ["pytest"] + test_paths
        
        # Add common options
        if kwargs.get("verbose", True):
            cmd.append("-v")
        
        # Execute
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=self.base_path
        )
        
        return {
            "status": "success" if result.returncode == 0 else "failed",
            "output": result.stdout,
            "test_paths": test_paths
        }
    
    def _parse_coverage(self) -> Optional[Dict[str, Any]]:
        """Parse coverage from JSON report."""
        coverage_file = self.base_path / "coverage.json"
        
        if coverage_file.exists():
            with open(coverage_file) as f:
                cov_data = json.load(f)
            
            totals = cov_data.get("totals", {})
            
            return {
                "percent_covered": totals.get("percent_covered", 0),
                "lines_covered": totals.get("covered_lines", 0),
                "lines_total": totals.get("num_statements", 0),
                "missing_lines": totals.get("missing_lines", 0)
            }
        
        return None
    
    def _parse_stdout_results(
        self,
        output: str,
        duration: float,
        timestamp: datetime
    ) -> Dict[str, Any]:
        """Parse test results from stdout."""
        import re
        
        # Try to extract test counts
        passed_match = re.search(r"(\d+) passed", output)
        failed_match = re.search(r"(\d+) failed", output)
        skipped_match = re.search(r"(\d+) skipped", output)
        
        passed = int(passed_match.group(1)) if passed_match else 0
        failed = int(failed_match.group(1)) if failed_match else 0
        skipped = int(skipped_match.group(1)) if skipped_match else 0
        
        return {
            "status": "success" if failed == 0 else "failed",
            "total": passed + failed + skipped,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "duration_seconds": duration,
            "timestamp": timestamp.isoformat(),
            "output": output
        }


class TestReporter:
    """
    Generates comprehensive test reports.
    
    Supports multiple formats:
    - HTML dashboards
    - JSON for CI/CD
    - Markdown summaries
    """
    
    def __init__(self, results_dir: Optional[Path] = None):
        """Initialize reporter."""
        self.results_dir = results_dir or Path.cwd() / "test-results"
    
    def generate_report(
        self,
        test_results: Dict[str, Any],
        format: str = "html"
    ) -> str:
        """
        Generate test report.
        
        Args:
            test_results: Test results dictionary
            format: Report format (html, json, markdown)
        
        Returns:
            Path to generated report
        """
        generators = {
            "html": self._generate_html_report,
            "json": self._generate_json_report,
            "markdown": self._generate_markdown_report
        }
        
        if format not in generators:
            raise ValueError(f"Unknown format: {format}")
        
        return generators[format](test_results)
    
    def _generate_html_report(self, results: Dict[str, Any]) -> str:
        """Generate HTML dashboard."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = self.results_dir / f"test-report-{timestamp}.html"
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Archon Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .summary {{ background: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .passed {{ color: green; }}
        .failed {{ color: red; }}
        .stats {{ display: flex; gap: 20px; margin-top: 20px; }}
        .stat {{ background: white; padding: 15px; border-radius: 5px; }}
    </style>
</head>
<body>
    <h1>Archon Test Report</h1>
    <div class="summary">
        <h2>Summary</h2>
        <div class="stats">
            <div class="stat">
                <h3>Total Tests</h3>
                <p>{results.get('total', 0)}</p>
            </div>
            <div class="stat passed">
                <h3>Passed</h3>
                <p>{results.get('passed', 0)}</p>
            </div>
            <div class="stat failed">
                <h3>Failed</h3>
                <p>{results.get('failed', 0)}</p>
            </div>
            <div class="stat">
                <h3>Coverage</h3>
                <p>{results.get('coverage', {}).get('percent_covered', 0):.1f}%</p>
            </div>
        </div>
        <p>Duration: {results.get('duration_seconds', 0):.2f}s</p>
        <p>Timestamp: {results.get('timestamp', '')}</p>
    </div>
</body>
</html>
"""
        
        report_path.write_text(html_content)
        logger.info(f"HTML report generated: {report_path}")
        
        return str(report_path)
    
    def _generate_json_report(self, results: Dict[str, Any]) -> str:
        """Generate JSON report for CI/CD."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = self.results_dir / f"test-report-{timestamp}.json"
        
        with open(report_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"JSON report generated: {report_path}")
        
        return str(report_path)
    
    def _generate_markdown_report(self, results: Dict[str, Any]) -> str:
        """Generate Markdown summary."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = self.results_dir / f"test-report-{timestamp}.md"
        
        markdown = f"""# Archon Test Report

## Summary

- **Total Tests**: {results.get('total', 0)}
- **Passed**: ✅ {results.get('passed', 0)}
- **Failed**: ❌ {results.get('failed', 0)}
- **Skipped**: ⏭️ {results.get('skipped', 0)}
- **Duration**: {results.get('duration_seconds', 0):.2f}s

## Coverage

- **Coverage**: {results.get('coverage', {}).get('percent_covered', 0):.1f}%
- **Lines Covered**: {results.get('coverage', {}).get('lines_covered', 0)}
- **Total Lines**: {results.get('coverage', {}).get('lines_total', 0)}

## Status

{':white_check_mark: All tests passed!' if results.get('status') == 'success' else ':x: Some tests failed'}

*Generated: {results.get('timestamp', '')}*
"""
        
        report_path.write_text(markdown)
        logger.info(f"Markdown report generated: {report_path}")
        
        return str(report_path)
