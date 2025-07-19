#!/usr/bin/env python3
import sys
import os

def print_usage():
    print("Usage: python3 main.py <input_file> [output_file]")
    print("Supported file types: .h, .hpp, .hh, .hxx, .cpp, .cc, .cxx")
    sys.exit(1)

def main():
    # Add src to sys.path for imports regardless of how the script is run
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

    try:
        from generator.header.header_generator import HeaderDoxygenGenerator
        from generator.cplusplus.cplusplus_generator import CPlusPlusDoxygenGenerator
    except ImportError as e:
        print("Error importing generator modules:", e)
        sys.exit(2)

    if len(sys.argv) < 2:
        print_usage()

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else input_file

    if not os.path.isfile(input_file):
        print(f"Input file '{input_file}' does not exist.")
        sys.exit(1)

    ext = os.path.splitext(input_file)[1].lower()

    try:
        if ext in [".h", ".hpp", ".hh", ".hxx"]:
            generator = HeaderDoxygenGenerator()
            output_lines = generator.parse_header(input_file)
        elif ext in [".cpp", ".cc", ".cxx"]:
            generator = CPlusPlusDoxygenGenerator()
            output_lines = generator.parse_source(input_file)
        else:
            print("Unsupported file type.")
            print_usage()
    except Exception as e:
        print(f"Error processing file: {e}")
        sys.exit(3)

    try:
        with open(output_file, 'w') as f:
            f.writelines(output_lines)
        print(f"Doxygen comments added to {output_file}")
    except Exception as e:
        print(f"Error writing to output file: {e}")
        sys.exit(4)

if __name__ == '__main__':
    main()