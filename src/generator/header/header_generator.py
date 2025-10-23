import re
from typing import List, Dict, Optional, Tuple


class HeaderDoxygenGenerator:
    def __init__(self, enhance_existing: bool = False):
        """
        Initialize the HeaderDoxygenGenerator.
        Tracks the current class and namespace for context-aware comment generation.

        Args:
            enhance_existing: If True, enhance existing Doxygen comments instead of skipping them
        """
        self.current_class = None
        self.current_namespace = None
        self.enhance_existing = enhance_existing


    def parse_header(self, filename: str) -> List[str]:
        """
        Parse a C++ header file and return lines with added Doxygen comments.

        Args:
            filename (str): Path to the header file.

        Returns:
            List[str]: List of lines with Doxygen comments inserted.
        Raises:
            ValueError: If the file extension is not a supported C++ header file.
        """
        # Only allow header files
        ext = filename.split('.')[-1].lower()
        if ext not in ["h", "hpp", "hh", "hxx"]:
            raise ValueError("Only C++ header files are supported (.h, .hpp, .hh, .hxx)")
        with open(filename, 'r') as f:
            lines = f.readlines()

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

            # Handle existing Doxygen comments
            if stripped.startswith('/**') or stripped.startswith('///') or stripped.startswith('/*!'):
                if not self.enhance_existing:
                    # Skip existing comments (default behavior)
                    while i < len(lines) and '*/' not in lines[i]:
                        output.append(lines[i])
                        i += 1
                    if i < len(lines):
                        output.append(lines[i])
                        i += 1
                    last_was_decl = False
                    continue
                else:
                    # Extract and enhance existing comment
                    existing_comment_lines = []
                    comment_start = i
                    while i < len(lines) and '*/' not in lines[i]:
                        existing_comment_lines.append(lines[i])
                        i += 1
                    if i < len(lines):
                        existing_comment_lines.append(lines[i])
                        i += 1

                    # Keep the existing comment but mark that we should enhance the following declaration
                    output.extend(existing_comment_lines)
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

            # --- Robust multi-line class/struct detection ---
            # Look ahead for class/struct declaration possibly split across lines
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
                # Check if { is present, else look ahead
                if '{' in stripped:
                    class_decl_found = True
                else:
                    j = i + 1
                    while j < len(lines):
                        next_line = lines[j].strip()
                        class_decl_lines.append(lines[j])
                        if next_line.startswith('//') or next_line.startswith('/*'):
                            break  # Don't cross over comments
                        if '{' in next_line:
                            class_decl_found = True
                            break
                        # Stop if we hit a semicolon (forward declaration)
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
                # Process class body
                prev_was_access_specifier = False
                skip_next_comment = False
                in_function_body = 0  # Track if inside a function body (brace depth)
                prev_access_specifier_line = None
                while i < len(lines) and inside_class:
                    line = lines[i].rstrip('\n')
                    stripped = line.strip()
                    class_brace_depth += stripped.count('{')
                    class_brace_depth -= stripped.count('}')
                    # Handle access specifiers - output immediately and mark for next declaration
                    if re.match(r'^(public|private|protected)\s*:\s*$', stripped):
                        output.append(lines[i])
                        prev_access_specifier_line = True  # Mark that we just output an access specifier
                        i += 1
                        last_was_decl = False
                        continue
                    # Track if inside a function body
                    if in_function_body > 0:
                        in_function_body += stripped.count('{')
                        in_function_body -= stripped.count('}')
                        output.append(lines[i])
                        i += 1
                        continue

                    # Skip blank lines and simple lines that can't be function declarations
                    if not stripped or stripped.startswith('//') or stripped.startswith('#'):
                        output.append(lines[i])
                        i += 1
                        continue

                    # Try to match function (declaration or definition)
                    func_match = self._match_function(stripped, lines, i)
                    if func_match:
                        func_decl, end_idx = func_match
                        indent = self._get_indent(lines[i])
                        # Clean up return_type: remove all C++ keywords
                        ret_type = func_decl.get('return_type', '').strip()
                        ret_type = re.sub(r'\b(?:virtual|inline|explicit|constexpr|static|friend|mutable|volatile|register|extern|thread_local|auto|typename|override|final)\b', '', ret_type)
                        ret_type = re.sub(r'\s+', ' ', ret_type).strip()
                        func_decl['return_type'] = ret_type

                        # Generate and output comment with proper indentation
                        doc_comment = self._generate_function_comment(func_decl, indent)
                        for line_comment in doc_comment:
                            output.append(line_comment.rstrip('\n') + '\n')

                        # Output the function declaration
                        for idx in range(i, end_idx + 1):
                            output.append(lines[idx])
                        if '{' in ''.join(lines[i:end_idx+1]):
                            in_function_body = 1
                        i = end_idx + 1
                        last_was_decl = True
                        prev_access_specifier_line = None  # Reset after processing
                        continue
                    # Try to match variable (including those with default values, e.g. int x = 0;)
                    var_match = self._match_variable(stripped, lines, i)
                    if var_match:
                        var_decl, end_idx = var_match
                        indent = self._get_indent(lines[i])
                        # Only add comment if previous line is not an access specifier and not flagged to skip
                        if output and output[-1].strip() and not prev_was_access_specifier and not skip_next_comment:
                            output.append('\n')
                        if not prev_was_access_specifier and not skip_next_comment:
                            # Remove access specifier prefix from type if present
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
                        prev_was_access_specifier = False
                        skip_next_comment = False
                        continue
                    # End of class
                    if class_brace_depth == 0:
                        inside_class = False
                        self.current_class = None
                        output.append(lines[i])
                        output.append('\n')
                        i += 1
                        last_was_decl = True
                        break
                    # Regular line in class
                    output.append(lines[i])
                    i += 1
                    last_was_decl = False
                    prev_was_access_specifier = False
                    skip_next_comment = False
                continue

            # Handle function declarations (outside class)
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

    def _match_function(self, line: str, lines: List[str], start_idx: int) -> Optional[Tuple[Dict, int]]:
        """
        Try to match a function declaration starting at start_idx, including constructors and destructors.

        Args:
            line (str): Current line.
            lines (List[str]): All lines from the file.
            start_idx (int): Index of the current line.

        Returns:
            Optional[Tuple[Dict, int]]: Tuple of function info dict and end index, or None if not a function.
        """
        # Handle multi-line function declarations (join lines until ; or {)
        full_decl = line
        end_idx = start_idx
        while end_idx < len(lines) and ';' not in full_decl and '{' not in full_decl:
            end_idx += 1
            if end_idx < len(lines):
                full_decl += ' ' + lines[end_idx].strip()

        if '{' in full_decl:
            full_decl = full_decl[:full_decl.index('{')].strip()
        elif ';' in full_decl:
            full_decl = full_decl[:full_decl.index(';')].strip()
        else:
            return None

        # Detect assignment operator (copy/move)
        is_assignment = False
        assignment_type = None
        if 'operator=' in full_decl:
            # Only skip if it's not a copy/move assignment
            is_assignment = True
            # Try to detect copy/move assignment
            if self.current_class:
                # e.g. ClassName& operator=(const ClassName&) or ClassName& operator=(ClassName&&)
                if re.search(r'operator\s*=\s*\((const\s+' + re.escape(self.current_class) + r'\s*&|'+re.escape(self.current_class)+r'\s*&&)', full_decl):
                    assignment_type = 'copy' if 'const' in full_decl else 'move'
            # If not copy/move assignment, skip
            if not assignment_type:
                return None

        # Match function declaration using regex (also matches ctors/dtors)
        pattern = r'(?:(?:virtual|static|inline|explicit|constexpr)\s+)*' \
                  r'(?:[\w:<>]+\s+)*' \
                  r'(~?\w+|operator=)\s*\((.*?)\)\s*(?:const\s*)?' \
                  r'(?:noexcept\s*(?:\([^)]*\))?\s*)?' \
                  r'(?:\=\s*(?:default|delete|\d+))?\s*'

        match = re.match(pattern, full_decl)
        if not match:
            return None

        func_name = match.group(1)
        params = match.group(2)

        # Try to extract return type (for constructors/destructors, this will be empty)
        ret_type_match = re.match(r'(?:(?:virtual|static|inline|explicit|constexpr)\s+)*((?:[\w:<>]+\s+)*)' + re.escape(func_name) + r'\s*\(', full_decl)
        return_type = ret_type_match.group(1).strip() if ret_type_match else ''

        # Parse parameters (type and name)
        param_list = []
        if params:
            for p in [p.strip() for p in params.split(',')]:
                if not p:
                    continue
                # Handle default values
                p = re.sub(r'\s*=\s*.*$', '', p)
                # Get type and name
                parts = p.rsplit(' ', 1)
                if len(parts) == 1:
                    param_type = parts[0]
                    param_name = ''
                else:
                    param_type, param_name = parts
                param_list.append((param_type, param_name))

        # Check for noexcept
        noexcept = 'noexcept' in full_decl

        # Check for throw specification (older C++ style)
        throw_spec = None
        throw_match = re.search(r'throw\s*\((.*?)\)', full_decl)
        if throw_match:
            throw_spec = [t.strip() for t in throw_match.group(1).split(',') if t.strip()]

        # Detect if this is a constructor or destructor
        is_ctor = self.current_class and (func_name == self.current_class)
        is_dtor = self.current_class and (func_name == f'~{self.current_class}')

        # Detect copy/move constructor
        is_copy_ctor = False
        is_move_ctor = False
        if self.current_class and func_name == self.current_class and param_list:
            # Copy: const ClassName&
            if len(param_list) == 1 and re.match(r'const\s+' + re.escape(self.current_class) + r'\s*&', param_list[0][0]):
                is_copy_ctor = True
            # Move: ClassName&&
            elif len(param_list) == 1 and re.match(re.escape(self.current_class) + r'\s*&&', param_list[0][0]):
                is_move_ctor = True

        # Detect copy/move assignment operator
        is_copy_assign = is_assignment and assignment_type == 'copy'
        is_move_assign = is_assignment and assignment_type == 'move'

        return {
            'return_type': return_type,
            'name': func_name,
            'params': param_list,
            'noexcept': noexcept,
            'throw': throw_spec,
            'static': 'static' in full_decl,
            'const': 'const' in full_decl.split(')')[-1],
            'full_decl': full_decl,
            'is_ctor': is_ctor,
            'is_dtor': is_dtor,
            'is_copy_ctor': is_copy_ctor,
            'is_move_ctor': is_move_ctor,
            'is_copy_assign': is_copy_assign,
            'is_move_assign': is_move_assign
        }, end_idx


    def _match_variable(self, line: str, lines: List[str], start_idx: int) -> Optional[Tuple[Dict, int]]:
        """
        Try to match a variable declaration starting at start_idx.
        Args:
            line (str): Current line.
            lines (List[str]): All lines from the file.
            start_idx (int): Index of the current line.
        Returns:
            Optional[Tuple[Dict, int]]: Tuple of variable info dict and end index, or None if not a variable.
        """
        # Skip lines that are part of a function or other constructs
        if any(s in line for s in ['{', '}', '(', ')', ';']) and not (';' in line and '=' not in line):
            return None

        # Skip forward declarations and type/namespace/using/typedef declarations
        skip_prefixes = (
            'class ', 'struct ', 'enum ', 'namespace ', 'using ', 'typedef ', 'template ', 'friend ', 'public:', 'private:', 'protected:'
        )
        if line.strip().startswith(skip_prefixes):
            return None

        # Handle multi-line declarations (join lines until ;)
        full_decl = line
        end_idx = start_idx
        while end_idx < len(lines) and ';' not in full_decl:
            end_idx += 1
            if end_idx < len(lines):
                full_decl = f"{full_decl.rstrip()} {lines[end_idx].strip()}"

        if ';' not in full_decl:
            return None

        full_decl = full_decl[:full_decl.index(';')].strip()

        # Skip again if the full_decl is a forward declaration or type/namespace/using/typedef
        if full_decl.startswith(skip_prefixes):
            return None

        # Updated regex pattern for variable declarations
        pattern = r'(?:(?:static|constexpr|mutable|inline)\s+)?' \
                  r'(?:const\s+)?' \
                  r'(.+?)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*(?:=\s*.*)?$'

        match = re.match(pattern, full_decl)
        if not match:
            return None

        var_type = match.group(1).strip()
        var_name = match.group(2)

        return {
            'type': var_type,
            'name': var_name,
            'static': 'static' in full_decl,
            'constexpr': 'constexpr' in full_decl,
            'mutable': 'mutable' in full_decl,
            'full_decl': full_decl
        }, end_idx


    def _get_indent(self, line: str) -> str:
        """
        Return the leading whitespace of a line.
        Args:
            line (str): The line to check.
        Returns:
            str: Leading whitespace (indentation).
        """
        return line[:len(line) - len(line.lstrip())]

    def _generate_class_comment(self, class_name: str, class_type: str, indent: str = "") -> List[str]:
        """
        Generate Doxygen comment for a class or struct.

        Args:
            class_name (str): Name of the class or struct.
            class_type (str): 'class' or 'struct'.
            indent (str): Indentation to use.

        Returns:
            List[str]: Doxygen comment lines.
        """
        comment = [
            f"{indent}/**",
            f"{indent} * @brief {class_type} {class_name}",
            f"{indent} *",
            f"{indent} * @details Detailed description of {class_type} {class_name}",
            f"{indent} */"
        ]
        return [line + "\n" for line in comment]

    def _generate_function_comment(self, func: Dict, indent: str = "") -> List[str]:
        """
        Generate a compact, readable Doxygen comment for a function, constructor, or destructor.
        """
        ret_type = func.get('return_type', '').strip()
        for spec in ('public:', 'private:', 'protected:'):
            if ret_type.startswith(spec):
                ret_type = ret_type[len(spec):].strip()
        ret_type = re.sub(r'^(virtual|inline|explicit|constexpr|static)\\s+', '', ret_type)

        comment = [f'{indent}/**']

        # Brief description
        if func.get('is_copy_ctor'):
            comment.append(f"{indent} * @brief Copy constructor for {self.current_class}")
        elif func.get('is_move_ctor'):
            comment.append(f"{indent} * @brief Move constructor for {self.current_class}")
        elif func.get('is_copy_assign'):
            comment.append(f"{indent} * @brief Copy assignment operator for {self.current_class}")
        elif func.get('is_move_assign'):
            comment.append(f"{indent} * @brief Move assignment operator for {self.current_class}")
        elif func.get('is_ctor'):
            comment.append(f"{indent} * @brief Constructor for {self.current_class}")
        elif func.get('is_dtor'):
            comment.append(f"{indent} * @brief Destructor for {self.current_class}")
        else:
            comment.append(f"{indent} * @brief {self._generate_brief_description(func['name'])}")

        # Detailed description
        comment.append(f'{indent} * @details')

        # Parameters
        for param_type, param_name in func['params']:
            if param_name:
                clean_name = param_name.lstrip('&*')
                comment.append(f'{indent} * @param {clean_name}')

        # Return value
        if not func.get('is_ctor') and not func.get('is_dtor') and ret_type not in ('void', ''):
            comment.append(f'{indent} * @return {ret_type}')

        # Exceptions
        if func['throw']:
            for exc in func['throw']:
                comment.append(f'{indent} * @throws {exc}')
        elif not func['noexcept']:
            comment.append(f'{indent} * @throws std::exception on error')

        if func['static']:
            comment.append(f'{indent} * @static')
        if func['const']:
            comment.append(f'{indent} * @const')

        comment.append(f'{indent} */\n')
        return [line + '\n' for line in comment]

    def _generate_enum_comment(self, enum_name: str, indent: str = "") -> List[str]:
        """
        Generate Doxygen comment for an enum.

        Args:
            enum_name (str): Name of the enum.
            indent (str): Indentation to use.

        Returns:
            List[str]: Doxygen comment lines.
        """
        comment = [
            f'{indent}/**\n',
            f'{indent} * @brief Enum {enum_name}\n',
            f'{indent} *\n',
            f'{indent} * @details Detailed description of enum {enum_name}\n',
            f'{indent} */\n'
        ]
        return comment

    def _generate_variable_comment(self, var: Dict, indent: str = "") -> list[str] | None:
        """
        Generate Doxygen comment for a variable.

        Args:
            var (Dict): Variable information.
            indent (str): Indentation to use.

        Returns:
            List[str]: Doxygen comment lines, or None if not applicable.
        """
        # Skip variables in function declarations
        if '(' in var['full_decl'] or ')' in var['full_decl']:
            return None

        comment = [f'{indent}/**\n']

        # Brief description
        brief_desc = f"{indent} * @brief {self._generate_brief_description(var['name'], is_var=True)}\n"
        comment.append(brief_desc)
        comment.append(f'{indent} *\n')

        # Static
        if var['static']:
            comment.append(f'{indent} * @static\n')

        # Constexpr
        if var['constexpr']:
            comment.append(f'{indent} * @constexpr\n')

        # Mutable
        if var['mutable']:
            comment.append(f'{indent} * @mutable\n')

        comment.append(f'{indent} */\n')
        return comment

    def _generate_brief_description(self, name: str, is_var: bool = False) -> str:
        """
        Generate a brief description based on the name.

        Args:
            name (str): Name of the function or variable.
            is_var (bool): True if variable, False if functioned.

        Returns:
            str: Brief description.
        """
        if is_var:
            return f"Variable {name}"

        # Convert camelCase or snake_case to readable text
        readable = re.sub(r'([A-Z])', r' \1', name)
        readable = readable.replace('_', ' ')
        readable = readable.lower().capitalize()

        # Common prefixes for function names
        prefixes = {
            'get': 'Gets the ',
            'set': 'Sets the ',
            'is': 'Checks if ',
            'has': 'Checks if has ',
            'create': 'Creates a new ',
            'init': 'Initializes the ',
            'update': 'Updates the ',
            'delete': 'Deletes the ',
            'remove': 'Removes the ',
            'add': 'Adds a new ',
            'find': 'Finds the ',
            'calculate': 'Calculates the ',
            'compute': 'Computes the ',
        }

        for prefix, desc in prefixes.items():
            if name.lower().startswith(prefix):
                rest = name[len(prefix):]
                if not rest:
                    return desc[:-1]
                rest_readable = re.sub(r'([A-Z])', r' \1', rest)
                rest_readable = rest_readable.replace('_', ' ')
                rest_readable = rest_readable.lower()
                return desc + rest_readable

        return readable

    def process_lines(self, lines: List[str]) -> List[str]:
        """
        Process lines of a header file, adding Doxygen comments.

        Args:
            lines (List[str]): Lines of the header file.

        Returns:
            List[str]: Lines with added Doxygen comments.
        """
        output_lines = []
        inside_class = False
        current_indent = ""

        for i, line in enumerate(lines):
            stripped_line = line.strip()

            # Skip empty lines
            if not stripped_line:
                output_lines.append(line)
                continue

            # Skip existing Doxygen comments
            if stripped_line.startswith('/**') or stripped_line.startswith('///') or stripped_line.startswith('/*!'):
                output_lines.append(line)
                continue

            # Handle namespace declaration
            namespace_match = re.match(r'namespace\s+(\w+)\s*\{', stripped_line)
            if namespace_match:
                self.current_namespace = namespace_match.group(1)
                output_lines.append(line)
                continue

            # Handle class or struct declaration
            class_match = re.match(
                r'(class|struct)\s+(\w+)\s*(?:final)?\s*(?::\s*(?:public|private|protected)\s+\w+)?\s*\{', stripped_line)
            if class_match:
                self.current_class = class_match.group(2)
                inside_class = True
                class_brace_depth = 1
                indent = self._get_indent(lines[i])
                doc_comment = self._generate_class_comment(class_match.group(2), class_match.group(1), indent)
                output_lines.extend(doc_comment)
                output_lines.append(lines[i])
                i += 1
                # Process class body
                while i < len(lines) and inside_class:
                    line = lines[i].strip()
                    class_brace_depth += line.count('{')
                    class_brace_depth -= line.count('}')
                    # Skip visibility specifiers
                    if re.match(r'^(public|private|protected)\s*:\s*$', line):
                        output_lines.append(lines[i])
                        i += 1
                        continue
                    # Variable in class
                    var_match = self._match_variable(line, lines, i)
                    if var_match:
                        var_decl, end_idx = var_match
                        indent = self._get_indent(lines[i])
                        doc_comment = self._generate_variable_comment(var_decl, indent)
                        if doc_comment:
                            output_lines.extend(doc_comment)
                        for idx in range(i, end_idx + 1):
                            output_lines.append(lines[idx])
                        i = end_idx + 1
                        continue
                    # Function in class
                    func_match = self._match_function(line, lines, i)
                    if func_match:
                        func_decl, end_idx = func_match
                        indent = self._get_indent(lines[i])
                        doc_comment = self._generate_function_comment(func_decl, indent)
                        output_lines.extend(doc_comment)
                        for idx in range(i, end_idx + 1):
                            output_lines.append(lines[idx])
                        i = end_idx + 1
                        continue
                    # End of class
                    if class_brace_depth == 0:
                        inside_class = False
                        self.current_class = None
                        output_lines.append(lines[i])
                        i += 1
                        break
                    # Regular line in class
                    output_lines.append(lines[i])
                    i += 1
                continue

            # Handle function declarations
            func_match = self._match_function(stripped_line, lines, i)
            if func_match:
                func_decl, end_idx = func_match
                indent = self._get_indent(lines[i])
                doc_comment = self._generate_function_comment(func_decl, indent)
                output_lines.extend(doc_comment)
                # Add the original lines
                for idx in range(i, end_idx + 1):
                    output_lines.append(lines[idx])
                i = end_idx + 1
                continue

            # Handle enum declaration
            enum_match = re.match(r'enum\s+(?:class\s+)?(\w+)\s*(?::\s*\w+)?\s*\{', stripped_line)
            if enum_match:
                indent = self._get_indent(lines[i])
                doc_comment = self._generate_enum_comment(enum_match.group(1), indent)
                output_lines.extend(doc_comment)
                output_lines.append(lines[i])
                continue

            # Handle variable declarations (member or global)
            var_match = self._match_variable(stripped_line, lines, i)
            if var_match:
                var_decl, end_idx = var_match
                indent = self._get_indent(lines[i])
                doc_comment = self._generate_variable_comment(var_decl, indent)
                if doc_comment:
                    output_lines.extend(doc_comment)
                for idx in range(i, end_idx + 1):
                    output_lines.append(lines[idx])
                i = end_idx + 1
                continue

            # Handle closing braces for namespace/class
            if stripped_line == '}' and (self.current_class or self.current_namespace):
                if ';' in stripped_line:  # End of class/namespace
                    if self.current_class:
                        self.current_class = None
                    else:
                        self.current_namespace = None
                output_lines.append(line)
                inside_class = False
                continue

            # If inside a class, check for variable declarations and add comments
            if inside_class and self._is_variable_declaration(stripped_line):
                var_info = self._match_variable(stripped_line, lines, i)
                if var_info:
                    # Insert comment before this variable
                    comment = self._generate_variable_comment(var_info[0], indent=current_indent)
                    output_lines.extend(comment)
                    output_lines.append(line)
                    continue

            # Regular line - just add it
            output_lines.append(line)

        return output_lines

    def _is_variable_declaration(self, line: str) -> bool:
        """
        Check if a line is a variable declaration.

        Args:
            line (str): Line to check.

        Returns:
            bool: True if it's a variable declaration, False otherwise.
        """
        # A simple check for variable declaration patterns
        return re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*\s*=', line) is not None
