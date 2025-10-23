#!/bin/bash
#
# Convenient wrapper script for running tests
# Usage: ./scripts/run_tests.sh [OPTIONS]
#

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Run the Python test script with all arguments passed through
python3 "$SCRIPT_DIR/run_tests.py" "$@"
