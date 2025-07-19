# doxygen_comment_generator

## Project Description

**doxygen_comment_generator** is a Python tool that automatically generates Doxygen-style comments for C++ header (`.h`, `.hpp`, etc.) files. It analyzes your code and inserts well-formatted Doxygen comments for classes, functions, enums, and variables, helping you maintain high-quality documentation with minimal effort.

## Features

-- Supports C++ header files

- Preserves code indentation in generated comments
- Easily extensible for other C/C++ file types
- Simple command-line interface

## Installation

1. **Clone the repository:**

   ```sh
   git clone https://github.com/yourusername/doxygen_comment_generator.git
   cd doxygen_comment_generator
   ```

2. **(Recommended) Create and activate a virtual environment:**

   ```sh
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

   *(This keeps dependencies isolated and makes it easy to manage your Python environment.)*

## GUI Requirements

If you want to use the `--gui` option, your Python must have Tkinter installed (it is included by default on most systems, but not all minimal Linux installs). If you see an error about Tkinter missing, install it with:

```sh
# On Ubuntu/Debian:
sudo apt-get install python3-tk
# On Fedora:
sudo dnf install python3-tkinter
# On Arch:
sudo pacman -S tk
```

If you use a virtual environment, Tkinter must be available in the system Python used to create the venv.

1. **Install dependencies:**

   ```sh
   pip install -r requirements.txt
   ```

   *(If `requirements.txt` does not exist, you can skip this step if there are no extra dependencies.)*

## Usage

To generate Doxygen comments for a header file, run:

```sh
python src/generator/main.py -f <path_to_your_header_file>
```

**Example:**

```sh
python src/generator/main.py -f example.h
```

## Command-Line Options

The script supports the following options:

- `-f <path_to_your_header_file>`: Path to the C++ header file to process (required).
- `-o <path_to_your_output_file>`: Path to the C++ header file where you want to store if not inplace.
- `--dry-run`: Print output to console instead of writing to file.
- `--gui`: Launches a simple graphical interface for file selection and comment generation (requires Tkinter).
- `-h`, `--help`: Show help message and exit.

**Example usage:**

```sh
python src/generator/main.py --gui
```

```sh
python src/generator/main.py -h
```

The script will update the file contents with generated Doxygen comments.

## Running Tests

To run the unit tests:

```sh
python -m unittest discover -s tests
```

or

```sh
python -m unittest tests.test_generator
```

## Notes

- Make sure you have Python 3.7+ installed.
- For best results, use the tool on well-formatted C++ code.
- The tool is designed for C++ header files only.
