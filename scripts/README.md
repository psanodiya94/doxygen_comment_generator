# Test Scripts

This directory contains scripts for running tests and other development tasks.

## run_tests.py

A comprehensive test runner with clean, attractive output and optional coverage reporting.

### Features

- **Unittest Fallback**: Automatically falls back to unittest if pytest is not installed
- **Optional Auto-installation**: Can install pytest automatically with --install-deps flag
- Clean, colorful output with ANSI colors
- Progress indicators and test results
- Optional coverage reporting with HTML output (requires pytest)
- Automatic dependency checking
- Easy to use command-line interface
- Works on any machine - even without pytest!

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

To install pytest and pytest-cov:
```bash
python3 scripts/run_tests.py --install-deps
```

or

```bash
python3 scripts/run_tests.py --auto-install
```

Both flags will install pytest if missing and then run the tests.

### Options

- `-c, --coverage`: Run tests with coverage reporting (requires pytest)
- `-v, --verbose`: Verbose output (show each test)
- `--install-deps`: Install pytest/pytest-cov if missing and run tests
- `--auto-install`: Same as --install-deps
- `-h, --help`: Show help message

### Examples

```bash
# Run all tests (uses unittest if pytest not available)
python3 scripts/run_tests.py

# Run tests with coverage (installs pytest if needed)
python3 scripts/run_tests.py --install-deps --coverage

# Run specific test file with coverage
python3 scripts/run_tests.py --auto-install -c tests/test_generator.py

# Just install dependencies
python3 scripts/run_tests.py --install-deps
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
- pip (for installing pytest with --install-deps flag)

**Note**: The script will use unittest (built into Python) if pytest is not installed. For coverage reporting and advanced features, use `--install-deps` to install pytest and pytest-cov.
