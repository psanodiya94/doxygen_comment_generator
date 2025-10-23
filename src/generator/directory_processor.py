"""
Directory processor for batch processing C++ files.
Recursively processes all C++ files in specified directories.
"""

import os
from pathlib import Path
from typing import List, Dict, Tuple
from .cpp.cpp_generator import CppSourceGenerator


class DirectoryProcessor:
    """
    Processes directories containing C++ source and header files.
    Handles recursive traversal and batch documentation generation.
    """

    # Supported C++ file extensions
    CPP_EXTENSIONS = {'.h', '.hpp', '.hh', '.hxx', '.cpp', '.cc', '.cxx', '.c++'}

    def __init__(self, enhance_existing: bool = False):
        """
        Initialize the DirectoryProcessor.

        Args:
            enhance_existing: If True, enhance existing Doxygen comments instead of skipping them
        """
        self.enhance_existing = enhance_existing
        self.generator = CppSourceGenerator()
        if enhance_existing:
            self.generator.skip_existing_comments = False

    def find_cpp_files(self, directory: str, recursive: bool = True) -> List[str]:
        """
        Find all C++ files in a directory.

        Args:
            directory: Path to the directory to search
            recursive: If True, search recursively in subdirectories

        Returns:
            List of absolute paths to C++ files
        """
        cpp_files = []
        directory_path = Path(directory).resolve()

        if not directory_path.exists():
            raise ValueError(f"Directory does not exist: {directory}")

        if not directory_path.is_dir():
            raise ValueError(f"Path is not a directory: {directory}")

        if recursive:
            # Recursively find all C++ files
            for root, dirs, files in os.walk(directory_path):
                # Skip common non-source directories
                dirs[:] = [d for d in dirs if d not in {'.git', '.svn', 'build', 'cmake-build-debug', 'cmake-build-release', '__pycache__', '.venv', 'venv'}]

                for file in files:
                    if Path(file).suffix.lower() in self.CPP_EXTENSIONS:
                        cpp_files.append(str(Path(root) / file))
        else:
            # Only search the top-level directory
            for file in directory_path.iterdir():
                if file.is_file() and file.suffix.lower() in self.CPP_EXTENSIONS:
                    cpp_files.append(str(file))

        return sorted(cpp_files)

    def process_directory(self, directory: str, output_dir: str = None, dry_run: bool = False, recursive: bool = True) -> Dict[str, Tuple[bool, str]]:
        """
        Process all C++ files in a directory.

        Args:
            directory: Path to the directory to process
            output_dir: Optional output directory (if None, files are modified in place)
            dry_run: If True, don't write files, just return what would be done
            recursive: If True, process subdirectories recursively

        Returns:
            Dictionary mapping file paths to (success, message) tuples
        """
        results = {}
        cpp_files = self.find_cpp_files(directory, recursive=recursive)

        if not cpp_files:
            return {'_info': (False, f"No C++ files found in {directory}")}

        print(f"Found {len(cpp_files)} C++ file(s) to process")

        for file_path in cpp_files:
            try:
                # Process the file
                output_lines = self.generator.parse_source(file_path)

                if dry_run:
                    results[file_path] = (True, "Would be processed (dry run)")
                else:
                    # Determine output path
                    if output_dir:
                        # Recreate directory structure in output_dir
                        rel_path = os.path.relpath(file_path, directory)
                        out_path = os.path.join(output_dir, rel_path)
                        os.makedirs(os.path.dirname(out_path), exist_ok=True)
                    else:
                        # Write in place
                        out_path = file_path

                    # Write the output
                    with open(out_path, 'w') as f:
                        f.writelines(output_lines)

                    framework_info = f" (Test file: {self.generator.detected_framework})" if self.generator.is_test_file else ""
                    results[file_path] = (True, f"Processed successfully{framework_info}")

            except Exception as e:
                results[file_path] = (False, f"Error: {str(e)}")

        return results

    def process_project(self, project_root: str, include_dirs: List[str] = None, src_dirs: List[str] = None,
                       output_dir: str = None, dry_run: bool = False) -> Dict[str, Tuple[bool, str]]:
        """
        Process a C++ project with standard structure (include/ and src/ directories).

        Args:
            project_root: Root directory of the project
            include_dirs: List of include directory names (default: ['include', 'inc', 'includes'])
            src_dirs: List of source directory names (default: ['src', 'source', 'sources'])
            output_dir: Optional output directory
            dry_run: If True, don't write files

        Returns:
            Dictionary mapping file paths to (success, message) tuples
        """
        if include_dirs is None:
            include_dirs = ['include', 'inc', 'includes']
        if src_dirs is None:
            src_dirs = ['src', 'source', 'sources', 'test', 'tests']

        project_path = Path(project_root).resolve()
        if not project_path.exists():
            raise ValueError(f"Project root does not exist: {project_root}")

        results = {}
        dirs_to_process = []

        # Find directories to process
        for dir_name in include_dirs + src_dirs:
            dir_path = project_path / dir_name
            if dir_path.exists() and dir_path.is_dir():
                dirs_to_process.append(str(dir_path))

        if not dirs_to_process:
            return {'_info': (False, f"No standard source directories found in {project_root}. "
                                     f"Looked for: {include_dirs + src_dirs}")}

        print(f"Processing project at: {project_root}")
        print(f"Found directories: {[os.path.basename(d) for d in dirs_to_process]}")

        # Process each directory
        for directory in dirs_to_process:
            dir_results = self.process_directory(directory, output_dir, dry_run, recursive=True)
            results.update(dir_results)

        return results

    def print_results(self, results: Dict[str, Tuple[bool, str]]):
        """
        Print processing results in a readable format.

        Args:
            results: Results dictionary from process_directory or process_project
        """
        success_count = 0
        failure_count = 0

        print("\n" + "="*80)
        print("Processing Results")
        print("="*80)

        for file_path, (success, message) in results.items():
            if file_path == '_info':
                print(f"\nℹ️  {message}")
                continue

            status = "✓" if success else "✗"
            print(f"{status} {file_path}")
            if message and message != "Processed successfully":
                print(f"  → {message}")

            if success:
                success_count += 1
            else:
                failure_count += 1

        print("="*80)
        print(f"Total: {success_count} succeeded, {failure_count} failed")
        print("="*80)
