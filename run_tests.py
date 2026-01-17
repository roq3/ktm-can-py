#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
"""
Test runner script for ktm-can-py project.

This script provides a convenient way to run tests with various options
including coverage reporting, linting, and different test configurations.
"""

import argparse
import subprocess
import sys
import os
from pathlib import Path

def get_python_executable():
    """Get the path to the Python executable to use."""
    # Try to find virtualenv python in parent directory first
    parent_venv_python = PROJECT_ROOT.parent / '.venv' / 'bin' / 'python'
    if parent_venv_python.exists():
        return str(parent_venv_python)

    # Try to find virtualenv python in project directory
    venv_python = PROJECT_ROOT / '.venv' / 'bin' / 'python'
    if venv_python.exists():
        return str(venv_python)

    # Try to find .env python (alternative name)
    env_python = PROJECT_ROOT / '.env' / 'bin' / 'python'
    if env_python.exists():
        return str(env_python)

    # Fall back to system python3
    return 'python3'

def run_command(cmd, description):
    """Run a command and return True if successful."""
    print(f"\n{'='*50}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print('='*50)

    try:
        result = subprocess.run(cmd, cwd=PROJECT_ROOT)
        return result.returncode == 0
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        return False
    except Exception as e:
        print(f"Error running command: {e}")
        return False

def main():
    global PROJECT_ROOT
    PROJECT_ROOT = Path(__file__).parent

    python_exe = get_python_executable()
    parser = argparse.ArgumentParser(description='Run tests for ktm-can-py project')
    parser.add_argument('--coverage', '-c', action='store_true',
                       help='Run tests with coverage report')
    parser.add_argument('--lint', '-l', action='store_true',
                       help='Run linting checks')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    parser.add_argument('--quick', '-q', action='store_true',
                       help='Run only basic tests (no coverage, no lint)')
    parser.add_argument('--all', '-a', action='store_true',
                       help='Run all checks (tests + coverage + lint + type checking)')

    args = parser.parse_args()

    # Determine what to run
    run_tests = True
    run_coverage = args.coverage or args.all
    run_lint = args.lint or args.all
    run_type_check = args.all

    if args.quick:
        run_coverage = False
        run_lint = False

    success = True

    # Run tests
    if run_tests:
        cmd = [python_exe, '-m', 'pytest', 'tests/']
        if args.verbose:
            cmd.append('-v')
        if not run_command(cmd, "Running tests"):
            success = False

    # Run coverage
    if run_coverage and success:
        cmd = [python_exe, '-m', 'pytest', 'tests/', '--cov=ktm_can', '--cov-report=term-missing']
        if args.verbose:
            cmd.append('-v')
        if not run_command(cmd, "Running tests with coverage"):
            success = False

    # Run linting
    if run_lint:
        cmd = [python_exe, '-m', 'flake8', 'src/', 'tests/']
        if not run_command(cmd, "Running linting checks"):
            success = False

    # Run type checking
    if run_type_check:
        cmd = [python_exe, '-m', 'mypy', 'src/']
        if not run_command(cmd, "Running type checking"):
            success = False

    # Summary
    print(f"\n{'='*50}")
    if success:
        print("✅ All checks passed!")
    else:
        print("❌ Some checks failed!")
        sys.exit(1)

if __name__ == '__main__':
    # Get project root directory
    PROJECT_ROOT = Path(__file__).parent

    main()