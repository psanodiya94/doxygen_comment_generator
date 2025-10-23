# Doxygen Comment Generator for C++

Automatically generate Doxygen-style comments for C++ code, with specialized support for unit test documentation.

## Key Features

- **Test Framework Support**: Google Test, Catch2, doctest, Boost.Test, CppUnit
- **Batch Processing**: Process entire directories or projects
- **Smart Analysis**: Automatically detects test frameworks and generates meaningful descriptions
- **File Types**: Headers (.h, .hpp) and source files (.cpp, .cc, .cxx)

## Quick Start

```bash
# Clone and setup
git clone https://github.com/yourusername/doxygen_comment_generator.git
cd doxygen_comment_generator

# Document a single file
python src/generator/main.py -f myfile.cpp

# Document all tests in a directory
python src/generator/main.py -d tests/

# Document entire project (include/ and src/ directories)
python src/generator/main.py -p /path/to/project
```

## Installation

**Requirements**: Python 3.7+

No external dependencies required! Standard library only.

**Optional**: For GUI mode, ensure Tkinter is available:
```bash
# Ubuntu/Debian
sudo apt-get install python3-tk
```

## Usage Examples

### Single File
```bash
# Process and modify in place
python src/generator/main.py -f src/calculator.cpp

# Preview without modifying (dry-run)
python src/generator/main.py -f src/calculator.cpp --dry-run

# Save to different file
python src/generator/main.py -f src/calculator.cpp -o documented/calculator.cpp
```

### Test Files
Tool automatically detects testing frameworks:

```bash
# Google Test
python src/generator/main.py -f tests/test_math.cpp
# Output: Detected test file using gtest framework

# Catch2
python src/generator/main.py -f tests/test_string.cpp

# CppUnit
python src/generator/main.py -f tests/test_calculator.cpp
```

### Directory Processing
```bash
# Process all C++ files in directory
python src/generator/main.py -d src/

# Process recursively (default)
python src/generator/main.py -d include/ --recursive

# Process project (auto-finds include/, src/, tests/)
python src/generator/main.py -p .
```

### Advanced Options
```bash
# Enhance existing Doxygen comments
python src/generator/main.py -d src/ --enhance-existing

# GUI mode
python src/generator/main.py --gui
```

## Command Reference

### Input
- `-f <file>` - Process single C++ file
- `-d <dir>` - Process directory
- `-p <project>` - Process project root (auto-finds source directories)

### Output
- `-o <path>` - Output file/directory (default: modify in place)
- `--dry-run` - Preview without modifying files

### Options
- `--enhance-existing` - Modify existing Doxygen comments
- `--recursive` - Process subdirectories (default: true)
- `--no-recursive` - Don't recurse into subdirectories
- `--gui` - Launch graphical interface
- `-h` - Show help

## Output Examples

### Regular Function
```cpp
/**
 * @brief Calculate sum of two numbers
 * @details
 * @param a First number
 * @param b Second number
 * @return int Sum of a and b
 * @throws std::exception on error
 */
int add(int a, int b);
```

### Test Case (Google Test)
```cpp
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
```

## Testing Frameworks

| Framework | Supported Macros |
|-----------|-----------------|
| **Google Test** | TEST, TEST_F, TEST_P, TYPED_TEST |
| **Catch2** | TEST_CASE, SCENARIO, SECTION |
| **doctest** | TEST_CASE, SCENARIO |
| **Boost.Test** | BOOST_AUTO_TEST_CASE |
| **CppUnit** | CPPUNIT_TEST, test methods |

## Running Tests

```bash
# Run all tests
python -m unittest discover -s tests

# Run specific test suite
python -m unittest tests.test_new_features
```

All 57 tests pass ✓

## Real-World Usage

### CI/CD Integration
```bash
# In your CI pipeline
python src/generator/main.py -p . --dry-run
# Review, then:
python src/generator/main.py -p .
git add -A
git commit -m "Add Doxygen documentation"
```

### Pre-commit Hook
```bash
#!/bin/bash
# .git/hooks/pre-commit
python src/generator/main.py -d src/ --dry-run
```

### Document New Test File
```bash
# After writing tests
python src/generator/main.py -f tests/test_new_feature.cpp
# Comments added automatically based on test framework
```

## Notes

- **Preserves existing comments** by default (use `--enhance-existing` to modify)
- **Skips build directories** (.git, build, cmake-build-*)
- **Smart indentation** preserves your code style
- **No configuration needed** - works out of the box

## Sample Files

Check `sample/` directory for examples:
- `SampleHeader.h` - Various C++ constructs
- `test_example_gtest.cpp` - Google Test
- `test_example_catch2.cpp` - Catch2
- `test_example_cppunit.cpp` - CppUnit

## License

MIT License - see LICENSE file

## Contributing

1. Add tests for new features
2. Ensure all tests pass: `python -m unittest discover -s tests`
3. Submit pull request

---

**Perfect for**: Documenting unit tests, maintaining legacy code, CI/CD automation, team projects
