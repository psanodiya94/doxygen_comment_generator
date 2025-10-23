# doxygen_comment_generator

## Project Description

**doxygen_comment_generator** is a Python tool that automatically generates Doxygen-style comments for C++ header and source files. It analyzes your code and inserts well-formatted Doxygen comments for classes, functions, enums, variables, and **test cases**, helping you maintain high-quality documentation with minimal effort.

Perfect for documenting unit tests! The tool intelligently detects and documents test cases from popular testing frameworks, making it ideal for newly written test code.

## Features

### Core Capabilities
- **Supports C++ header files** (`.h`, `.hpp`, `.hh`, `.hxx`)
- **Supports C++ source files** (`.cpp`, `.cc`, `.cxx`, `.c++`)
- **Intelligent test case documentation** - automatically detects and documents unit tests
- **Multi-framework support** - Google Test, Catch2, doctest, Boost.Test
- Preserves code indentation in generated comments
- Simple command-line interface and optional GUI

### Test Case Documentation
- Automatically detects testing frameworks in your code
- Generates meaningful descriptions from test names
- Analyzes test coverage (what assertions are used)
- Documents test suites, fixtures, and test types
- Perfect for documenting newly written unit tests

## Installation

1. **Clone the repository:**

   ```sh
   git clone https://github.com/yourusername/doxygen_comment_generator.git
   cd doxygen_comment_generator
   ```

2. **(Recommended) Create and activate a virtual environment:**

   ```sh
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

   *(This keeps dependencies isolated and makes it easy to manage your Python environment.)*

## GUI Requirements

If you want to use the `--gui` option, your Python must have Tkinter installed (it is included by default on most systems, but not all minimal Linux installs). If you see an error about Tkinter missing, install it with:

```sh
# On Ubuntu/Debian:
sudo apt-get install python3-tk
# On Fedora:
sudo dnf install python3-tkinter
# On Arch:
sudo pacman -S tk
```

If you use a virtual environment, Tkinter must be available in the system Python used to create the venv.

1. **Install dependencies:**

   ```sh
   pip install -r requirements.txt
   ```

   *(If `requirements.txt` does not exist, you can skip this step if there are no extra dependencies.)*

## Usage

### Basic Usage

To generate Doxygen comments for any C++ file (header or source), run:

```sh
python src/generator/main.py -f <path_to_your_cpp_file>
```

**Examples:**

```sh
# For header files
python src/generator/main.py -f include/myclass.h

# For source files
python src/generator/main.py -f src/myclass.cpp

# For test files (automatic test framework detection)
python src/generator/main.py -f tests/test_myclass.cpp
```

### Test File Documentation

The tool automatically detects test files and generates specialized documentation:

```sh
# Document Google Test file
python src/generator/main.py -f tests/test_math.cpp

# Document Catch2 test file
python src/generator/main.py -f tests/test_string.cpp
```

When processing test files, the tool will:
- Detect the testing framework automatically
- Generate descriptive comments for each test case
- Document what each test covers
- Include test suite and fixture information

## Command-Line Options

The script supports the following options:

- `-f <path_to_file>`: Path to the C++ file to process (header or source, required unless using `--gui`)
- `-o <path_to_output>`: Path to output file (default: overwrites input file)
- `--dry-run`: Print output to console instead of writing to file
- `--test-mode`: Enable specialized test case documentation mode
- `--gui`: Launch graphical interface for file selection and comment generation (requires Tkinter)
- `-h`, `--help`: Show help message and exit

**Example usage:**

```sh
# Process and preview output without modifying file
python src/generator/main.py -f myfile.cpp --dry-run

# Save to a different file
python src/generator/main.py -f myfile.h -o myfile_documented.h

# Use GUI mode
python src/generator/main.py --gui

# Get help
python src/generator/main.py -h
```

## Running Tests

To run the unit tests:

```sh
python -m unittest discover -s tests
```

or run specific test suites:

```sh
# Test header generator
python -m unittest tests.test_generator

# Test C++ source generator and test analyzer
python -m unittest tests.test_cpp_generator
```

## Examples

### Example 1: Documenting a Regular C++ Class

**Input (myclass.h):**
```cpp
class Calculator {
public:
    int add(int a, int b);
    int multiply(int a, int b);
};
```

**Output:**
```cpp
/**
 * @brief class Calculator
 *
 * @details Detailed description of class Calculator
 */
class Calculator {
public:
    /**
     * @brief Adds a new
     * @details
     * @param a
     * @param b
     * @return int
     * @throws std::exception on error
     */
    int add(int a, int b);

    /**
     * @brief Multiplies
     * @details
     * @param a
     * @param b
     * @return int
     * @throws std::exception on error
     */
    int multiply(int a, int b);
};
```

### Example 2: Documenting Google Test Cases

**Input (test_math.cpp):**
```cpp
#include <gtest/gtest.h>

TEST(MathTest, TestAddition) {
    EXPECT_EQ(2 + 2, 4);
    EXPECT_NE(2 + 2, 5);
}

TEST_F(CalculatorTest, TestMultiplication) {
    EXPECT_EQ(multiply(3, 4), 12);
}
```

**Output:**
```cpp
#include <gtest/gtest.h>

/**
 * @brief Tests Addition
 *
 * @details
 * Test Suite: MathTest
 * Framework: Google Test
 *
 * Test Coverage:
 * - Covers equality comparison
 * - Covers inequality comparison
 *
 * @test TEST
 */
TEST(MathTest, TestAddition) {
    EXPECT_EQ(2 + 2, 4);
    EXPECT_NE(2 + 2, 5);
}

/**
 * @brief Tests Multiplication
 *
 * @details
 * Test Suite: CalculatorTest
 * Test Fixture: CalculatorTest
 * Framework: Google Test
 *
 * Test Coverage:
 * - Covers equality comparison
 *
 * @test TEST_F
 */
TEST_F(CalculatorTest, TestMultiplication) {
    EXPECT_EQ(multiply(3, 4), 12);
}
```

## Supported Testing Frameworks

- **Google Test (gtest)** - TEST, TEST_F, TEST_P, TYPED_TEST, etc.
- **Catch2** - TEST_CASE, SCENARIO, SECTION, etc.
- **doctest** - TEST_CASE, SCENARIO, TEST_SUITE, etc.
- **Boost.Test** - BOOST_AUTO_TEST_CASE, BOOST_FIXTURE_TEST_CASE, etc.

The tool automatically detects the framework by analyzing include directives and test macros.

## Notes

- **Python 3.7+** required
- For best results, use the tool on well-formatted C++ code
- Supports both **header files** (`.h`, `.hpp`, `.hh`, `.hxx`) and **source files** (`.cpp`, `.cc`, `.cxx`, `.c++`)
- **Test files are automatically detected** - no special flags needed
- The tool preserves existing Doxygen comments and doesn't duplicate them
- Perfect for documenting newly written unit tests in your codebase

## Sample Files

Check the `sample/` directory for example files:
- `SampleHeader.h` - Example header file with various C++ constructs
- `test_example_gtest.cpp` - Example Google Test file
- `test_example_catch2.cpp` - Example Catch2 test file
