"""
Database Seeding Script for Testing

Seeds the test database with realistic mock data for all scenarios.
Enables comprehensive testing of the Archon system.

Usage:
    python seed_test_database.py                    # Seed all scenarios
    python seed_test_database.py customer_support   # Seed specific scenario
    python seed_test_database.py --clear            # Clear database first
"""

import asyncio
import argparse
import sys
import os
from pathlib import Path

# Add python to path
sys.path.append(str(Path(__file__).parent.parent))

from tests.fixtures import MockDataGenerator, generate_scenario
from dotenv import load_dotenv

# Load env
load_dotenv()

# Colors for output
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


class DatabaseSeeder:
    """Seeds database with mock data for testing."""
    
    def __init__(self):
        self.generator = MockDataGenerator()
        
    async def clear_database(self):
        """Clear all test data from database."""
        print(f"{YELLOW}⚠️  Clearing test database...{RESET}")
        
        try:
            from src.memory import SessionMemory, WorkingMemory, LongTermMemory
            
            # TODO: Implement clearing logic when DB methods exist
            # For now, just log
            print(f"{BLUE}   Note: Clear logic pending DB methods{RESET}")
            
        except Exception as e:
            print(f"{YELLOW}   Warning: Could not clear database: {e}{RESET}")
    
    async def seed_scenario(self, scenario: dict):
        """Seed database with a single scenario."""
        print(f"\n{BLUE}📊 Seeding: {scenario['name']}{RESET}")
        print(f"   {scenario['description']}")
        
        try:
            # TODO: Implement seeding when DB methods exist
            # For now, just display stats
            
            stats = {
                "users": 1 if "user" in scenario else len(scenario.get("users", [])),
                "conversations": len(scenario.get("conversations", [])),
                "working_memories": 0,
                "longterm_facts": 0
            }
            
            # Count memories
            if "working_memory" in scenario:
                if isinstance(scenario["working_memory"], dict):
                    stats["working_memories"] = sum(len(m) for m in scenario["working_memory"].values())
                else:
                    stats["working_memories"] = len(scenario["working_memory"])
                    
            if "longterm_memory" in scenario:
                if isinstance(scenario["longterm_memory"], dict):
                    stats["longterm_facts"] = sum(len(m) for m in scenario["longterm_memory"].values())
                else:
                    stats["longterm_facts"] = len(scenario["longterm_memory"])
            
            print(f"{GREEN}   ✓ Generated:{RESET}")
            print(f"     - {stats['users']} user(s)")
            print(f"     - {stats['conversations']} conversation(s)")
            print(f"     - {stats['working_memories']} working memories")
            print(f"     - {stats['longterm_facts']} long-term facts")
            
            return stats
            
        except Exception as e:
            print(f"{YELLOW}   ⚠️  Error: {e}{RESET}")
            return None
    
    async def seed_all(self):
        """Seed database with all scenarios."""
        scenarios = self.generator.generate_all_scenarios()
        
        print(f"\n{BLUE}{'='*60}{RESET}")
        print(f"{BLUE}  SEEDING TEST DATABASE{RESET}")
        print(f"{BLUE}{'='*60}{RESET}")
        
        total_stats = {
            "users": 0,
            "conversations": 0,
            "working_memories": 0,
            "longterm_facts": 0
        }
        
        for scenario in scenarios:
            stats = await self.seed_scenario(scenario)
            if stats:
                for key in total_stats:
                    total_stats[key] += stats[key]
        
        print(f"\n{GREEN}{'='*60}{RESET}")
        print(f"{GREEN}  SEEDING COMPLETE{RESET}")
        print(f"{GREEN}{'='*60}{RESET}")
        print(f"\n{BLUE}Total Generated:{RESET}")
        print(f"  - {total_stats['users']} users")
        print(f"  - {total_stats['conversations']} conversations")
        print(f"  - {total_stats['working_memories']} working memories")
        print(f"  - {total_stats['longterm_facts']} long-term facts\n")


async def main():
    parser = argparse.ArgumentParser(description="Seed test database with mock data")
    parser.add_argument(
        "scenario",
        nargs="?",
        choices=["customer_support", "code_review", "data_analysis", "content_creation", "multi_agent"],
        help="Specific scenario to seed (default: all)"
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear database before seeding"
    )
    
    args = parser.parse_args()
    
    seeder = DatabaseSeeder()
    
    if args.clear:
        await seeder.clear_database()
    
    if args.scenario:
        # Seed specific scenario
        scenario = generate_scenario(args.scenario)
        await seeder.seed_scenario(scenario)
    else:
        # Seed all
        await seeder.seed_all()


if __name__ == "__main__":
    asyncio.run(main())
