# Test Scripts

This directory contains scripts for running tests and other development tasks.

## run_tests.py

A comprehensive test runner with clean, attractive output and optional coverage reporting.

### Features

- **Auto-installation**: Automatically installs pytest if not found (no manual setup needed!)
- Clean, colorful output with ANSI colors
- Progress indicators and test results
- Optional coverage reporting with HTML output
- Automatic dependency checking
- Easy to use command-line interface
- Works on any machine, even without pytest pre-installed

### Usage

#### Basic Usage

Run all tests:
```bash
python3 scripts/run_tests.py
```

Or using the bash wrapper:
```bash
./scripts/run_tests.sh
```

#### Run with Coverage

Generate coverage report:
```bash
python3 scripts/run_tests.py --coverage
# or
python3 scripts/run_tests.py -c
```

This will:
- Run all tests with coverage tracking
- Display coverage summary in terminal with missing lines
- Generate HTML coverage report in `htmlcov/index.html`

#### Run Specific Tests

Run a specific test file:
```bash
python3 scripts/run_tests.py tests/test_generator.py
```

Run with coverage and verbose output:
```bash
python3 scripts/run_tests.py -c -v tests/test_cpp_generator.py
```

#### Install Dependencies

The script automatically installs pytest if it's not found. You can also manually install dependencies:
```bash
python3 scripts/run_tests.py --install-deps
```

To prevent automatic installation:
```bash
python3 scripts/run_tests.py --no-auto-install
```

### Options

- `-c, --coverage`: Run tests with coverage reporting
- `-v, --verbose`: Verbose output (show each test)
- `--install-deps`: Install test dependencies and exit (pytest, pytest-cov)
- `--no-auto-install`: Do not automatically install missing dependencies
- `-h, --help`: Show help message

### Examples

```bash
# Run all tests (auto-installs pytest if not found)
python3 scripts/run_tests.py

# Run tests with coverage
python3 scripts/run_tests.py --coverage

# Run specific test file with coverage
python3 scripts/run_tests.py -c tests/test_generator.py

# Install dependencies only (useful for CI/CD setup)
python3 scripts/run_tests.py --install-deps

# Run without auto-installing dependencies
python3 scripts/run_tests.py --no-auto-install
```

### Output

The script provides:
- Dependency checking
- Colorful test progress
- Test results summary
- Coverage report (when using --coverage)
- Success/failure banner

### Requirements

- Python 3.7+
- pip (for auto-installing dependencies)

**Note**: pytest and pytest-cov are automatically installed if not found. You don't need to install them manually unless you use the `--no-auto-install` flag.
