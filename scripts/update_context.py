#!/usr/bin/env python3
"""
Script to update context files with the current date.
Target files:
- AI_TASKS.md
- .context/current_state.md
- AI_WORK_LOG.md (optional, usually appended to, but we can check last entry)

Usage:
    python scripts/update_context.py [--check]
"""

import os
import re
import sys
from datetime import datetime
import argparse

# Configuration
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILES_TO_UPDATE = [
    {
        "path": "AI_TASKS.md",
        "patterns": [
            (r"(\*\*Last Updated:\*\* )(\d{4}-\d{2}-\d{2})", r"\g<1>{date}"),
            (r"(Last Updated: )(\d{4}-\d{2}-\d{2})", r"\g<1>{date}"),
        ]
    },
    {
        "path": ".context/current_state.md",
        "patterns": [
             (r"(Last Updated: )(\d{4}-\d{2}-\d{2})", r"\g<1>{date}"),
             # Maybe update a header like "## Status (YYYY-MM-DD)"
             (r"(## Status \()(\d{4}-\d{2}-\d{2})(\))", r"\g<1>{date}\g<3>")
        ]
    }
]

def get_current_date():
    return datetime.now().strftime("%Y-%m-%d")

def update_file(file_config, check_only=False):
    file_path = os.path.join(PROJECT_ROOT, file_config["path"])
    if not os.path.exists(file_path):
        print(f"⚠️  File not found: {file_config['path']}")
        return False

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    new_content = content
    current_date = get_current_date()
    changes_made = False

    for pattern, replacement in file_config["patterns"]:
        # Prepare replacement with current date
        repl_str = replacement.format(date=current_date)
        
        # Check if we need to update
        # We use re.subn to count replacements
        new_content, count = re.subn(pattern, repl_str, new_content)
        if count > 0:
            # Check if the content actually changed (i.e., date was different)
            if new_content != content:
                changes_made = True

    if check_only:
        if changes_made:
            print(f"❌ {file_config['path']} is stale.")
            return False
        else:
            print(f"✅ {file_config['path']} is up to date.")
            return True

    if changes_made:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"✅ Updated {file_config['path']}")
    else:
        print(f"zk {file_config['path']} already up to date.")
    
    return True

def main():
    parser = argparse.ArgumentParser(description="Update AI context files timestamps.")
    parser.add_argument("--check", action="store_true", help="Only check if files are up to date, don't write.")
    args = parser.parse_args()

    all_ok = True
    for config in FILES_TO_UPDATE:
        if not update_file(config, check_only=args.check):
            all_ok = False
    
    if args.check and not all_ok:
        sys.exit(1)

if __name__ == "__main__":
    main()
