import re
from typing import List, Dict, Optional, Tuple

class HeaderDoxygenGenerator:
    def __init__(self):
        """
        Initialize the HeaderDoxygenGenerator with current class and namespace tracking.
        """
        self.current_class = None
        self.current_namespace = None

    def parse_header(self, filename: str) -> List[str]:
        """
        Parse a C/C++ header file and return lines with added Doxygen comments.

        Args:
            filename (str): Path to the header file.

        Returns:
            List[str]: List of lines with Doxygen comments inserted.
        """
        with open(filename, 'r') as f:
            lines = f.readlines()

        output = []
        i = 0
        inside_class = False
        class_brace_depth = 0
        last_was_decl = False

        while i < len(lines):
            line = lines[i].rstrip('\n')
            stripped = line.strip()

            # Skip empty lines
            if not stripped:
                output.append(lines[i])
                last_was_decl = False
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
                last_was_decl = False
                continue

            # Handle namespace declaration
            namespace_match = re.match(r'namespace\s+(\w+)\s*\{', stripped)
            if namespace_match:
                self.current_namespace = namespace_match.group(1)
                if output and output[-1].strip():
                    output.append('\n')
                output.append(lines[i])
                last_was_decl = True
                i += 1
                continue

            # Handle class or struct declaration
            class_match = re.match(r'(class|struct)\s+(\w+)\s*(?:final)?\s*(?::\s*(?:public|private|protected)\s+\w+)?\s*\{', stripped)
            if class_match:
                self.current_class = class_match.group(2)
                inside_class = True
                class_brace_depth = 1
                indent = self._get_indent(lines[i])
                if output and output[-1].strip():
                    output.append('\n')
                doc_comment = self._generate_class_comment(class_match.group(2), class_match.group(1), indent)
                output.extend(doc_comment)
                output.append(lines[i])
                output.append('\n')
                last_was_decl = True
                i += 1
                # Process class body
                while i < len(lines) and inside_class:
                    line = lines[i].rstrip('\n')
                    stripped = line.strip()
                    class_brace_depth += stripped.count('{')
                    class_brace_depth -= stripped.count('}')
                    # Skip visibility specifiers
                    if re.match(r'^(public|private|protected)\s*:\s*$', stripped):
                        output.append(lines[i])
                        i += 1
                        last_was_decl = False
                        continue
                    # Try to match function or variable, even for constructors/destructors/overrides
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
                    # Try to match variable (including those with default values, e.g. int x = 0;)
                    var_match = self._match_variable(stripped, lines, i)
                    if var_match:
                        var_decl, end_idx = var_match
                        indent = self._get_indent(lines[i])
                        if output and output[-1].strip():
                            output.append('\n')
                        doc_comment = self._generate_variable_comment(var_decl, indent)
                        if doc_comment:
                            output.extend(doc_comment)
                        for idx in range(i, end_idx + 1):
                            output.append(lines[idx])
                        output.append('\n')
                        i = end_idx + 1
                        last_was_decl = True
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

            # Handle variable declarations (member or global)
            var_match = self._match_variable(stripped, lines, i)
            if var_match:
                var_decl, end_idx = var_match
                indent = self._get_indent(lines[i])
                if output and output[-1].strip():
                    output.append('\n')
                doc_comment = self._generate_variable_comment(var_decl, indent)
                if doc_comment:
                    output.extend(doc_comment)
                for idx in range(i, end_idx + 1):
                    output.append(lines[idx])
                output.append('\n')
                i = end_idx + 1
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

        # Remove trailing blank lines
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
            Optional[Tuple[Dict, int]]: Function info dict and end index, or None.
        """
        # Handle multi-line function declarations
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

        # Match function declaration using regex
        # This pattern will also match constructors and destructors
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

        # Parse parameters
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
        # Skip lines that are part of a function or other constructs
        if any(s in line for s in ['{', '}', '(', ')', ';']) and not (';' in line and '=' not in line):
            return None

        # Handle multi-line declarations
        full_decl = line
        end_idx = start_idx
        while end_idx < len(lines) and ';' not in full_decl:
            end_idx += 1
            if end_idx < len(lines):
                full_decl = f"{full_decl.rstrip()} {lines[end_idx].strip()}"

        if ';' not in full_decl:
            return None

        full_decl = full_decl[:full_decl.index(';')].strip()

        # Updated regex pattern
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
        """Return the leading whitespace of a line."""
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
        Generate Doxygen comment for a function, constructor, or destructor.

        Args:
            func (Dict): Function information.
            indent (str): Indentation to use.

        Returns:
            List[str]: Doxygen comment lines.
        """
        comment = [f'{indent}/**\n']

        # Brief description
        if func.get('is_copy_ctor'):
            brief_desc = f"{indent} * @brief Copy constructor for {self.current_class}\n"
        elif func.get('is_move_ctor'):
            brief_desc = f"{indent} * @brief Move constructor for {self.current_class}\n"
        elif func.get('is_copy_assign'):
            brief_desc = f"{indent} * @brief Copy assignment operator for {self.current_class}\n"
        elif func.get('is_move_assign'):
            brief_desc = f"{indent} * @brief Move assignment operator for {self.current_class}\n"
        elif func.get('is_ctor'):
            brief_desc = f"{indent} * @brief Constructor for {self.current_class}\n"
        elif func.get('is_dtor'):
            brief_desc = f"{indent} * @brief Destructor for {self.current_class}\n"
        else:
            brief_desc = f"{indent} * @brief {self._generate_brief_description(func['name'])}\n"
        comment.append(brief_desc)
        comment.append(f'{indent} *\n')

        # Detailed description
        comment.append(f'{indent} * @details \n')
        comment.append(f'{indent} *\n')

        # Parameters
        for param_type, param_name in func['params']:
            if param_name:  # Skip unnamed parameters
                comment.append(f'{indent} * @param {param_name} \n')

        # Return value (not for constructors/destructors)
        if not func.get('is_ctor') and not func.get('is_dtor') and func['return_type'] not in ('void', ''):
            comment.append(f'{indent} * @return {func["return_type"]} \n')

        # Exceptions
        if func['throw']:
            for exc in func['throw']:
                comment.append(f'{indent} * @throws {exc} \n')
        elif not func['noexcept']:
            comment.append(f'{indent} * @throws std::exception on error\n')

        # Static
        if func['static']:
            comment.append(f'{indent} * @static\n')

        # Const
        if func['const']:
            comment.append(f'{indent} * @const\n')

        comment.append(f'{indent} */\n')
        return comment

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
