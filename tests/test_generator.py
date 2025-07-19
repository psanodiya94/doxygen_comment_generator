import unittest
import sys
import os
from unittest.mock import patch, mock_open

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from generator.header.header_generator import HeaderDoxygenGenerator
from generator.cplusplus.cplusplus_generator import CPlusPlusDoxygenGenerator

class TestHeaderDoxygenGenerator(unittest.TestCase):
    def setUp(self):
        self.generator = HeaderDoxygenGenerator()

    @patch("builtins.open", new_callable=mock_open, read_data="    class Test {};")
    def test_parse_header_class(self, mock_file):
        result = self.generator.parse_header("test.h")
        self.assertTrue(any("/**" in line for line in result))
        self.assertTrue(any("class Test" in line for line in result))
        comment_lines = [line for line in result if "/**" in line or "* @" in line]
        self.assertTrue(all(line.startswith("    ") for line in comment_lines))

    @patch("builtins.open", new_callable=mock_open, read_data="namespace Foo {\nclass Bar {};\n}")
    def test_parse_header_namespace(self, mock_file):
        result = self.generator.parse_header("test.h")
        self.assertIn("namespace Foo {", "".join(result))
        self.assertIn("class Bar", "".join(result))

    @patch("builtins.open", new_callable=mock_open, read_data="enum class Color { RED, GREEN };")
    def test_parse_header_enum(self, mock_file):
        result = self.generator.parse_header("test.h")
        self.assertTrue(any("@brief Enum Color" in line for line in result))

    @patch("builtins.open", new_callable=mock_open, read_data="int value;")
    def test_parse_header_variable(self, mock_file):
        result = self.generator.parse_header("test.h")
        self.assertTrue(any("@brief Variable value" in line for line in result))

    @patch("builtins.open", new_callable=mock_open, read_data="int add(int a, int b);")
    def test_parse_header_function(self, mock_file):
        result = self.generator.parse_header("test.h")
        self.assertTrue(any("@brief Add" in line or "@brief add" in line for line in result))
        self.assertTrue(any("@param a" in line for line in result))
        self.assertTrue(any("@param b" in line for line in result))
        self.assertTrue(any("@return int" in line for line in result))

    def test_generate_class_comment(self):
        comment = self.generator._generate_class_comment("Test", "class", indent="    ")
        self.assertIn("@brief class Test", comment[1])
        self.assertTrue(all(line.startswith("    ") for line in comment))

    def test_generate_function_comment(self):
        func_info = {
            "return_type": "int",
            "name": "testFunction",
            "params": [("int", "param1"), ("float", "param2")],
            "noexcept": False,
            "throw": None,
            "static": False,
            "const": False,
        }
        comment = self.generator._generate_function_comment(func_info, indent="  ")
        self.assertIn("@brief Test function", comment[1])
        self.assertIn("@param param1", "".join(comment))
        self.assertIn("@return int", "".join(comment))
        self.assertTrue(all(line.startswith("  ") or line == '\n' for line in comment))

    def test_generate_enum_comment(self):
        comment = self.generator._generate_enum_comment("TestEnum", indent="\t")
        self.assertIn("@brief Enum TestEnum", comment[1])
        self.assertTrue(all(line.startswith("\t") for line in comment))

    def test_generate_variable_comment(self):
        var_info = {
            "type": "int",
            "name": "testVar",
            "static": False,
            "constexpr": False,
            "mutable": False,
            "full_decl": "int testVar;"
        }
        comment = self.generator._generate_variable_comment(var_info, indent="  ")
        self.assertIn("@brief Variable testVar", comment[1])
        self.assertTrue(all(line.startswith("  ") or line == '\n' for line in comment))

    def test_match_function(self):
        lines = ["    int testFunction(int param1, float param2);"]
        result = self.generator._match_function(lines[0].strip(), lines, 0)
        self.assertIsNotNone(result)
        self.assertEqual(result[0]["name"], "testFunction")

    def test_match_variable(self):
        lines = ["    int testVar;"]
        result = self.generator._match_variable(lines[0].strip(), lines, 0)
        self.assertIsNotNone(result)
        self.assertEqual(result[0]["name"], "testVar")

    def test_generate_brief_description(self):
        self.assertEqual(self.generator._generate_brief_description("getValue"), "Gets the  value")
        self.assertEqual(self.generator._generate_brief_description("set_value"), "Sets the  value")
        self.assertEqual(self.generator._generate_brief_description("isEnabled"), "Checks if  enabled")
        self.assertEqual(self.generator._generate_brief_description("customFunc"), "Custom func")

    @patch("builtins.open", new_callable=mock_open, read_data="""
    class SettingsManager {
    public:
        static constexpr int MAX_SETTINGS = 100;
    };
    """)
    def test_variable_comment_not_before_class(self, mock_file):
        result = self.generator.parse_header("test.h")
        # The comment should not be before the class, but before MAX_SETTINGS
        for idx, line in enumerate(result):
            if "class SettingsManager" in line:
                # Next non-empty line should NOT be a doxygen comment
                next_idx = idx + 1
                while next_idx < len(result) and result[next_idx].strip() == "":
                    next_idx += 1
                self.assertFalse("/**" in result[next_idx])
            if "MAX_SETTINGS" in line:
                # The previous line should be the doxygen comment
                self.assertTrue("/**" in result[idx-1])
                self.assertIn("@brief Variable MAX_SETTINGS", "".join(result[idx-1:idx+2]))
                break
        else:
            self.fail("MAX_SETTINGS not found in output")

class TestCPlusPlusDoxygenGenerator(unittest.TestCase):
    def setUp(self):
        self.generator = CPlusPlusDoxygenGenerator()

    @patch("builtins.open", new_callable=mock_open, read_data="int foo() {\n    return 1;\n}\n")
    def test_parse_source_function(self, mock_file):
        result = self.generator.parse_source("test.cpp")
        self.assertTrue(any("@brief foo function" in line for line in result))

    @patch("builtins.open", new_callable=mock_open, read_data="int main() {\n    return 0;\n}\n")
    def test_parse_source_main(self, mock_file):
        result = self.generator.parse_source("main.cpp")
        self.assertTrue(any("@brief main function" in line for line in result))

    def test_get_indent(self):
        self.assertEqual(self.generator._get_indent("    int foo() {"), "    ")
        self.assertEqual(self.generator._get_indent("\tint foo() {"), "\t")

if __name__ == "__main__":
    unittest.main()