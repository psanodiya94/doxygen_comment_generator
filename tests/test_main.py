import unittest
import os
import sys
import tempfile
import shutil
from unittest.mock import patch, MagicMock, mock_open
from io import StringIO

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from generator.main import main

class TestMain(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(lambda: shutil.rmtree(self.temp_dir))
        
        # Create a sample C++ header file
        self.test_header = os.path.join(self.temp_dir, "test.h")
        with open(self.test_header, 'w') as f:
            f.write("class Test {};\n")

        # Create a sample test file
        self.test_cpp = os.path.join(self.temp_dir, "test.cpp")
        with open(self.test_cpp, 'w') as f:
            f.write("#include <gtest/gtest.h>\nTEST(Suite, Case) {}\n")

    def test_main_input_file(self):
        """Test processing a single input file."""
        with patch('sys.argv', ['script', '-f', self.test_header]):
            with patch('sys.stdout', new=StringIO()) as fake_out:
                main()
                output = fake_out.getvalue()
                self.assertIn("Doxygen comments added", output)

    def test_main_dry_run(self):
        """Test dry run mode."""
        with patch('sys.argv', ['script', '-f', self.test_header, '--dry-run']):
            with patch('sys.stdout', new=StringIO()) as fake_out:
                main()
                output = fake_out.getvalue()
                self.assertIn("/**", output)
                self.assertIn("@brief", output)

    def test_main_directory_mode(self):
        """Test processing a directory."""
        with patch('sys.argv', ['script', '-d', self.temp_dir]):
            with patch('sys.stdout', new=StringIO()) as fake_out:
                main()
                output = fake_out.getvalue()
                self.assertIn("Processing Results", output)
                self.assertIn("succeeded", output)

    def test_main_project_mode(self):
        """Test processing a project."""
        # Create project structure
        os.makedirs(os.path.join(self.temp_dir, "include"))
        os.makedirs(os.path.join(self.temp_dir, "src"))
        shutil.copy(self.test_header, os.path.join(self.temp_dir, "include", "test.h"))
        
        with patch('sys.argv', ['script', '-p', self.temp_dir]):
            with patch('sys.stdout', new=StringIO()) as fake_out:
                main()
                output = fake_out.getvalue()
                self.assertIn("Processing project", output)
                self.assertIn("Total:", output)

    def test_main_enhance_existing(self):
        """Test enhancing existing comments."""
        with patch('sys.argv', ['script', '-f', self.test_header, '--enhance-existing']):
            with patch('sys.stdout', new=StringIO()) as fake_out:
                main()
                output = fake_out.getvalue()
                self.assertIn("Enhanced existing Doxygen comments", output)

    def test_main_output_file(self):
        """Test specifying an output file."""
        output_file = os.path.join(self.temp_dir, "output.h")
        with patch('sys.argv', ['script', '-f', self.test_header, '-o', output_file]):
            main()
            self.assertTrue(os.path.exists(output_file))

    def test_main_no_input(self):
        """Test error when no input is provided."""
        with patch('sys.argv', ['script']):
            with patch('sys.stdout', new=StringIO()) as fake_out:
                with self.assertRaises(SystemExit) as cm:
                    main()
                self.assertEqual(cm.exception.code, 1)

    def test_main_invalid_file(self):
        """Test error with invalid file path."""
        with patch('sys.argv', ['script', '-f', 'nonexistent.h']):
            with patch('sys.stdout', new=StringIO()) as fake_out:
                with self.assertRaises(SystemExit) as cm:
                    main()
                self.assertEqual(cm.exception.code, 1)

    def test_main_unsupported_file_type(self):
        """Test error with unsupported file type."""
        unsupported_file = os.path.join(self.temp_dir, "test.txt")
        with open(unsupported_file, 'w') as f:
            f.write("test")
            
        with patch('sys.argv', ['script', '-f', unsupported_file]):
            with patch('sys.stdout', new=StringIO()) as fake_out:
                with self.assertRaises(SystemExit) as cm:
                    main()
                self.assertEqual(cm.exception.code, 1)

    def test_main_test_file_detection(self):
        """Test detection of test files."""
        with patch('sys.argv', ['script', '-f', self.test_cpp]):
            with patch('sys.stdout', new=StringIO()) as fake_out:
                main()
                output = fake_out.getvalue()
                self.assertIn("Detected test file", output)

    def test_main_recursive_directory(self):
        """Test recursive directory processing."""
        nested_dir = os.path.join(self.temp_dir, "nested")
        os.makedirs(nested_dir)
        shutil.copy(self.test_header, os.path.join(nested_dir, "nested_test.h"))
        
        with patch('sys.argv', ['script', '-d', self.temp_dir, '--recursive']):
            with patch('sys.stdout', new=StringIO()) as fake_out:
                main()
                output = fake_out.getvalue()
                self.assertIn("Processing Results", output)
                self.assertIn("nested", output)

    def test_main_no_recursive(self):
        """Test non-recursive directory processing."""
        nested_dir = os.path.join(self.temp_dir, "nested")
        os.makedirs(nested_dir)
        shutil.copy(self.test_header, os.path.join(nested_dir, "nested_test.h"))
        
        with patch('sys.argv', ['script', '-d', self.temp_dir, '--no-recursive']):
            with patch('sys.stdout', new=StringIO()) as fake_out:
                main()
                output = fake_out.getvalue()
                self.assertIn("Processing Results", output)
                self.assertNotIn("nested", output)

    def test_main_gui_mode(self):
        """Test GUI mode."""
        with patch('sys.argv', ['script', '--gui', '--input_file', 'test.h']):
            # Create a mock module for each tkinter submodule
            mock_tkinter = MagicMock()
            mock_filedialog = MagicMock()
            mock_messagebox = MagicMock()
            mock_scrolledtext = MagicMock()

            # Set up specific mocks needed by the GUI
            mock_root = MagicMock()
            mock_tkinter.Tk.return_value = mock_root
            mock_filedialog.askopenfilename.return_value = ""
            mock_filedialog.asksaveasfilename.return_value = ""
            mock_scrolledtext.ScrolledText = MagicMock()

            # Make mainloop raise SystemExit to prevent continuing after GUI
            mock_root.mainloop.side_effect = SystemExit(0)

            # Mock all required tkinter components
            with patch.dict('sys.modules', {
                'tkinter': mock_tkinter,
                'tkinter.filedialog': mock_filedialog,
                'tkinter.messagebox': mock_messagebox,
                'tkinter.scrolledtext': mock_scrolledtext
            }), patch('sys.stdout', new=StringIO()):
                with self.assertRaises(SystemExit) as cm:
                    main()
                self.assertEqual(cm.exception.code, 0)
                # Verify that Tk was initialized and mainloop was called
                mock_tkinter.Tk.assert_called_once()

    def test_main_gui_no_tkinter(self):
        """Test GUI mode when Tkinter is not available."""
        with patch('sys.argv', ['script', '--gui']):
            with patch('sys.stdout', new=StringIO()) as fake_out:
                with patch.dict('sys.modules', {'tkinter': None}):
                    with self.assertRaises(SystemExit) as cm:
                        main()
                    self.assertEqual(cm.exception.code, 5)
                    output = fake_out.getvalue()
                    self.assertIn("Tkinter is not installed", output)

    def test_output_file_error(self):
        """Test error when writing to output file."""
        with patch('sys.argv', ['script', '-f', self.test_header, '-o', '/nonexistent/output.h']):
            with patch('sys.stdout', new=StringIO()) as fake_out:
                with self.assertRaises(SystemExit) as cm:
                    main()
                self.assertEqual(cm.exception.code, 4)
                self.assertIn("Error writing to output file", fake_out.getvalue())

    def test_directory_processor_error(self):
        """Test error handling in directory processor."""
        with patch('sys.argv', ['script', '-d', self.temp_dir]):
            with patch('sys.stdout', new=StringIO()) as fake_out:
                with patch('generator.directory_processor.DirectoryProcessor.process_directory', 
                         side_effect=Exception("Test error")):
                    with self.assertRaises(SystemExit) as cm:
                        main()
                    self.assertEqual(cm.exception.code, 3)
                    self.assertIn("Error processing directory", fake_out.getvalue())

    def test_import_error(self):
        """Test error handling when imports fail."""
        with patch('sys.argv', ['script', '-f', self.test_header]):
            with patch('sys.stdout', new=StringIO()) as fake_out:
                with patch.dict('sys.modules', {'generator.header.header_generator': None}):
                    with self.assertRaises(SystemExit) as cm:
                        main()
                    self.assertEqual(cm.exception.code, 2)
                    self.assertIn("Error importing generator modules", fake_out.getvalue())

    def test_processing_file_error(self):
        """Test error when processing file fails."""
        with patch('sys.argv', ['script', '-f', self.test_header]):
            with patch('sys.stdout', new=StringIO()) as fake_out:
                with patch('generator.cpp.cpp_generator.CppSourceGenerator.parse_source',
                         side_effect=Exception("Parse error")):
                    with self.assertRaises(SystemExit) as cm:
                        main()
                    self.assertEqual(cm.exception.code, 3)
                    self.assertIn("Error processing file", fake_out.getvalue())

    def test_all_header_extensions(self):
        """Test all supported header file extensions."""
        extensions = ['.h', '.hpp', '.hh', '.hxx']
        for ext in extensions:
            test_file = os.path.join(self.temp_dir, f"test{ext}")
            with open(test_file, 'w') as f:
                f.write("class Test {};")

            with patch('sys.argv', ['script', '-f', test_file]):
                with patch('sys.stdout', new=StringIO()) as fake_out:
                    main()
                    output = fake_out.getvalue()
                    self.assertIn("Doxygen comments added", output)

    def test_all_source_extensions(self):
        """Test all supported C++ source file extensions."""
        extensions = ['.cpp', '.cc', '.cxx', '.c++']
        for ext in extensions:
            test_file = os.path.join(self.temp_dir, f"test{ext}")
            with open(test_file, 'w') as f:
                f.write("int main() { return 0; }")

            with patch('sys.argv', ['script', '-f', test_file]):
                with patch('sys.stdout', new=StringIO()) as fake_out:
                    main()
                    output = fake_out.getvalue()
                    self.assertIn("Doxygen comments added", output)

    def test_dry_run_directory_mode(self):
        """Test dry run in directory mode."""
        with patch('sys.argv', ['script', '-d', self.temp_dir, '--dry-run']):
            with patch('sys.stdout', new=StringIO()) as fake_out:
                main()
                output = fake_out.getvalue()
                self.assertIn("Processing Results", output)

    def test_project_mode_dry_run(self):
        """Test dry run in project mode."""
        os.makedirs(os.path.join(self.temp_dir, "include"))
        os.makedirs(os.path.join(self.temp_dir, "src"))
        shutil.copy(self.test_header, os.path.join(self.temp_dir, "include", "test.h"))

        with patch('sys.argv', ['script', '-p', self.temp_dir, '--dry-run']):
            with patch('sys.stdout', new=StringIO()) as fake_out:
                main()
                output = fake_out.getvalue()
                self.assertIn("Processing project", output)

    def test_directory_with_output_dir(self):
        """Test directory processing with output directory."""
        output_dir = os.path.join(self.temp_dir, "output")
        with patch('sys.argv', ['script', '-d', self.temp_dir, '-o', output_dir]):
            with patch('sys.stdout', new=StringIO()):
                main()
                # Output directory should be created
                self.assertTrue(os.path.exists(output_dir))

    def test_project_with_output_dir(self):
        """Test project processing with output directory."""
        os.makedirs(os.path.join(self.temp_dir, "include"))
        shutil.copy(self.test_header, os.path.join(self.temp_dir, "include", "test.h"))
        output_dir = os.path.join(self.temp_dir, "output")

        with patch('sys.argv', ['script', '-p', self.temp_dir, '-o', output_dir]):
            with patch('sys.stdout', new=StringIO()):
                main()
                # Output directory should be created
                self.assertTrue(os.path.exists(output_dir))


if __name__ == '__main__':
    unittest.main()
