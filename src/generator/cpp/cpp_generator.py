"""
C++ Source File Doxygen Comment Generator
Handles .cpp, .cc, .cxx files including test files with intelligent test case documentation.
"""

import re
from typing import List, Dict, Optional, Tuple
from ..header.header_generator import HeaderDoxygenGenerator
from ..test_analyzer import TestCaseAnalyzer, TestInfo


class CppSourceGenerator(HeaderDoxygenGenerator):
    """
    Generates Doxygen comments for C++ source files (.cpp, .cc, .cxx).
    Extends HeaderDoxygenGenerator with support for implementation files and test cases.
    """

    def __init__(self):
        """Initialize the CppSourceGenerator."""
        super().__init__()
        self.test_analyzer = TestCaseAnalyzer()
        self.is_test_file = False
        self.detected_framework = None

    def parse_source(self, filename: str) -> List[str]:
        """
        Parse a C++ source file and return lines with added Doxygen comments.

        Args:
            filename (str): Path to the source file.

        Returns:
            List[str]: List of lines with Doxygen comments inserted.

        Raises:
            ValueError: If the file extension is not a supported C++ source file.
        """
        # Support both header and source file extensions
        ext = filename.split('.')[-1].lower()
        if ext not in ["h", "hpp", "hh", "hxx", "cpp", "cc", "cxx", "c++"]:
            raise ValueError("Only C++ header and source files are supported")

        with open(filename, 'r') as f:
            lines = f.readlines()

        # Detect if this is a test file
        self.detected_framework = self.test_analyzer.detect_test_framework(lines)
        self.is_test_file = self.detected_framework is not None

        # If it's a test file, use specialized test parsing
        if self.is_test_file:
            return self._parse_test_file(lines)
        else:
            # Use standard header parsing for regular source files
            return self.parse_header_internal(lines)

    def parse_header_internal(self, lines: List[str]) -> List[str]:
        """
        Internal method to parse lines without file validation.
        Used for both header and source files.

        Args:
            lines (List[str]): Lines from the file

        Returns:
            List[str]: Lines with Doxygen comments
        """
        output = []
        i = 0
        inside_class = False
        class_brace_depth = 0
        last_was_decl = False

        # Main parsing loop
        while i < len(lines):
            line = lines[i].rstrip('\n')
            stripped = line.strip()

            # Skip empty lines (preserve formatting)
            if not stripped:
                output.append(lines[i])
                last_was_decl = False
                i += 1
                continue

            # Skip existing Doxygen comments (do not duplicate)
            if stripped.startswith('/**') or stripped.startswith('///') or stripped.startswith('/*!'):
                while i < len(lines) and '*/' not in lines[i]:
                    output.append(lines[i])
                    i += 1
                if i < len(lines):
                    output.append(lines[i])
                    i += 1
                last_was_decl = False
                continue

            # Handle namespace declaration (track for context)
            namespace_match = re.match(r'namespace\s+(\w+)\s*\{', stripped)
            if namespace_match:
                self.current_namespace = namespace_match.group(1)
                if output and output[-1].strip():
                    output.append('\n')
                output.append(lines[i])
                last_was_decl = True
                i += 1
                continue

            # Class detection and handling (same as header)
            class_decl_lines = []
            class_decl_start = i
            class_decl_found = False
            class_type = None
            class_name = None
            class_decl_pattern = r'^(class|struct)\s+(\w+)(.*)$'
            match = re.match(class_decl_pattern, stripped)
            if match:
                class_type = match.group(1)
                class_name = match.group(2)
                class_decl_lines.append(lines[i])
                if '{' in stripped:
                    class_decl_found = True
                else:
                    j = i + 1
                    while j < len(lines):
                        next_line = lines[j].strip()
                        class_decl_lines.append(lines[j])
                        if next_line.startswith('//') or next_line.startswith('/*'):
                            break
                        if '{' in next_line:
                            class_decl_found = True
                            break
                        if ';' in next_line:
                            break
                        j += 1

            if class_decl_found and class_type and class_name:
                self.current_class = class_name
                inside_class = True
                class_brace_depth = 1
                indent = self._get_indent(class_decl_lines[0])
                if output and output[-1].strip():
                    output.append('\n')
                doc_comment = self._generate_class_comment(class_name, class_type, indent)
                output.extend(doc_comment)
                for l in class_decl_lines:
                    output.append(l)
                output.append('\n')
                i = class_decl_start + len(class_decl_lines)
                last_was_decl = True

                # Process class body (same as header)
                prev_access_specifier_line = None
                in_function_body = 0
                while i < len(lines) and inside_class:
                    line = lines[i].rstrip('\n')
                    stripped = line.strip()
                    class_brace_depth += stripped.count('{')
                    class_brace_depth -= stripped.count('}')

                    if re.match(r'^(public|private|protected)\s*:\s*$', stripped):
                        prev_access_specifier_line = lines[i]
                        i += 1
                        last_was_decl = False
                        continue

                    if in_function_body > 0:
                        in_function_body += stripped.count('{')
                        in_function_body -= stripped.count('}')
                        output.append(lines[i])
                        if in_function_body == 0:
                            prev_access_specifier_line = None
                        i += 1
                        continue

                    func_match = self._match_function(stripped, lines, i)
                    if func_match:
                        func_decl, end_idx = func_match
                        indent = self._get_indent(lines[i])
                        ret_type = func_decl.get('return_type', '').strip()
                        ret_type = re.sub(r'\b(?:virtual|inline|explicit|constexpr|static|friend|mutable|volatile|register|extern|thread_local|auto|typename|override|final)\b', '', ret_type)
                        ret_type = re.sub(r'\s+', ' ', ret_type).strip()
                        func_decl['return_type'] = ret_type

                        if prev_access_specifier_line:
                            output.append(prev_access_specifier_line)
                            prev_access_specifier_line = None

                        doc_comment = self._generate_function_comment(func_decl, indent)
                        for line_comment in doc_comment:
                            output.append(line_comment.rstrip('\n') + '\n')
                        for idx in range(i, end_idx + 1):
                            output.append(lines[idx])
                        if '{' in ''.join(lines[i:end_idx+1]):
                            in_function_body = 1
                        i = end_idx + 1
                        last_was_decl = True
                        continue

                    var_match = self._match_variable(stripped, lines, i)
                    if var_match:
                        var_decl, end_idx = var_match
                        indent = self._get_indent(lines[i])
                        if output and output[-1].strip():
                            output.append('\n')
                        if var_decl.get('type'):
                            for spec in ('public:', 'private:', 'protected:'):
                                if var_decl['type'].startswith(spec):
                                    var_decl['type'] = var_decl['type'][len(spec):].strip()
                        doc_comment = self._generate_variable_comment(var_decl, indent)
                        if doc_comment:
                            output.extend(doc_comment)
                        for idx in range(i, end_idx + 1):
                            output.append(lines[idx])
                        output.append('\n')
                        i = end_idx + 1
                        last_was_decl = True
                        continue

                    if class_brace_depth == 0:
                        inside_class = False
                        self.current_class = None
                        output.append(lines[i])
                        output.append('\n')
                        i += 1
                        last_was_decl = True
                        break

                    output.append(lines[i])
                    i += 1
                    last_was_decl = False

                continue

            # Handle function definitions (outside class) - common in .cpp files
            func_match = self._match_function(stripped, lines, i)
            if func_match:
                func_decl, end_idx = func_match
                indent = self._get_indent(lines[i])
                if output and output[-1].strip():
                    output.append('\n')
                doc_comment = self._generate_function_comment(func_decl, indent)
                output.extend(doc_comment)
                for idx in range(i, end_idx + 1):
                    output.append(lines[idx])
                output.append('\n')
                i = end_idx + 1
                last_was_decl = True
                continue

            # Handle enum declaration
            enum_match = re.match(r'enum\s+(?:class\s+)?(\w+)\s*(?::\s*\w+)?\s*\{', stripped)
            if enum_match:
                indent = self._get_indent(lines[i])
                if output and output[-1].strip():
                    output.append('\n')
                doc_comment = self._generate_enum_comment(enum_match.group(1), indent)
                output.extend(doc_comment)
                output.append(lines[i])
                output.append('\n')
                i += 1
                last_was_decl = True
                continue

            # Handle closing braces for namespace/class
            if stripped == '}' and (self.current_class or self.current_namespace):
                if ';' in stripped:
                    if self.current_class:
                        self.current_class = None
                    else:
                        self.current_namespace = None
                output.append(lines[i])
                output.append('\n')
                i += 1
                last_was_decl = True
                continue

            # Regular line - just add it
            output.append(lines[i])
            last_was_decl = False
            i += 1

        # Remove trailing blank lines for clean output
        while output and not output[-1].strip():
            output.pop()
        output.append('\n')
        return output

    def _parse_test_file(self, lines: List[str]) -> List[str]:
        """
        Parse a test file with specialized handling for test cases.

        Args:
            lines: Lines from the test file

        Returns:
            List of lines with Doxygen comments for test cases
        """
        output = []
        i = 0

        while i < len(lines):
            line = lines[i].rstrip('\n')
            stripped = line.strip()

            # Skip empty lines
            if not stripped:
                output.append(lines[i])
                i += 1
                continue

            # Skip existing Doxygen comments
            if stripped.startswith('/**') or stripped.startswith('///') or stripped.startswith('/*!'):
                while i < len(lines) and '*/' not in lines[i]:
                    output.append(lines[i])
                    i += 1
                if i < len(lines):
                    output.append(lines[i])
                    i += 1
                continue

            # Try to parse test case
            test_case = self.test_analyzer.parse_test_case(lines, i, self.detected_framework)
            if test_case:
                test_info, end_idx = test_case
                indent = self._get_indent(lines[i])

                # Generate test case comment
                if output and output[-1].strip():
                    output.append('\n')

                doc_comment = self._generate_test_case_comment(test_info, indent)
                output.extend(doc_comment)

                # Add the test case lines
                for idx in range(i, end_idx + 1):
                    output.append(lines[idx])

                output.append('\n')
                i = end_idx + 1
                continue

            # Regular line
            output.append(lines[i])
            i += 1

        # Remove trailing blank lines
        while output and not output[-1].strip():
            output.pop()
        output.append('\n')
        return output

    def _generate_test_case_comment(self, test_info: TestInfo, indent: str = "") -> List[str]:
        """
        Generate Doxygen comment for a test case.

        Args:
            test_info: Information about the test case
            indent: Indentation to use

        Returns:
            List of comment lines
        """
        comment = [f'{indent}/**\n']

        # Brief description
        description = self.test_analyzer.generate_test_description(test_info)
        comment.append(f'{indent} * @brief {description}\n')
        comment.append(f'{indent} *\n')

        # Test details
        comment.append(f'{indent} * @details\n')

        # Test suite/fixture
        if test_info.test_suite:
            suite_label = 'Test Suite' if test_info.framework == 'gtest' else 'Test Category'
            comment.append(f'{indent} * {suite_label}: {test_info.test_suite}\n')

        if test_info.fixture_class:
            comment.append(f'{indent} * Test Fixture: {test_info.fixture_class}\n')

        # Framework
        framework_names = {
            'gtest': 'Google Test',
            'catch2': 'Catch2',
            'doctest': 'doctest',
            'boost': 'Boost.Test'
        }
        comment.append(f'{indent} * Framework: {framework_names.get(test_info.framework, test_info.framework)}\n')

        # Coverage analysis
        coverage = self.test_analyzer.analyze_test_coverage(test_info)
        if coverage:
            comment.append(f'{indent} *\n')
            comment.append(f'{indent} * Test Coverage:\n')
            for point in coverage:
                comment.append(f'{indent} * - {point}\n')

        # Test type
        if test_info.test_type:
            comment.append(f'{indent} *\n')
            comment.append(f'{indent} * @test {test_info.test_type}\n')

        comment.append(f'{indent} */\n')
        return comment
