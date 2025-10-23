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

    # Check pytest
    result = subprocess.run(
        'python3 -m pytest --version',
        shell=True,
        capture_output=True,
        text=True
    )

    pytest_installed = result.returncode == 0

    if pytest_installed:
        print_success("pytest is available")
    else:
        print_error("pytest is not installed")

    # Check pytest-cov (optional)
    result_cov = subprocess.run(
        'python3 -c "import pytest_cov" 2>/dev/null',
        shell=True,
        capture_output=True,
        text=True
    )

    if result_cov.returncode == 0:
        print_success("pytest-cov is available")
    else:
        print_info("pytest-cov is not installed (optional for coverage)")

    return pytest_installed


def install_dependencies(with_coverage=False):
    """Install pytest and optionally pytest-cov"""
    print_section("Installing Test Dependencies", Colors.OKCYAN)

    packages = ['pytest']
    if with_coverage:
        packages.append('pytest-cov')

    cmd = f"python3 -m pip install {' '.join(packages)}"
    print_info(f"Installing {', '.join(packages)}...")

    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        print_success(f"Successfully installed {', '.join(packages)}")
        return True
    else:
        print_error("Failed to install dependencies")
        print_info("You may need to install manually:")
        print_info(f"  pip install {' '.join(packages)}")
        if result.stderr:
            print_info(f"Error: {result.stderr.strip()}")
        return False


def run_tests(with_coverage=False, verbose=False, test_path=None, auto_install=True):
    """Run the test suite"""
    print_banner("🧪 DOXYGEN COMMENT GENERATOR TEST SUITE 🧪", Colors.HEADER)

    # Check dependencies
    if not check_dependencies():
        if auto_install:
            print_info("\nAttempting to install missing dependencies...")
            if not install_dependencies(with_coverage=with_coverage):
                print_error("\nFailed to install dependencies automatically.")
                print_info("Please install manually: pip install pytest pytest-cov")
                return False
            print()
        else:
            print_error("\nMissing required dependencies.")
            print_info("Install with: pip install pytest pytest-cov")
            print_info("Or run with --install-deps flag")
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
  %(prog)s                    # Run all tests (auto-installs pytest if missing)
  %(prog)s --coverage         # Run tests with coverage report
  %(prog)s -c -v              # Run with coverage and verbose output
  %(prog)s tests/test_generator.py  # Run specific test file
  %(prog)s --install-deps     # Install dependencies and exit
  %(prog)s --no-auto-install  # Don't auto-install if pytest is missing

Note: The script will automatically install pytest if it's not found, unless
      the --no-auto-install flag is used.
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
        help='Install test dependencies and exit (pytest, pytest-cov)'
    )

    parser.add_argument(
        '--no-auto-install',
        action='store_true',
        help='Do not automatically install missing dependencies'
    )

    args = parser.parse_args()

    # Change to project root directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    import os
    os.chdir(project_root)

    # Install dependencies if requested and exit
    if args.install_deps:
        if install_dependencies(with_coverage=True):
            return 0
        else:
            return 1

    # Run tests
    success = run_tests(
        with_coverage=args.coverage,
        verbose=args.verbose,
        test_path=args.test_path,
        auto_install=not args.no_auto_install
    )

    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
