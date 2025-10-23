"""
Test Case Analyzer for extracting test information and generating meaningful documentation.
Supports popular C++ testing frameworks: Google Test, Catch2, doctest, Boost.Test, and more.
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class TestInfo:
    """Information about a detected test case."""
    framework: str  # 'gtest', 'catch2', 'doctest', 'boost', 'custom'
    test_name: str
    test_suite: Optional[str] = None
    test_type: str = 'TEST'  # TEST, TEST_F, TEST_P, SCENARIO, etc.
    fixture_class: Optional[str] = None
    assertions: List[str] = None
    description: Optional[str] = None

    def __post_init__(self):
        if self.assertions is None:
            self.assertions = []


class TestCaseAnalyzer:
    """
    Analyzes C++ test code to extract test case information and generate
    meaningful Doxygen comments describing what each test covers.
    """

    # Google Test patterns
    GTEST_PATTERNS = [
        r'TEST\s*\(\s*(\w+)\s*,\s*(\w+)\s*\)',           # TEST(TestSuite, TestName)
        r'TEST_F\s*\(\s*(\w+)\s*,\s*(\w+)\s*\)',         # TEST_F(FixtureClass, TestName)
        r'TEST_P\s*\(\s*(\w+)\s*,\s*(\w+)\s*\)',         # TEST_P(TestSuite, TestName)
        r'TYPED_TEST\s*\(\s*(\w+)\s*,\s*(\w+)\s*\)',     # TYPED_TEST(TestSuite, TestName)
        r'TYPED_TEST_P\s*\(\s*(\w+)\s*,\s*(\w+)\s*\)',   # TYPED_TEST_P(TestSuite, TestName)
    ]

    # Catch2 patterns
    CATCH2_PATTERNS = [
        r'TEST_CASE\s*\(\s*"([^"]+)"(?:\s*,\s*"([^"]*)")?\s*\)',  # TEST_CASE("test name", "[tag]")
        r'SCENARIO\s*\(\s*"([^"]+)"(?:\s*,\s*"([^"]*)")?\s*\)',   # SCENARIO("scenario name", "[tag]")
        r'TEMPLATE_TEST_CASE\s*\(\s*"([^"]+)"',                   # TEMPLATE_TEST_CASE("test name", ...)
    ]

    # doctest patterns
    DOCTEST_PATTERNS = [
        r'TEST_CASE\s*\(\s*"([^"]+)"\s*\)',              # TEST_CASE("test name")
        r'SCENARIO\s*\(\s*"([^"]+)"\s*\)',               # SCENARIO("scenario name")
        r'TEST_SUITE\s*\(\s*"([^"]+)"\s*\)',             # TEST_SUITE("suite name")
    ]

    # Boost.Test patterns
    BOOST_PATTERNS = [
        r'BOOST_AUTO_TEST_CASE\s*\(\s*(\w+)\s*\)',                      # BOOST_AUTO_TEST_CASE(test_name)
        r'BOOST_FIXTURE_TEST_CASE\s*\(\s*(\w+)\s*,\s*(\w+)\s*\)',       # BOOST_FIXTURE_TEST_CASE(test, fixture)
        r'BOOST_AUTO_TEST_SUITE\s*\(\s*(\w+)\s*\)',                     # BOOST_AUTO_TEST_SUITE(suite_name)
    ]

    # Common assertion patterns across frameworks
    ASSERTION_PATTERNS = {
        'gtest': [
            r'EXPECT_EQ', r'EXPECT_NE', r'EXPECT_LT', r'EXPECT_LE', r'EXPECT_GT', r'EXPECT_GE',
            r'EXPECT_TRUE', r'EXPECT_FALSE', r'EXPECT_STREQ', r'EXPECT_STRNE',
            r'EXPECT_THROW', r'EXPECT_NO_THROW', r'EXPECT_ANY_THROW',
            r'ASSERT_EQ', r'ASSERT_NE', r'ASSERT_LT', r'ASSERT_LE', r'ASSERT_GT', r'ASSERT_GE',
            r'ASSERT_TRUE', r'ASSERT_FALSE', r'ASSERT_THROW', r'ASSERT_NO_THROW',
        ],
        'catch2': [
            r'REQUIRE', r'REQUIRE_FALSE', r'REQUIRE_THROWS', r'REQUIRE_NOTHROW',
            r'CHECK', r'CHECK_FALSE', r'CHECK_THROWS', r'CHECK_NOTHROW',
        ],
        'doctest': [
            r'REQUIRE', r'REQUIRE_FALSE', r'REQUIRE_THROWS', r'REQUIRE_NOTHROW',
            r'CHECK', r'CHECK_FALSE', r'CHECK_THROWS', r'CHECK_NOTHROW',
        ],
        'boost': [
            r'BOOST_CHECK', r'BOOST_REQUIRE', r'BOOST_CHECK_EQUAL', r'BOOST_REQUIRE_EQUAL',
            r'BOOST_CHECK_THROW', r'BOOST_REQUIRE_THROW', r'BOOST_CHECK_NO_THROW',
        ]
    }

    def __init__(self):
        """Initialize the TestCaseAnalyzer."""
        pass

    def detect_test_framework(self, lines: List[str]) -> Optional[str]:
        """
        Detect which testing framework is being used in the file.

        Args:
            lines: Lines from the source file

        Returns:
            Framework name ('gtest', 'catch2', 'doctest', 'boost') or None
        """
        content = '\n'.join(lines)

        # Check for framework-specific includes or macros
        if re.search(r'#include\s*[<"]gtest/gtest\.h[>"]', content):
            return 'gtest'
        if re.search(r'#include\s*[<"]catch2?/catch.*\.hpp[>"]', content):
            return 'catch2'
        if re.search(r'#include\s*[<"]doctest/doctest\.h[>"]', content):
            return 'doctest'
        if re.search(r'#include\s*[<"]boost/test/', content):
            return 'boost'

        # Check for framework-specific macros
        for pattern in self.GTEST_PATTERNS:
            if re.search(pattern, content):
                return 'gtest'

        for pattern in self.CATCH2_PATTERNS:
            if re.search(pattern, content):
                return 'catch2'

        for pattern in self.BOOST_PATTERNS:
            if re.search(pattern, content):
                return 'boost'

        return None

    def parse_test_case(self, lines: List[str], start_idx: int, framework: str) -> Optional[Tuple[TestInfo, int]]:
        """
        Parse a test case starting at the given line index.

        Args:
            lines: All lines from the file
            start_idx: Starting line index
            framework: Detected testing framework

        Returns:
            Tuple of (TestInfo, end_index) or None if not a test case
        """
        line = lines[start_idx].strip()

        if framework == 'gtest':
            return self._parse_gtest_case(lines, start_idx, line)
        elif framework in ('catch2', 'doctest'):
            return self._parse_catch_doctest_case(lines, start_idx, line, framework)
        elif framework == 'boost':
            return self._parse_boost_case(lines, start_idx, line)

        return None

    def _parse_gtest_case(self, lines: List[str], start_idx: int, line: str) -> Optional[Tuple[TestInfo, int]]:
        """Parse Google Test case."""
        for pattern_str in self.GTEST_PATTERNS:
            pattern = re.compile(pattern_str)
            match = pattern.search(line)
            if match:
                # Determine test type
                test_type = line.split('(')[0].strip()

                test_suite = match.group(1)
                test_name = match.group(2)

                # Find the test body
                body_start, body_end = self._find_test_body(lines, start_idx)
                assertions = self._extract_assertions(lines[body_start:body_end+1], 'gtest')

                test_info = TestInfo(
                    framework='gtest',
                    test_name=test_name,
                    test_suite=test_suite,
                    test_type=test_type,
                    fixture_class=test_suite if 'TEST_F' in test_type else None,
                    assertions=assertions
                )

                return test_info, body_end

        return None

    def _parse_catch_doctest_case(self, lines: List[str], start_idx: int, line: str, framework: str) -> Optional[Tuple[TestInfo, int]]:
        """Parse Catch2/doctest test case."""
        patterns = self.CATCH2_PATTERNS if framework == 'catch2' else self.DOCTEST_PATTERNS

        for pattern_str in patterns:
            pattern = re.compile(pattern_str)
            match = pattern.search(line)
            if match:
                test_type = line.split('(')[0].strip()
                test_name = match.group(1)
                test_tags = match.group(2) if match.lastindex >= 2 else None

                body_start, body_end = self._find_test_body(lines, start_idx)
                assertions = self._extract_assertions(lines[body_start:body_end+1], framework)

                test_info = TestInfo(
                    framework=framework,
                    test_name=test_name,
                    test_suite=test_tags,
                    test_type=test_type,
                    assertions=assertions
                )

                return test_info, body_end

        return None

    def _parse_boost_case(self, lines: List[str], start_idx: int, line: str) -> Optional[Tuple[TestInfo, int]]:
        """Parse Boost.Test case."""
        for pattern_str in self.BOOST_PATTERNS:
            pattern = re.compile(pattern_str)
            match = pattern.search(line)
            if match:
                test_type = line.split('(')[0].strip()
                test_name = match.group(1)
                fixture_class = match.group(2) if match.lastindex >= 2 else None

                body_start, body_end = self._find_test_body(lines, start_idx)
                assertions = self._extract_assertions(lines[body_start:body_end+1], 'boost')

                test_info = TestInfo(
                    framework='boost',
                    test_name=test_name,
                    test_type=test_type,
                    fixture_class=fixture_class,
                    assertions=assertions
                )

                return test_info, body_end

        return None

    def _find_test_body(self, lines: List[str], start_idx: int) -> Tuple[int, int]:
        """
        Find the start and end of a test function body.

        Args:
            lines: All lines from the file
            start_idx: Starting line index

        Returns:
            Tuple of (body_start_idx, body_end_idx)
        """
        # Find the opening brace
        body_start = start_idx
        while body_start < len(lines) and '{' not in lines[body_start]:
            body_start += 1

        if body_start >= len(lines):
            return start_idx, start_idx

        # Find the matching closing brace
        brace_count = 0
        body_end = body_start

        for i in range(body_start, len(lines)):
            brace_count += lines[i].count('{')
            brace_count -= lines[i].count('}')

            if brace_count == 0:
                body_end = i
                break

        return body_start, body_end

    def _extract_assertions(self, body_lines: List[str], framework: str) -> List[str]:
        """
        Extract assertion statements from test body.

        Args:
            body_lines: Lines of the test body
            framework: Testing framework name

        Returns:
            List of assertion types found
        """
        assertions = []
        patterns = self.ASSERTION_PATTERNS.get(framework, [])

        body_text = '\n'.join(body_lines)

        for pattern in patterns:
            if re.search(pattern, body_text):
                assertions.append(pattern)

        return assertions

    def generate_test_description(self, test_info: TestInfo) -> str:
        """
        Generate a human-readable description of what the test covers.

        Args:
            test_info: Information about the test case

        Returns:
            Description string
        """
        # Convert test name to readable format
        test_name = test_info.test_name

        # Handle different naming conventions
        if '_' in test_name:
            # snake_case: Test_Function_Returns_True -> Test Function Returns True
            readable = test_name.replace('_', ' ')
        else:
            # CamelCase: TestFunctionReturnsTrue -> Test Function Returns True
            readable = re.sub(r'([A-Z])', r' \1', test_name).strip()

        # Common test prefixes and their meanings
        test_patterns = {
            r'^test\s+': 'Tests ',
            r'^when\s+': 'When ',
            r'^should\s+': 'Should ',
            r'^verify\s+': 'Verifies ',
            r'^check\s+': 'Checks ',
            r'^ensure\s+': 'Ensures ',
            r'^validate\s+': 'Validates ',
        }

        description = readable
        for pattern, replacement in test_patterns.items():
            if re.search(pattern, readable.lower()):
                description = re.sub(pattern, replacement, description, flags=re.IGNORECASE)
                break
        else:
            # If no pattern matched, add "Tests " prefix if not already present
            if not description.lower().startswith(('test', 'verify', 'check', 'ensure', 'validate', 'when', 'should')):
                description = 'Tests ' + description.lower()

        return description

    def analyze_test_coverage(self, test_info: TestInfo) -> List[str]:
        """
        Analyze what the test covers based on assertions and test structure.

        Args:
            test_info: Information about the test case

        Returns:
            List of coverage points
        """
        coverage = []

        # Analyze assertion types
        assertion_coverage = {
            'EXPECT_EQ': 'equality comparison',
            'EXPECT_NE': 'inequality comparison',
            'EXPECT_TRUE': 'boolean true condition',
            'EXPECT_FALSE': 'boolean false condition',
            'EXPECT_THROW': 'exception throwing behavior',
            'EXPECT_NO_THROW': 'no exception behavior',
            'REQUIRE': 'required conditions',
            'CHECK': 'checked conditions',
            'BOOST_CHECK_EQUAL': 'equality validation',
        }

        for assertion in test_info.assertions:
            for pattern, description in assertion_coverage.items():
                if pattern in assertion:
                    coverage.append(f"Covers {description}")
                    break

        # Deduplicate coverage points
        coverage = list(dict.fromkeys(coverage))

        return coverage[:5]  # Limit to top 5 coverage points
