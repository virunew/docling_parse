#!/usr/bin/env python3
"""
Test Runner Script

This script runs all the tests in the project and reports the results.
It can run unit tests, integration tests, or both.
"""

import os
import sys
import argparse
import subprocess
import time
from pathlib import Path

def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Run tests for the docling parser project.")
    
    parser.add_argument(
        "--unit", "-u",
        action="store_true",
        help="Run only unit tests"
    )
    
    parser.add_argument(
        "--integration", "-i",
        action="store_true",
        help="Run only integration tests"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Increase verbosity of output"
    )
    
    parser.add_argument(
        "--coverage", "-c",
        action="store_true",
        help="Run tests with coverage report"
    )

    parser.add_argument(
        "--test", "-t",
        help="Run a specific test file or test class"
    )
    
    args = parser.parse_args()
    
    # If neither unit nor integration is specified, run both
    if not args.unit and not args.integration:
        args.unit = True
        args.integration = True
    
    return args

def get_test_files():
    """Get all test files in the project."""
    # Get all test files in the tests directory
    tests_dir = Path("tests")
    unit_tests = list(tests_dir.glob("test_*.py"))
    
    # Get integration tests (files that start with integration_)
    integration_tests = list(tests_dir.glob("integration_*.py"))
    
    return {
        "unit": unit_tests,
        "integration": integration_tests
    }

def run_tests(args):
    """Run the specified tests and return success/failure."""
    test_files = get_test_files()
    
    # Build the command
    cmd = [sys.executable, "-m", "pytest"]
    
    # Add verbosity flag
    if args.verbose:
        cmd.append("-v")
    
    # Add coverage if requested
    if args.coverage:
        cmd.extend(["--cov=src", "--cov-report=term-missing"])
    
    # Handle specific test request
    if args.test:
        # Check if it's a path or a test class
        if "/" in args.test or "\\" in args.test:
            # It's a path
            cmd.append(args.test)
        else:
            # It's a test name
            cmd.append(f"tests/test_{args.test}.py")
        
        print(f"Running test: {args.test}")
        result = subprocess.run(cmd)
        return result.returncode == 0
    
    # Otherwise run selected test types
    success = True
    
    if args.unit and test_files["unit"]:
        print("\n=== Running Unit Tests ===\n")
        unit_cmd = cmd + [str(f) for f in test_files["unit"]]
        result = subprocess.run(unit_cmd)
        success = success and result.returncode == 0
    
    if args.integration and test_files["integration"]:
        print("\n=== Running Integration Tests ===\n")
        int_cmd = cmd + [str(f) for f in test_files["integration"]]
        result = subprocess.run(int_cmd)
        success = success and result.returncode == 0
    
    return success

def main():
    """Main function."""
    start_time = time.time()
    
    # Parse command-line arguments
    args = parse_arguments()
    
    # Run the tests
    success = run_tests(args)
    
    # Print summary
    elapsed_time = time.time() - start_time
    print(f"\nTest run completed in {elapsed_time:.2f} seconds.")
    
    if success:
        print("All tests passed! 🎉")
        return 0
    else:
        print("Some tests failed. 😢")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 