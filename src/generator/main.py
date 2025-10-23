#!/usr/bin/env python3

import sys
import os
import argparse

def main():
    # Add src to sys.path for imports regardless of how the script is run
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))


    parser = argparse.ArgumentParser(
        description="Generate Doxygen comments for C++ header and source files."
    )
    parser.add_argument("-f", "--input_file", help="Path to the input C++ file (header or source)")
    parser.add_argument("-d", "--directory", help="Path to directory containing C++ files to process")
    parser.add_argument("-p", "--project", help="Path to project root (will process include/ and src/ directories)")
    parser.add_argument("-o", "--output", help="Path to output file or directory (default: overwrite in place)")
    parser.add_argument("--dry-run", action="store_true", help="Print output to console instead of writing to file")
    parser.add_argument("--gui", action="store_true", help="Launch a simple GUI for file upload and Doxygen generation")
    parser.add_argument("--test-mode", action="store_true", help="Enable specialized test case documentation mode")
    parser.add_argument("--enhance-existing", action="store_true", help="Enhance existing Doxygen comments instead of skipping them")
    parser.add_argument("--recursive", action="store_true", default=True, help="Process directories recursively (default: True)")
    parser.add_argument("--no-recursive", dest="recursive", action="store_false", help="Don't process directories recursively")


    args = parser.parse_args()

    try:
        from generator.header.header_generator import HeaderDoxygenGenerator
        from generator.cpp.cpp_generator import CppSourceGenerator
        from generator.directory_processor import DirectoryProcessor
    except ImportError as e:
        print("Error importing generator modules:", e)
        sys.exit(2)

    if args.gui:
        # Check for Tkinter availability
        try:
            import tkinter as tk
            from tkinter import filedialog, messagebox, scrolledtext
        except ImportError:
            print("Error: Tkinter is not installed. Please install it to use the GUI option.\nOn Ubuntu/Debian: sudo apt-get install python3-tk")
            sys.exit(5)
        def run_gui():
            root = tk.Tk()
            root.title("Doxygen Header Comment Generator")
            root.geometry("700x500")

            def select_file():
                file_path = filedialog.askopenfilename(
                    filetypes=[
                        ("C++ Files", "*.h *.hpp *.hh *.hxx *.cpp *.cc *.cxx *.c++"),
                        ("Header Files", "*.h *.hpp *.hh *.hxx"),
                        ("Source Files", "*.cpp *.cc *.cxx *.c++"),
                        ("All Files", "*.*")
                    ]
                )
                if file_path:
                    entry_file.delete(0, tk.END)
                    entry_file.insert(0, file_path)

            def generate_comments():
                file_path = entry_file.get()
                if not file_path or not os.path.isfile(file_path):
                    messagebox.showerror("Error", "Please select a valid C++ file.")
                    return
                ext = os.path.splitext(file_path)[1].lower()
                if ext not in [".h", ".hpp", ".hh", ".hxx", ".cpp", ".cc", ".cxx", ".c++"]:
                    messagebox.showerror("Error", "Unsupported file type. Only C++ header and source files are supported.")
                    return
                try:
                    # Use CppSourceGenerator for all file types (handles both headers and sources)
                    generator = CppSourceGenerator()
                    output_lines = generator.parse_source(file_path)
                    text_output.delete(1.0, tk.END)
                    text_output.insert(tk.END, ''.join(output_lines))
                except Exception as e:
                    messagebox.showerror("Error", f"Error processing file: {e}")

            def save_output():
                content = text_output.get(1.0, tk.END)
                if not content.strip():
                    messagebox.showinfo("Info", "No output to save.")
                    return
                save_path = filedialog.asksaveasfilename(
                    defaultextension=".h",
                    filetypes=[
                        ("C++ Files", "*.h *.hpp *.hh *.hxx *.cpp *.cc *.cxx *.c++"),
                        ("Header Files", "*.h *.hpp *.hh *.hxx"),
                        ("Source Files", "*.cpp *.cc *.cxx *.c++"),
                        ("All Files", "*.*")
                    ]
                )
                if save_path:
                    with open(save_path, 'w') as f:
                        f.write(content)
                    messagebox.showinfo("Saved", f"Output saved to {save_path}")

            frame = tk.Frame(root)
            frame.pack(pady=10)
            tk.Label(frame, text="C++ File:").pack(side=tk.LEFT)
            entry_file = tk.Entry(frame, width=50)
            entry_file.pack(side=tk.LEFT, padx=5)
            tk.Button(frame, text="Browse", command=select_file).pack(side=tk.LEFT)
            tk.Button(frame, text="Generate", command=generate_comments).pack(side=tk.LEFT, padx=5)
            tk.Button(frame, text="Save Output", command=save_output).pack(side=tk.LEFT)

            text_output = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=80, height=25)
            text_output.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

            root.mainloop()

        run_gui()
    else:
        # Check for directory or project mode
        if args.directory or args.project:
            # Directory processing mode
            processor = DirectoryProcessor(enhance_existing=args.enhance_existing)

            try:
                if args.project:
                    results = processor.process_project(
                        args.project,
                        output_dir=args.output,
                        dry_run=args.dry_run
                    )
                else:  # args.directory
                    results = processor.process_directory(
                        args.directory,
                        output_dir=args.output,
                        dry_run=args.dry_run,
                        recursive=args.recursive
                    )

                processor.print_results(results)

            except Exception as e:
                print(f"Error processing directory: {e}")
                sys.exit(3)

            return

        if not args.input_file:
            print("Input file, directory, or project root is required unless using --gui.")
            print("Use -f for single file, -d for directory, or -p for project root.")
            sys.exit(1)

    input_file = args.input_file
    if not os.path.isfile(input_file):
        print(f"Input file '{input_file}' does not exist.")
        sys.exit(1)

    ext = os.path.splitext(input_file)[1].lower()
    if ext not in [".h", ".hpp", ".hh", ".hxx", ".cpp", ".cc", ".cxx", ".c++"]:
        print("Unsupported file type. Only C++ header and source files are supported.")
        sys.exit(1)

    try:
        # Use CppSourceGenerator for all file types (handles both headers and sources)
        generator = CppSourceGenerator(enhance_existing=args.enhance_existing)
        output_lines = generator.parse_source(input_file)

        # Display information about detected test framework
        if generator.is_test_file:
            print(f"Detected test file using {generator.detected_framework} framework")

        if args.enhance_existing:
            print("Enhanced existing Doxygen comments")
    except Exception as e:
        print(f"Error processing file: {e}")
        sys.exit(3)

    # Output logic
    if args.dry_run:
        print(''.join(output_lines))
        return

    # If output file is specified, use it; otherwise, overwrite the input file
    if args.output:
        output_file = args.output
    else:
        output_file = input_file

    try:
        with open(output_file, 'w') as f:
            f.writelines(output_lines)
        print(f"Doxygen comments added to {output_file}")
    except Exception as e:
        print(f"Error writing to output file: {e}")
        sys.exit(4)

if __name__ == '__main__':
    main()