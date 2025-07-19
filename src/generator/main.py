#!/usr/bin/env python3
import sys
import os
from src.generator.header.header_generator import HeaderDoxygenGenerator
from src.generator.cplusplus.cplusplus_generator import CPlusPlusDoxygenGenerator

def main():
    """
    Entry point for the Doxygen comment generator script.

    Parses command-line arguments to get the input header file and optional output file.
    Uses DoxygenGenerator to parse the header and write the output with Doxygen comments.
    """
    if len(sys.argv) < 2:
        print("Usage: doxygen_generator.py <header_file> [output_file]")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else input_file
    ext = os.path.splitext(input_file)[1].lower()

    if ext in [".h", ".hpp", ".hh", ".hxx"]:
        generator = HeaderDoxygenGenerator()
        output_lines = generator.parse_header(input_file)
    elif ext in [".cpp", ".cc", ".cxx"]:
        generator = CPlusPlusDoxygenGenerator()
        output_lines = generator.parse_source(input_file)
    else:
        print("Unsupported file type.")
        sys.exit(1)

    with open(output_file, 'w') as f:
        f.writelines(output_lines)

    print(f"Doxygen comments added to {output_file}")


if __name__ == '__main__':
    main()