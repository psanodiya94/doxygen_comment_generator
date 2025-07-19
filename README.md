# doxygen_generator

## Project Description

**doxygen_generator** is a Python tool that automatically generates Doxygen-style comments for C++ header (`.h`, `.hpp`, etc.) and source (`.cpp`, `.cc`, etc.) files. It analyzes your code and inserts well-formatted Doxygen comments for classes, functions, enums, and variables, helping you maintain high-quality documentation with minimal effort.

## Features

- Supports both C++ header and source files
- Preserves code indentation in generated comments
- Easily extensible for other C/C++ file types
- Simple command-line interface

## Installation

1. **Clone the repository:**

   ```sh
   git clone https://github.com/yourusername/doxygen_comment_generator.git
   cd doxygen_comment_generator
   ```

2. **(Optional but recommended) Create and activate a virtual environment:**

   ```sh
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**

   ```sh
   pip install -r requirements.txt
   ```

   *(If `requirements.txt` does not exist, you can skip this step if there are no extra dependencies.)*

## Usage

To generate Doxygen comments for a file, run:

```sh
python src/main.py <path_to_your_cpp_or_header_file>
```

**Examples:**

```sh
python src/main.py example.h
python src/main.py example.cpp
```

The script will print the file contents with generated Doxygen comments to the console.

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
- The tool automatically detects whether the input file is a header or source file and uses
