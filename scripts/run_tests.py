#!/usr/bin/env python3
"""
Test Runner Script for Doxygen Comment Generator
Runs tests with optional coverage reporting and attractive output formatting.
"""

import sys
import subprocess
import argparse
import platform
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


def get_python_command():
    """Get the current operating system"""
    if platform.system() == 'Windows':
        return 'python'
    else:
        return 'python3'

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
        get_python_command() + ' -m pytest --version',
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
        get_python_command() + ' -c "import pytest_cov" 2>/dev/null',
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

    cmd = f"{get_python_command()} -m pip install {' '.join(packages)}"
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


def run_tests_with_unittest(test_path=None):
    """Run tests using unittest as fallback"""
    print_section("Running Tests with unittest", Colors.OKBLUE)
    print_info("pytest not found, falling back to unittest\n")

    import os
    import unittest

    # Determine test path
    if test_path:
        test_location = test_path
    else:
        test_location = 'tests'

    # Discover and run tests
    loader = unittest.TestLoader()
    if os.path.isfile(test_location):
        # Load specific test file
        suite = loader.discover(os.path.dirname(test_location),
                               pattern=os.path.basename(test_location))
    else:
        # Load all tests from directory
        suite = loader.discover(test_location, pattern='test_*.py')

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print results
    print_section("Test Results", Colors.OKBLUE)

    if result.wasSuccessful():
        print_success(f"All tests passed! ✨")
        print_success(f"Ran {result.testsRun} tests")
        print_banner("SUCCESS", Colors.OKGREEN)
        return True
    else:
        print_error(f"Some tests failed")
        print_info(f"Failures: {len(result.failures)}")
        print_info(f"Errors: {len(result.errors)}")
        print_banner("FAILED", Colors.FAIL)
        return False


def run_tests(with_coverage=False, verbose=False, test_path=None, auto_install=False):
    """Run the test suite"""
    print_banner("🧪 DOXYGEN COMMENT GENERATOR TEST SUITE 🧪", Colors.HEADER)

    # Check dependencies
    pytest_available = check_dependencies()

    if not pytest_available:
        if auto_install:
            print_info("\nAttempting to install missing dependencies...")
            if not install_dependencies(with_coverage=with_coverage):
                print_error("\nFailed to install dependencies automatically.")
                print_info("Falling back to unittest...")
                return run_tests_with_unittest(test_path)
            print()
            # Re-check after installation
            pytest_available = True
        else:
            print_info("\npytest not installed. Use --install-deps to install it.")
            print_info("Falling back to unittest (coverage not available)...\n")
            return run_tests_with_unittest(test_path)

    # Build pytest command
    cmd_parts = [get_python_command(), '-m', 'pytest']

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
  %(prog)s                    # Run all tests (uses unittest if pytest missing)
  %(prog)s --coverage         # Run tests with coverage report (requires pytest)
  %(prog)s -c -v              # Run with coverage and verbose output
  %(prog)s tests/test_generator.py  # Run specific test file
  %(prog)s --install-deps     # Install pytest and pytest-cov, then run tests
  %(prog)s --auto-install     # Auto-install pytest if missing

Note: The script uses unittest as fallback if pytest is not installed.
      Use --install-deps or --auto-install to install pytest automatically.
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
        help='Automatically install pytest/pytest-cov if missing and run tests'
    )

    parser.add_argument(
        '--auto-install',
        action='store_true',
        help='Automatically install pytest if missing (same as --install-deps)'
    )

    args = parser.parse_args()

    # Change to project root directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    import os
    os.chdir(project_root)

    # Determine if we should auto-install
    auto_install = args.install_deps or args.auto_install

    # Run tests
    success = run_tests(
        with_coverage=args.coverage,
        verbose=args.verbose,
        test_path=args.test_path,
        auto_install=auto_install
    )

    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
