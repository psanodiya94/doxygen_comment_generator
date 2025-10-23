"""
Tests for CppUnit support and new features added to the generator.
"""

import unittest
import sys
import os
from unittest.mock import patch, mock_open
import tempfile
import shutil

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from generator.test_analyzer import TestCaseAnalyzer, TestInfo
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

    def test_process_directory_dry_run(self):
        """Test directory processing in dry-run mode."""
        self.test_dir = tempfile.mkdtemp()

        # Create a simple C++ file
        test_file = os.path.join(self.test_dir, 'test.h')
        with open(test_file, 'w') as f:
            f.write('class Test {};\n')

        results = self.processor.process_directory(self.test_dir, dry_run=True, recursive=False)

        self.assertEqual(len(results), 1)
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


if __name__ == "__main__":
    unittest.main()
