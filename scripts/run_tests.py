#!/usr/bin/env python3
"""
Test Runner Script for Doxygen Comment Generator
Runs tests with optional coverage reporting and attractive output formatting.
"""

import sys
import subprocess
import argparse
from pathlib import Path


class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_banner(text, color=Colors.OKBLUE):
    """Print a formatted banner"""
    width = 70
    print(f"\n{color}{'=' * width}")
    print(f"{text.center(width)}")
    print(f"{'=' * width}{Colors.ENDC}\n")


def print_section(text, color=Colors.OKCYAN):
    """Print a section header"""
    print(f"\n{color}{Colors.BOLD}▶ {text}{Colors.ENDC}")
    print(f"{color}{'─' * 70}{Colors.ENDC}")


def print_success(text):
    """Print success message"""
    print(f"{Colors.OKGREEN}✓{Colors.ENDC} {text}")


def print_error(text):
    """Print error message"""
    print(f"{Colors.FAIL}✗{Colors.ENDC} {text}")


def print_info(text):
    """Print info message"""
    print(f"{Colors.OKCYAN}ℹ{Colors.ENDC} {text}")


def run_command(cmd, description):
    """Run a shell command and return the result"""
    print_info(f"{description}...")
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            check=True,
            capture_output=False,
            text=True
        )
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        return False


def check_dependencies():
    """Check if required dependencies are installed"""
    print_section("Checking Dependencies", Colors.OKCYAN)

    dependencies = {
        'pytest': 'pytest --version',
        'pytest-cov': 'pytest --co -q 2>&1 | grep -q "pytest-cov" || echo "not_critical"'
    }

    all_installed = True
    for dep, check_cmd in dependencies.items():
        result = subprocess.run(
            check_cmd,
            shell=True,
            capture_output=True,
            text=True
        )
        if result.returncode == 0 or 'not_critical' in result.stdout:
            print_success(f"{dep} is available")
        else:
            print_error(f"{dep} is not installed")
            if dep == 'pytest':
                all_installed = False
            else:
                print_info(f"  Install with: pip install {dep}")

    return all_installed


def run_tests(with_coverage=False, verbose=False, test_path=None):
    """Run the test suite"""
    print_banner("🧪 DOXYGEN COMMENT GENERATOR TEST SUITE 🧪", Colors.HEADER)

    # Check dependencies
    if not check_dependencies():
        print_error("\nMissing required dependencies. Please install pytest first.")
        print_info("Install with: pip install pytest pytest-cov")
        return False

    # Build pytest command
    cmd_parts = ['python3', '-m', 'pytest']

    # Add test path if specified
    if test_path:
        cmd_parts.append(test_path)
    else:
        cmd_parts.append('tests/')

    # Add verbosity
    if verbose:
        cmd_parts.append('-v')
    else:
        cmd_parts.append('-v')  # Always use verbose for better output

    # Add coverage options
    if with_coverage:
        print_section("Running Tests with Coverage", Colors.OKBLUE)
        cmd_parts.extend([
            '--cov=src',
            '--cov-report=term-missing',
            '--cov-report=html:htmlcov',
            '--cov-branch'
        ])
    else:
        print_section("Running Tests", Colors.OKBLUE)

    # Add color output
    cmd_parts.append('--color=yes')

    # Build final command
    cmd = ' '.join(cmd_parts)

    # Run tests
    print_info(f"Command: {cmd}\n")
    result = subprocess.run(cmd, shell=True)

    # Print results
    print_section("Test Results", Colors.OKBLUE)

    if result.returncode == 0:
        print_success("All tests passed! ✨")
        if with_coverage:
            print_info("Coverage report generated in: htmlcov/index.html")
            print_info("View coverage: open htmlcov/index.html")
        print_banner("SUCCESS", Colors.OKGREEN)
        return True
    else:
        print_error("Some tests failed")
        print_banner("FAILED", Colors.FAIL)
        return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Run tests for Doxygen Comment Generator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Run all tests
  %(prog)s --coverage         # Run tests with coverage report
  %(prog)s -c -v              # Run with coverage and verbose output
  %(prog)s tests/test_generator.py  # Run specific test file
        """
    )

    parser.add_argument(
        '-c', '--coverage',
        action='store_true',
        help='Run tests with coverage reporting'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose output (show each test)'
    )

    parser.add_argument(
        'test_path',
        nargs='?',
        help='Specific test file or directory to run (default: tests/)'
    )

    parser.add_argument(
        '--install-deps',
        action='store_true',
        help='Install test dependencies (pytest, pytest-cov)'
    )

    args = parser.parse_args()

    # Change to project root directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    import os
    os.chdir(project_root)

    # Install dependencies if requested
    if args.install_deps:
        print_section("Installing Test Dependencies", Colors.OKCYAN)
        cmd = "pip install pytest pytest-cov"
        if run_command(cmd, "Installing pytest and pytest-cov"):
            print_success("Dependencies installed successfully!")
        else:
            print_error("Failed to install dependencies")
            return 1
        print()

    # Run tests
    success = run_tests(
        with_coverage=args.coverage,
        verbose=args.verbose,
        test_path=args.test_path
    )

    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
