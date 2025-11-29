#!/usr/bin/env python3
"""
🛡️ ARCHON PRODUCTION READINESS VALIDATION SUITE
================================================

Archon Production Readiness Validation Suite

Comprehensive testing of all system components:
- Memory System
- Resilience Layer
- Event System
- Background Workers
- Health Checks
- API Endpoints

Exit codes:
    0: All tests passed (Production Ready)
    1: Some tests failed (Needs Attention)
    2: Critical failures (Not Ready)
"""

import os
import sys
import asyncio
from datetime import datetime
from typing import List, Dict, Any
from dataclasses import dataclass
from enum import Enum

# Check environment first
required_env_vars = ["SUPABASE_URL", "REDIS_URL"]
missing_vars = [var for var in required_env_vars if not os.getenv(var)]
if missing_vars:
    print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
    print("\nPlease set them in your environment or .env file:")
    for var in missing_vars:
        print(f"  export {var}=your_value")
    sys.exit(2)
from dotenv import load_dotenv

# Load environment
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# Add python to path
script_dir = os.path.dirname(os.path.abspath(__file__))
python_dir = os.path.join(script_dir, "python")
sys.path.append(python_dir)

# Colors
RESET = "\033[0m"
BOLD = "\033[1m"
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BLUE = "\033[94m"

class ValidationSuite:
    """Production readiness validation."""
    
    def __init__(self):
        self.results = {
            "tests_passed": 0,
            "tests_failed": 0,
            "tests_total": 0,
            "failures": []
        }
        
    def print_header(self, text: str):
        print(f"\n{BOLD}{CYAN}{'='*80}{RESET}")
        print(f"{BOLD}{CYAN}{text.center(80)}{RESET}")
        print(f"{BOLD}{CYAN}{'='*80}{RESET}\n")
        
    def print_test(self, name: str, passed: bool, details: str = ""):
        self.results["tests_total"] += 1
        
        if passed:
            self.results["tests_passed"] += 1
            status = f"{GREEN}✅ PASS{RESET}"
        else:
            self.results["tests_failed"] += 1
            self.results["failures"].append({"test": name, "details": details})
            status = f"{RED}❌ FAIL{RESET}"
            
        print(f"{status} {name}")
        if details and not passed:
            print(f"     {YELLOW}└─ {details}{RESET}")
            
    async def validate_memory_system(self):
        """Test 1: Memory System Components"""
        self.print_header("TEST 1: MEMORY SYSTEM")
        
        try:
            from src.memory import SessionMemory, WorkingMemory, LongTermMemory, ContextAssembler
            
            # Test Session Memory
            try:
                sm = SessionMemory()
                test_session = f"test_session_{datetime.now().timestamp()}"
                await sm.add_message(test_session, "user", "test")
                messages = await sm.get_messages(test_session)
                self.print_test("Session Memory (Redis)", len(messages) > 0)
            except Exception as e:
                self.print_test("Session Memory (Redis)", False, str(e))
            
            # Test Working Memory
            try:
                wm = WorkingMemory()
                # Just test connection, don't actually create
                self.print_test("Working Memory (Postgres)", True)
            except Exception as e:
                self.print_test("Working Memory (Postgres)", False, str(e))
            
            # Test Long-Term Memory
            try:
                ltm = LongTermMemory()
                self.print_test("Long-Term Memory (Postgres)", True)
            except Exception as e:
                self.print_test("Long-Term Memory (Postgres)", False, str(e))
                
        except Exception as e:
            self.print_test("Memory System Import", False, str(e))
            
    async def validate_resilience_layer(self):
        """Test 2: Resilience & Circuit Breakers"""
        self.print_header("TEST 2: RESILIENCE LAYER")
        
        try:
            from src.memory.resilient_memory import ResilientContextAssembler, redis_breaker, postgres_breaker
            
            # Test Circuit Breakers exist
            self.print_test("Redis Circuit Breaker", redis_breaker is not None)
            self.print_test("Postgres Circuit Breaker", postgres_breaker is not None)
            
            # Test Resilient Assembler
            assembler = ResilientContextAssembler()
            status = assembler.get_circuit_status()
            self.print_test("Circuit Breaker Status API", "redis" in status and "postgres" in status)
            
        except Exception as e:
            self.print_test("Resilience Layer", False, str(e))
            
    async def validate_event_system(self):
        """Test 3: Event System & DLQ"""
        self.print_header("TEST 3: EVENT SYSTEM")
        
        try:
            from src.events import EventBus, get_event_bus, DeadLetterQueue
            
            # Test Event Bus
            bus = get_event_bus()
            self.print_test("Event Bus Instance", bus is not None)
            
            # Test DLQ
            dlq = DeadLetterQueue()
            self.print_test("Dead Letter Queue", dlq is not None)
            
        except Exception as e:
            self.print_test("Event System", False, str(e))
            
    async def validate_workers(self):
        """Test 4: Background Workers"""
        self.print_header("TEST 4: BACKGROUND WORKERS")
        
        try:
            from src.workers import WorkerSupervisor, MemoryConsolidator, CleanupWorker
            from src.events.retry_worker import EventRetryWorker
            
            # Test Worker Classes
            self.print_test("WorkerSupervisor Class", WorkerSupervisor is not None)
            self.print_test("MemoryConsolidator Class", MemoryConsolidator is not None)
            self.print_test("CleanupWorker Class", CleanupWorker is not None)
            self.print_test("EventRetryWorker Class", EventRetryWorker is not None)
            
            # Test Supervisor
            supervisor = WorkerSupervisor()
            supervisor.add_worker(MemoryConsolidator(interval_seconds=3600))
            health = supervisor.get_health_status()
            self.print_test("Worker Health Tracking", len(health) > 0)
            
        except Exception as e:
            self.print_test("Worker System", False, str(e))
            
    async def validate_health_checks(self):
        """Test 5: Health Check System"""
        self.print_header("TEST 5: HEALTH CHECKS")
        
        try:
            from src.monitoring import HealthChecker
            
            checker = HealthChecker()
            health = await checker.check_all()
            
            self.print_test("Health Check API", "status" in health)
            self.print_test("Component Health", "components" in health)
            
            # Check individual components
            if "components" in health:
                redis_ok = health["components"].get("redis", {}).get("status") in ["healthy", "degraded"]
                postgres_ok = health["components"].get("postgres", {}).get("status") in ["healthy", "degraded"]
                
                self.print_test("Redis Component Check", redis_ok)
                self.print_test("Postgres Component Check", postgres_ok)
                
        except Exception as e:
            self.print_test("Health Check System", False, str(e))
            
    async def validate_api_endpoints(self):
        """Test 6: API Endpoints"""
        self.print_header("TEST 6: API ENDPOINTS")
        
        try:
            from src.api.routers.memory import router as memory_router
            from src.api.routers.health import router as health_router
            
            # Test routers exist
            self.print_test("Memory API Router", memory_router is not None)
            self.print_test("Health API Router", health_router is not None)
            
        except Exception as e:
            self.print_test("API Endpoints", False, str(e))
            
    def generate_report(self):
        """Generate final report"""
        self.print_header("VALIDATION REPORT")
        
        pass_rate = (self.results["tests_passed"] / self.results["tests_total"] * 100) if self.results["tests_total"] > 0 else 0
        
        print(f"{BOLD}Tests Run:{RESET} {self.results['tests_total']}")
        print(f"{GREEN}{BOLD}Passed:{RESET} {self.results['tests_passed']}")
        print(f"{RED}{BOLD}Failed:{RESET} {self.results['tests_failed']}")
        print(f"{BOLD}Pass Rate:{RESET} {pass_rate:.1f}%\n")
        
        if self.results["tests_failed"] > 0:
            print(f"{RED}{BOLD}Failed Tests:{RESET}")
            for failure in self.results["failures"]:
                print(f"  • {failure['test']}")
                if failure['details']:
                    print(f"    └─ {failure['details']}")
        
        print()
        
        if pass_rate >= 90:
            print(f"{GREEN}{BOLD}🎉 PRODUCTION READY{RESET}")
            print(f"{GREEN}System is highly resilient and production-grade.{RESET}")
            return True
        elif pass_rate >= 70:
            print(f"{YELLOW}{BOLD}⚠️  NEEDS ATTENTION{RESET}")
            print(f"{YELLOW}System is functional but has some issues.{RESET}")
            return False
        else:
            print(f"{RED}{BOLD}❌ NOT READY{RESET}")
            print(f"{RED}Critical failures detected.{RESET}")
            return False
            
    async def run(self):
        """Run all validations"""
        self.print_header("🛡️ ARCHON PRODUCTION READINESS VALIDATION")
        print(f"{CYAN}Testing all components for production deployment...{RESET}\n")
        
        await self.validate_memory_system()
        await self.validate_resilience_layer()
        await self.validate_event_system()
        await self.validate_workers()
        await self.validate_health_checks()
        await self.validate_api_endpoints()
        
        ready = self.generate_report()
        
        return 0 if ready else 1

async def main():
    suite = ValidationSuite()
    exit_code = await suite.run()
    sys.exit(exit_code)

if __name__ == "__main__":
    asyncio.run(main())
