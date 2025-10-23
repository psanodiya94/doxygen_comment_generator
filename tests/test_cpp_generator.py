"""
Tests for C++ source file generator and test case analyzer.
"""

import unittest
import sys
import os
from unittest.mock import patch, mock_open

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from generator.cpp.cpp_generator import CppSourceGenerator
from generator.test_analyzer import TestCaseAnalyzer, TestInfo


class TestCppSourceGenerator(unittest.TestCase):
    """Test cases for CppSourceGenerator."""

    def setUp(self):
        """Set up test fixtures."""
        self.generator = CppSourceGenerator()

    @patch("builtins.open", new_callable=mock_open, read_data="""
#include <iostream>

void helperFunction(int x) {
    std::cout << x << std::endl;
}

int main() {
    helperFunction(42);
    return 0;
}
""")
    def test_parse_regular_cpp_file(self, mock_file):
        """Test parsing a regular C++ source file."""
        result = self.generator.parse_source("test.cpp")
        self.assertIsInstance(result, list)
        # Should have generated comments for functions
        self.assertTrue(any("@brief" in line for line in result))

    @patch("builtins.open", new_callable=mock_open, read_data="""
#include <gtest/gtest.h>

TEST(MathTest, Addition) {
    EXPECT_EQ(2 + 2, 4);
}
""")
    def test_parse_gtest_file(self, mock_file):
        """Test parsing a Google Test file."""
        result = self.generator.parse_source("test_math.cpp")
        self.assertIsInstance(result, list)
        self.assertTrue(self.generator.is_test_file)
        self.assertEqual(self.generator.detected_framework, 'gtest')
        # Should have test-specific documentation
        self.assertTrue(any("@brief" in line for line in result))
        self.assertTrue(any("@test" in line for line in result))

    @patch("builtins.open", new_callable=mock_open, read_data="""
#include <catch2/catch.hpp>

TEST_CASE("String operations", "[string]") {
    REQUIRE(true);
}
""")
    def test_parse_catch2_file(self, mock_file):
        """Test parsing a Catch2 test file."""
        result = self.generator.parse_source("test_string.cpp")
        self.assertIsInstance(result, list)
        self.assertTrue(self.generator.is_test_file)
        self.assertEqual(self.generator.detected_framework, 'catch2')

    @patch("builtins.open", new_callable=mock_open, read_data="""
class Calculator {
public:
    int add(int a, int b) {
        return a + b;
    }

    int subtract(int a, int b) {
        return a - b;
    }
};
""")
    def test_parse_class_in_cpp_file(self, mock_file):
        """Test parsing class definitions in C++ source file."""
        result = self.generator.parse_source("calculator.cpp")
        self.assertIsInstance(result, list)
        # Should have class and method comments
        self.assertTrue(any("class Calculator" in line for line in result))
        self.assertTrue(any("@brief" in line for line in result))

    @patch("builtins.open", new_callable=mock_open, read_data="""
namespace Utils {
    int factorial(int n) {
        if (n <= 1) return 1;
        return n * factorial(n - 1);
    }
}
""")
    def test_parse_namespace_in_cpp_file(self, mock_file):
        """Test parsing namespace in C++ source file."""
        result = self.generator.parse_source("utils.cpp")
        self.assertIsInstance(result, list)
        # Should preserve namespace and add function comments
        self.assertTrue(any("namespace Utils" in line for line in result))
        self.assertTrue(any("@brief" in line for line in result))


class TestTestCaseAnalyzer(unittest.TestCase):
    """Test cases for TestCaseAnalyzer."""

    def setUp(self):
        """Set up test fixtures."""
        self.analyzer = TestCaseAnalyzer()

    def test_detect_gtest_framework(self):
        """Test detection of Google Test framework."""
        lines = ['#include <gtest/gtest.h>', '', 'TEST(Foo, Bar) {}']
        framework = self.analyzer.detect_test_framework(lines)
        self.assertEqual(framework, 'gtest')

    def test_detect_catch2_framework(self):
        """Test detection of Catch2 framework."""
        lines = ['#include <catch2/catch.hpp>', '', 'TEST_CASE("test") {}']
        framework = self.analyzer.detect_test_framework(lines)
        self.assertEqual(framework, 'catch2')

    def test_detect_doctest_framework(self):
        """Test detection of doctest framework."""
        lines = ['#include <doctest/doctest.h>', '', 'TEST_CASE("test") {}']
        framework = self.analyzer.detect_test_framework(lines)
        self.assertEqual(framework, 'doctest')

    def test_detect_boost_framework(self):
        """Test detection of Boost.Test framework."""
        lines = ['#include <boost/test/unit_test.hpp>', '', 'BOOST_AUTO_TEST_CASE(test) {}']
        framework = self.analyzer.detect_test_framework(lines)
        self.assertEqual(framework, 'boost')

    def test_parse_gtest_test_case(self):
        """Test parsing Google Test TEST macro."""
        lines = ['TEST(TestSuite, TestName) {', '    EXPECT_EQ(1, 1);', '}']
        result = self.analyzer.parse_test_case(lines, 0, 'gtest')
        self.assertIsNotNone(result)
        test_info, end_idx = result
        self.assertEqual(test_info.framework, 'gtest')
        self.assertEqual(test_info.test_name, 'TestName')
        self.assertEqual(test_info.test_suite, 'TestSuite')
        self.assertIn('EXPECT_EQ', test_info.assertions)

    def test_parse_gtest_test_f_case(self):
        """Test parsing Google Test TEST_F macro."""
        lines = ['TEST_F(FixtureClass, TestName) {', '    ASSERT_TRUE(true);', '}']
        result = self.analyzer.parse_test_case(lines, 0, 'gtest')
        self.assertIsNotNone(result)
        test_info, end_idx = result
        self.assertEqual(test_info.test_type, 'TEST_F')
        self.assertEqual(test_info.fixture_class, 'FixtureClass')

    def test_parse_catch2_test_case(self):
        """Test parsing Catch2 TEST_CASE macro."""
        lines = ['TEST_CASE("Test name", "[tag]") {', '    REQUIRE(true);', '}']
        result = self.analyzer.parse_test_case(lines, 0, 'catch2')
        self.assertIsNotNone(result)
        test_info, end_idx = result
        self.assertEqual(test_info.framework, 'catch2')
        self.assertEqual(test_info.test_name, 'Test name')

    def test_generate_test_description_snake_case(self):
        """Test generating description from snake_case test name."""
        test_info = TestInfo(
            framework='gtest',
            test_name='Test_Addition_Returns_Correct_Result',
            test_suite='MathTest'
        )
        description = self.analyzer.generate_test_description(test_info)
        self.assertIn('Addition', description)
        self.assertIn('Returns', description)

    def test_generate_test_description_camel_case(self):
        """Test generating description from CamelCase test name."""
        test_info = TestInfo(
            framework='gtest',
            test_name='TestAdditionReturnsCorrectResult',
            test_suite='MathTest'
        )
        description = self.analyzer.generate_test_description(test_info)
        self.assertIsInstance(description, str)
        self.assertTrue(len(description) > 0)

    def test_analyze_test_coverage(self):
        """Test analyzing test coverage from assertions."""
        test_info = TestInfo(
            framework='gtest',
            test_name='TestEquality',
            test_suite='ComparisonTest',
            assertions=['EXPECT_EQ', 'EXPECT_TRUE', 'EXPECT_THROW']
        )
        coverage = self.analyzer.analyze_test_coverage(test_info)
        self.assertIsInstance(coverage, list)
        self.assertTrue(len(coverage) > 0)
        self.assertTrue(any('equality' in point.lower() for point in coverage))

    def test_extract_assertions_gtest(self):
        """Test extracting Google Test assertions."""
        body_lines = [
            '    EXPECT_EQ(a, b);',
            '    ASSERT_TRUE(condition);',
            '    EXPECT_THROW(func(), std::exception);'
        ]
        assertions = self.analyzer._extract_assertions(body_lines, 'gtest')
        self.assertIn('EXPECT_EQ', assertions)
        self.assertIn('ASSERT_TRUE', assertions)
        self.assertIn('EXPECT_THROW', assertions)

    def test_extract_assertions_catch2(self):
        """Test extracting Catch2 assertions."""
        body_lines = [
            '    REQUIRE(condition);',
            '    CHECK_FALSE(!condition);',
            '    REQUIRE_THROWS(func());'
        ]
        assertions = self.analyzer._extract_assertions(body_lines, 'catch2')
        self.assertIn('REQUIRE', assertions)
        self.assertIn('CHECK_FALSE', assertions)
        self.assertIn('REQUIRE_THROWS', assertions)

    def test_find_test_body(self):
        """Test finding test function body boundaries."""
        lines = [
            'TEST(Foo, Bar) {',
            '    int x = 1;',
            '    EXPECT_EQ(x, 1);',
            '}'
        ]
        start, end = self.analyzer._find_test_body(lines, 0)
        self.assertEqual(start, 0)
        self.assertEqual(end, 3)

    def test_find_nested_braces_test_body(self):
        """Test finding test body with nested braces."""
        lines = [
            'TEST(Foo, Bar) {',
            '    if (true) {',
            '        int x = 1;',
            '    }',
            '    EXPECT_EQ(1, 1);',
            '}'
        ]
        start, end = self.analyzer._find_test_body(lines, 0)
        self.assertEqual(start, 0)
        self.assertEqual(end, 5)


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete workflow."""

    @patch("builtins.open", new_callable=mock_open, read_data="""
#include <gtest/gtest.h>

class StringUtilsTest : public ::testing::Test {
protected:
    std::string test_string;
};

TEST_F(StringUtilsTest, TestLength) {
    EXPECT_EQ(test_string.length(), 10);
    EXPECT_TRUE(test_string.length() > 0);
}

TEST(MathUtils, TestAddition) {
    int result = 2 + 2;
    EXPECT_EQ(result, 4);
}
""")
    def test_full_test_file_processing(self, mock_file):
        """Test processing a complete test file with multiple test cases."""
        generator = CppSourceGenerator()
        result = generator.parse_source("test_utils.cpp")

        # Verify test file detection
        self.assertTrue(generator.is_test_file)
        self.assertEqual(generator.detected_framework, 'gtest')

        # Verify comment generation
        result_str = ''.join(result)
        self.assertIn('@brief', result_str)
        self.assertIn('@test', result_str)
        self.assertIn('Google Test', result_str)

        # Verify both TEST and TEST_F are documented
        self.assertIn('TestLength', result_str)
        self.assertIn('TestAddition', result_str)


if __name__ == "__main__":
    unittest.main()
