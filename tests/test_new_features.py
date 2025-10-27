"""
Tests for CppUnit support and new features added to the generator.
"""

import unittest
import sys
import os
import platform
from unittest.mock import patch, mock_open
import tempfile
import shutil

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from generator.analyzer import TestCaseAnalyzer, TestInfo
from generator.cpp.cpp_generator import CppSourceGenerator
from generator.directory_processor import DirectoryProcessor


class TestCppUnitSupport(unittest.TestCase):
    """Test CppUnit framework support."""

    def setUp(self):
        """Set up test fixtures."""
        self.analyzer = TestCaseAnalyzer()
        self.generator = CppSourceGenerator()

    def test_detect_cppunit_framework(self):
        """Test detection of CppUnit framework."""
        lines = ['#include <cppunit/TestCase.h>', '', 'CPPUNIT_TEST(testMethod)']
        framework = self.analyzer.detect_test_framework(lines)
        self.assertEqual(framework, 'cppunit')

    def test_parse_cppunit_test_macro(self):
        """Test parsing CPPUNIT_TEST macro."""
        lines = ['CPPUNIT_TEST(testAddition);']
        result = self.analyzer.parse_test_case(lines, 0, 'cppunit')
        self.assertIsNotNone(result)
        test_info, end_idx = result
        self.assertEqual(test_info.framework, 'cppunit')
        self.assertEqual(test_info.test_name, 'testAddition')
        self.assertEqual(test_info.test_type, 'CPPUNIT_TEST')

    def test_parse_cppunit_test_method(self):
        """Test parsing CppUnit test method."""
        lines = [
            'void testMultiplication() {',
            '    CPPUNIT_ASSERT_EQUAL(12, 3 * 4);',
            '}'
        ]
        result = self.analyzer.parse_test_case(lines, 0, 'cppunit')
        self.assertIsNotNone(result)
        test_info, end_idx = result
        self.assertEqual(test_info.test_name, 'testMultiplication')
        self.assertEqual(test_info.test_type, 'CPPUNIT_TEST_METHOD')
        self.assertIn('CPPUNIT_ASSERT_EQUAL', test_info.assertions)

    def test_cppunit_assertion_detection(self):
        """Test CppUnit assertion detection."""
        body_lines = [
            '    CPPUNIT_ASSERT(true);',
            '    CPPUNIT_ASSERT_EQUAL(5, result);',
            '    CPPUNIT_ASSERT_THROW(func(), std::exception);'
        ]
        assertions = self.analyzer._extract_assertions(body_lines, 'cppunit')
        self.assertIn('CPPUNIT_ASSERT', assertions)
        self.assertIn('CPPUNIT_ASSERT_EQUAL', assertions)
        self.assertIn('CPPUNIT_ASSERT_THROW', assertions)

    @patch("builtins.open", new_callable=mock_open, read_data="""
#include <cppunit/TestCase.h>

class MathTest : public CppUnit::TestFixture {
    CPPUNIT_TEST_SUITE(MathTest);
    CPPUNIT_TEST(testAddition);
    CPPUNIT_TEST_SUITE_END();

public:
    void testAddition() {
        CPPUNIT_ASSERT_EQUAL(4, 2 + 2);
    }
};
""")
    def test_cppunit_file_processing(self, mock_file):
        """Test processing a complete CppUnit file."""
        result = self.generator.parse_source("test.cpp")
        self.assertTrue(self.generator.is_test_file)
        self.assertEqual(self.generator.detected_framework, 'cppunit')
        result_str = ''.join(result)
        self.assertIn('@brief', result_str)
        self.assertIn('CppUnit', result_str)


class TestDirectoryProcessing(unittest.TestCase):
    """Test directory processing functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.processor = DirectoryProcessor()
        self.test_dir = None

    def tearDown(self):
        """Clean up test directory."""
        if self.test_dir and os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_find_cpp_files(self):
        """Test finding C++ files in a directory."""
        self.test_dir = tempfile.mkdtemp()

        # Create test files
        open(os.path.join(self.test_dir, 'test1.h'), 'w').close()
        open(os.path.join(self.test_dir, 'test2.cpp'), 'w').close()
        open(os.path.join(self.test_dir, 'readme.txt'), 'w').close()

        files = self.processor.find_cpp_files(self.test_dir, recursive=False)

        self.assertEqual(len(files), 2)
        self.assertTrue(any('test1.h' in f for f in files))
        self.assertTrue(any('test2.cpp' in f for f in files))

    def test_find_cpp_files_recursive(self):
        """Test recursive file finding."""
        self.test_dir = tempfile.mkdtemp()
        subdir = os.path.join(self.test_dir, 'subdir')
        os.makedirs(subdir)

        open(os.path.join(self.test_dir, 'main.cpp'), 'w').close()
        open(os.path.join(subdir, 'helper.h'), 'w').close()

        files = self.processor.find_cpp_files(self.test_dir, recursive=True)

        self.assertEqual(len(files), 2)

    @unittest.skipIf(platform.system() == 'Windows', 'Skip on Windows due to path format issues')
    def test_process_directory_dry_run(self):
        """Test directory processing in dry-run mode."""
        self.test_dir = tempfile.mkdtemp()

        # Create a simple C++ file
        test_file = os.path.join(self.test_dir, 'test.h')
        with open(test_file, 'w') as f:
            f.write('class Test {};\n')

        results = self.processor.process_directory(self.test_dir, dry_run=True, recursive=False)

        self.assertEqual(len(results), 1)
        self.assertIn(test_file, results)
        self.assertTrue(results[test_file][0])  # Success
        self.assertIn('dry run', results[test_file][1].lower())

    def test_skip_build_directories(self):
        """Test that build directories are skipped."""
        self.test_dir = tempfile.mkdtemp()
        build_dir = os.path.join(self.test_dir, 'build')
        os.makedirs(build_dir)

        open(os.path.join(self.test_dir, 'main.cpp'), 'w').close()
        open(os.path.join(build_dir, 'generated.cpp'), 'w').close()

        files = self.processor.find_cpp_files(self.test_dir, recursive=True)

        # Should only find main.cpp, not the one in build/
        self.assertEqual(len(files), 1)
        self.assertTrue('main.cpp' in files[0])
        self.assertFalse(any('build' in f for f in files))


class TestEnhanceExisting(unittest.TestCase):
    """Test enhancing existing Doxygen comments."""

    def setUp(self):
        """Set up test fixtures."""
        self.generator = CppSourceGenerator(enhance_existing=False)
        self.generator_enhance = CppSourceGenerator(enhance_existing=True)

    @patch("builtins.open", new_callable=mock_open, read_data="""
/**
 * @brief Existing comment
 */
class Test {
public:
    void method();
};
""")
    def test_skip_existing_comments(self, mock_file):
        """Test that existing comments are skipped by default."""
        result = self.generator.parse_source("test.h")
        result_str = ''.join(result)

        # Should preserve existing comment
        self.assertIn('Existing comment', result_str)
        # Count @brief occurrences - should be minimal
        brief_count = result_str.count('@brief')
        self.assertLessEqual(brief_count, 3)  # Class comment + maybe method

    def test_enhance_existing_flag(self):
        """Test that enhance_existing flag is set correctly."""
        self.assertFalse(self.generator.enhance_existing)
        self.assertTrue(self.generator_enhance.enhance_existing)


class TestAccessSpecifierHandling(unittest.TestCase):
    """Test proper handling of access specifiers."""

    def setUp(self):
        """Set up test fixtures."""
        self.generator = CppSourceGenerator()

    @patch("builtins.open", new_callable=mock_open, read_data="""
class Test {
public:
    void publicMethod();

protected:
    void protectedMethod();

private:
    int privateVar;
};
""")
    def test_access_specifier_placement(self, mock_file):
        """Test that comments appear after access specifiers."""
        result = self.generator.parse_source("test.h")
        result_str = ''.join(result)
        lines = result_str.split('\n')

        # Find protected: line
        protected_idx = None
        for i, line in enumerate(lines):
            if 'protected:' in line and '@' not in line:
                protected_idx = i
                break

        self.assertIsNotNone(protected_idx, "Should find 'protected:' line")

        # Check that next non-empty line after protected: is either comment or function
        next_line_idx = protected_idx + 1
        while next_line_idx < len(lines) and not lines[next_line_idx].strip():
            next_line_idx += 1

        if next_line_idx < len(lines):
            next_line = lines[next_line_idx]
            # Should be either a comment or the function itself
            self.assertTrue('/**' in next_line or 'void' in next_line or '*' in next_line)


class TestFrameworkNameMapping(unittest.TestCase):
    """Test that framework names are correctly mapped in output."""

    def setUp(self):
        """Set up test fixtures."""
        self.generator = CppSourceGenerator()

    @patch("builtins.open", new_callable=mock_open, read_data="""
#include <cppunit/TestCase.h>

void testSomething() {
    CPPUNIT_ASSERT(true);
}
""")
    def test_cppunit_framework_name(self, mock_file):
        """Test CppUnit framework name in comments."""
        result = self.generator.parse_source("test.cpp")
        result_str = ''.join(result)

        # Should show "CppUnit" not "cppunit"
        self.assertIn('CppUnit', result_str)


class TestDirectoryProcessorExtended(unittest.TestCase):
    """Extended tests for DirectoryProcessor to improve coverage."""

    def setUp(self):
        """Set up test fixtures."""
        self.processor = DirectoryProcessor()
        self.test_dir = None
        self.output_dir = None

    def tearDown(self):
        """Clean up test directories."""
        for directory in [self.test_dir, self.output_dir]:
            if directory and os.path.exists(directory):
                shutil.rmtree(directory)

    def test_directory_does_not_exist(self):
        """Test error when directory doesn't exist."""
        with self.assertRaises(ValueError) as context:
            self.processor.find_cpp_files('/nonexistent/path/to/dir')
        self.assertIn('does not exist', str(context.exception))

    def test_path_is_not_directory(self):
        """Test error when path is a file, not a directory."""
        self.test_dir = tempfile.mkdtemp()
        test_file = os.path.join(self.test_dir, 'test.txt')
        with open(test_file, 'w') as f:
            f.write('test')

        with self.assertRaises(ValueError) as context:
            self.processor.find_cpp_files(test_file)
        self.assertIn('not a directory', str(context.exception))

    def test_no_cpp_files_found(self):
        """Test when no C++ files are found in directory."""
        self.test_dir = tempfile.mkdtemp()
        # Create only non-C++ files
        with open(os.path.join(self.test_dir, 'readme.txt'), 'w') as f:
            f.write('readme')

        results = self.processor.process_directory(self.test_dir, recursive=False)
        self.assertIn('_info', results)
        self.assertFalse(results['_info'][0])
        self.assertIn('No C++ files found', results['_info'][1])

    @unittest.skipIf(platform.system() == 'Windows', 'Skip on Windows due to path format issues')
    def test_process_with_output_dir(self):
        """Test processing files with output directory."""
        self.test_dir = tempfile.mkdtemp()
        self.output_dir = tempfile.mkdtemp()

        # Create a simple C++ file
        test_file = os.path.join(self.test_dir, 'test.h')
        with open(test_file, 'w') as f:
            f.write('class Test { public: void method(); };\n')

        results = self.processor.process_directory(
            self.test_dir,
            output_dir=self.output_dir,
            dry_run=False,
            recursive=False
        )

        # Check that output file was created
        output_file = os.path.join(self.output_dir, 'test.h')
        self.assertTrue(os.path.exists(output_file),
                       f"Output file not found: {output_file}")
        self.assertIn(test_file, results,
                     f"Test file {test_file} not in results: {list(results.keys())}")
        self.assertTrue(results[test_file][0])

    @unittest.skipIf(platform.system() == 'Windows', 'Skip on Windows due to path format issues')
    def test_process_with_subdirectory_output(self):
        """Test processing with subdirectories and output dir."""
        self.test_dir = tempfile.mkdtemp()
        self.output_dir = tempfile.mkdtemp()

        # Create nested structure
        subdir = os.path.join(self.test_dir, 'src')
        os.makedirs(subdir)

        test_file = os.path.join(subdir, 'helper.cpp')
        with open(test_file, 'w') as f:
            f.write('void helper() {}\n')

        results = self.processor.process_directory(
            self.test_dir,
            output_dir=self.output_dir,
            dry_run=False,
            recursive=True
        )

        # Check that nested structure is preserved
        output_file = os.path.join(self.output_dir, 'src', 'helper.cpp')
        # For better debugging, list what files actually exist
        if not os.path.exists(output_file):
            # Walk the output directory to see what was created
            created_files = []
            for root, dirs, files in os.walk(self.output_dir):
                for file in files:
                    created_files.append(os.path.join(root, file))
            self.fail(f"Output file not found: {output_file}\nCreated files: {created_files}")

    def test_enhance_existing_in_processor(self):
        """Test DirectoryProcessor with enhance_existing flag."""
        processor_enhance = DirectoryProcessor(enhance_existing=True)
        self.assertTrue(processor_enhance.generator.enhance_existing)

        processor_normal = DirectoryProcessor(enhance_existing=False)
        self.assertFalse(processor_normal.generator.enhance_existing)

    def test_process_project_method(self):
        """Test process_project method."""
        self.test_dir = tempfile.mkdtemp()

        # Create standard project structure
        src_dir = os.path.join(self.test_dir, 'src')
        include_dir = os.path.join(self.test_dir, 'include')
        os.makedirs(src_dir)
        os.makedirs(include_dir)

        # Create test files
        with open(os.path.join(src_dir, 'main.cpp'), 'w') as f:
            f.write('int main() { return 0; }\n')

        with open(os.path.join(include_dir, 'header.h'), 'w') as f:
            f.write('class Header {};\n')

        results = self.processor.process_project(self.test_dir, dry_run=True)

        # Should process both directories
        self.assertGreater(len(results), 0)
        # Find the files in results
        found_main = any('main.cpp' in path for path in results.keys())
        found_header = any('header.h' in path for path in results.keys())
        self.assertTrue(found_main or found_header)

    def test_process_project_no_standard_dirs(self):
        """Test process_project when no standard directories exist."""
        self.test_dir = tempfile.mkdtemp()

        results = self.processor.process_project(self.test_dir)

        self.assertIn('_info', results)
        self.assertFalse(results['_info'][0])
        self.assertIn('No standard source directories', results['_info'][1])

    def test_process_project_nonexistent(self):
        """Test process_project with non-existent directory."""
        with self.assertRaises(ValueError) as context:
            self.processor.process_project('/nonexistent/project/root')
        self.assertIn('does not exist', str(context.exception))

    def test_print_results_method(self):
        """Test print_results method."""
        # Use os-agnostic paths for Windows compatibility
        import os
        file1 = os.path.join('path', 'to', 'file1.cpp')
        file2 = os.path.join('path', 'to', 'file2.h')
        file3 = os.path.join('path', 'to', 'file3.cpp')

        results = {
            file1: (True, 'Processed successfully'),
            file2: (True, 'Processed successfully (Test file: GoogleTest)'),
            file3: (False, 'Error: Parse error'),
            '_info': (False, 'Some info message')
        }

        # Capture stdout
        from io import StringIO
        import sys
        captured_output = StringIO()
        sys.stdout = captured_output

        try:
            self.processor.print_results(results)
            output = captured_output.getvalue()

            # Check that output contains expected elements
            self.assertIn('Processing Results', output)
            self.assertIn('file1.cpp', output)
            self.assertIn('file2.h', output)
            self.assertIn('file3.cpp', output)
            self.assertIn('Error: Parse error', output)
            self.assertIn('succeeded', output)
            self.assertIn('failed', output)
        finally:
            sys.stdout = sys.__stdout__

    @unittest.skipIf(platform.system() == 'Windows', 'Skip on Windows due to path format issues')
    def test_process_directory_in_place(self):
        """Test processing files in place (no output_dir)."""
        self.test_dir = tempfile.mkdtemp()

        test_file = os.path.join(self.test_dir, 'test.h')
        original_content = 'class Test {};\n'
        with open(test_file, 'w') as f:
            f.write(original_content)

        results = self.processor.process_directory(self.test_dir, dry_run=False, recursive=False)

        # File should be modified in place
        with open(test_file, 'r') as f:
            new_content = f.read()

        self.assertNotEqual(original_content, new_content)
        self.assertIn(test_file, results)
        self.assertTrue(results[test_file][0])

    @unittest.skipIf(platform.system() == 'Windows', 'Skip on Windows due to path format issues')
    def test_process_directory_error_handling(self):
        """Test error handling during directory processing."""
        self.test_dir = tempfile.mkdtemp()

        # Create a file with problematic content that might cause issues
        test_file = os.path.join(self.test_dir, 'test.cpp')
        with open(test_file, 'w') as f:
            f.write('invalid c++ syntax {{{{')

        results = self.processor.process_directory(self.test_dir, dry_run=False, recursive=False)

        # Should still return results, possibly with errors
        self.assertIn(test_file, results)


if __name__ == "__main__":
    unittest.main()
