#!/usr/bin/env python3
"""
PR Safety Check Script

This script provides automated checks to verify if it's safe to delete specific PRs.
It analyzes the codebase for dependencies, references, and potential impacts.
"""

import os
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Dict


def find_pr_references(root_dir: str, pr_numbers: List[int]) -> Dict[int, List[str]]:
    """
    Search for references to specific PR numbers in the codebase.
    
    Args:
        root_dir: Root directory to search
        pr_numbers: List of PR numbers to search for
        
    Returns:
        Dictionary mapping PR number to list of files containing references
    """
    references = {pr: [] for pr in pr_numbers}
    
    # Patterns to match PR references
    patterns = [
        r'#(\d+)',  # GitHub style #123
        r'PR\s*(\d+)',  # PR 123
        r'pull\s*request\s*(\d+)',  # pull request 123
    ]
    
    # File extensions to search
    extensions = {'.py', '.md', '.yml', '.yaml', '.json', '.txt', '.rst'}
    
    for file_path in Path(root_dir).rglob('*'):
        if file_path.is_file() and file_path.suffix.lower() in extensions:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                for pattern in patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        pr_num = int(match.group(1))
                        if pr_num in pr_numbers:
                            relative_path = os.path.relpath(file_path, root_dir)
                            references[pr_num].append(relative_path)
                            
            except (IOError, ValueError, UnicodeDecodeError):
                continue
                
    return references


def check_git_history(pr_numbers: List[int]) -> Dict[int, List[str]]:
    """
    Check git history for references to PR numbers.
    
    Args:
        pr_numbers: List of PR numbers to search for
        
    Returns:
        Dictionary mapping PR number to list of commits containing references
    """
    references = {pr: [] for pr in pr_numbers}
    
    try:
        # Get all commit messages
        result = subprocess.run(
            ['git', 'log', '--all', '--oneline'],
            capture_output=True, text=True, timeout=30
        )
        
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if line.strip():
                    for pr_num in pr_numbers:
                        patterns = [f'#{pr_num}', f'PR {pr_num}', f'pull request {pr_num}']
                        if any(pattern.lower() in line.lower() for pattern in patterns):
                            references[pr_num].append(line.strip())
                            
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
        pass
        
    return references


def run_tests() -> bool:
    """
    Run the test suite to ensure current functionality is working.
    
    Returns:
        True if all tests pass, False otherwise
    """
    try:
        result = subprocess.run(
            ['python', '-m', 'pytest', 'tests/', '-v'],
            capture_output=True, text=True, timeout=180
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
        return False


def generate_safety_report(pr_numbers: List[int], root_dir: str = '.') -> str:
    """
    Generate a comprehensive safety report for PR deletion.
    
    Args:
        pr_numbers: List of PR numbers to analyze
        root_dir: Root directory of the repository
        
    Returns:
        Formatted safety report as string
    """
    report = []
    report.append(f"PR Deletion Safety Report")
    report.append(f"=" * 40)
    report.append(f"Analyzing PRs: {', '.join(f'#{pr}' for pr in pr_numbers)}")
    report.append("")
    
    # Check code references
    report.append("🔍 CODE REFERENCES:")
    code_refs = find_pr_references(root_dir, pr_numbers)
    found_code_refs = False
    for pr_num, files in code_refs.items():
        if files:
            found_code_refs = True
            report.append(f"  PR #{pr_num}: Found in {len(files)} files")
            for file_path in files[:5]:  # Show max 5 files
                report.append(f"    - {file_path}")
            if len(files) > 5:
                report.append(f"    ... and {len(files) - 5} more files")
        else:
            report.append(f"  PR #{pr_num}: No references found ✅")
    
    report.append("")
    
    # Check git history
    report.append("📝 GIT HISTORY:")
    git_refs = check_git_history(pr_numbers)
    found_git_refs = False
    for pr_num, commits in git_refs.items():
        if commits:
            found_git_refs = True
            report.append(f"  PR #{pr_num}: Found in {len(commits)} commits")
            for commit in commits[:3]:  # Show max 3 commits
                report.append(f"    - {commit}")
            if len(commits) > 3:
                report.append(f"    ... and {len(commits) - 3} more commits")
        else:
            report.append(f"  PR #{pr_num}: No git references found ✅")
    
    report.append("")
    
    # Run tests
    report.append("🧪 TEST SUITE:")
    tests_pass = run_tests()
    if tests_pass:
        report.append("  All tests passing ✅")
    else:
        report.append("  Some tests failing ❌")
    
    report.append("")
    
    # Safety assessment
    report.append("⚖️  SAFETY ASSESSMENT:")
    risk_score = 0
    if found_code_refs:
        risk_score += 3
        report.append("  HIGH RISK: Code references found ❌")
    if found_git_refs:
        risk_score += 2
        report.append("  MEDIUM RISK: Git history references found ⚠️")
    if not tests_pass:
        risk_score += 2
        report.append("  MEDIUM RISK: Tests failing ❌")
    
    if risk_score == 0:
        report.append("  SAFE TO DELETE: No dependencies found ✅")
    elif risk_score <= 2:
        report.append("  EXERCISE CAUTION: Low risk dependencies found ⚠️")
    else:
        report.append("  NOT SAFE TO DELETE: High risk dependencies found ❌")
    
    report.append("")
    report.append("📋 RECOMMENDATIONS:")
    if risk_score == 0:
        report.append("  - PRs can be safely deleted")
        report.append("  - Consider archiving any valuable discussions first")
    elif risk_score <= 2:
        report.append("  - Review found references before deleting")
        report.append("  - Ensure references are not critical")
        report.append("  - Consider updating documentation")
    else:
        report.append("  - DO NOT DELETE these PRs")
        report.append("  - Found dependencies that may break functionality")
        report.append("  - Investigate and resolve dependencies first")
    
    return "\n".join(report)


def main():
    """Main entry point for the PR safety check script."""
    if len(sys.argv) < 2:
        print("Usage: python pr_safety_check.py <PR_NUMBER> [PR_NUMBER ...]")
        print("Example: python pr_safety_check.py 6 7")
        sys.exit(1)
    
    try:
        pr_numbers = [int(arg) for arg in sys.argv[1:]]
    except ValueError:
        print("Error: All arguments must be valid PR numbers")
        sys.exit(1)
    
    # Change to repository root if script is run from scripts directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if script_dir.endswith('scripts'):
        os.chdir(os.path.dirname(script_dir))
    
    report = generate_safety_report(pr_numbers)
    print(report)


if __name__ == "__main__":
    main()