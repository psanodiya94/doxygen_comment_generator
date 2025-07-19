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
        while i < len(lines):
            line = lines[i].strip()

            # Skip existing Doxygen comments
            if line.startswith('/**') or line.startswith('///') or line.startswith('/*!'):
                while i < len(lines) and '*/' not in lines[i]:
                    output.append(lines[i])
                    i += 1
                if i < len(lines):
                    output.append(lines[i])
                    i += 1
                continue

            # Handle namespace declaration
            namespace_match = re.match(r'namespace\s+(\w+)\s*\{', line)
            if namespace_match:
                self.current_namespace = namespace_match.group(1)
                output.append(lines[i])
                i += 1
                continue

            # Handle class or struct declaration
            class_match = re.match(
                r'(class|struct)\s+(\w+)\s*(?:final)?\s*(?::\s*(?:public|private|protected)\s+\w+)?\s*\{', line)
            if class_match:
                self.current_class = class_match.group(2)
                indent = self._get_indent(lines[i])
                doc_comment = self._generate_class_comment(class_match.group(2), class_match.group(1), indent)
                output.extend(doc_comment)
                output.append(lines[i])
                i += 1
                continue

            # Handle function declarations
            func_match = self._match_function(line, lines, i)
            if func_match:
                func_decl, end_idx = func_match
                indent = self._get_indent(lines[i])
                doc_comment = self._generate_function_comment(func_decl, indent)
                output.extend(doc_comment)
                # Add the original lines
                for idx in range(i, end_idx + 1):
                    output.append(lines[idx])
                i = end_idx + 1
                continue

            # Handle enum declaration
            enum_match = re.match(r'enum\s+(?:class\s+)?(\w+)\s*(?::\s*\w+)?\s*\{', line)
            if enum_match:
                indent = self._get_indent(lines[i])
                doc_comment = self._generate_enum_comment(enum_match.group(1), indent)
                output.extend(doc_comment)
                output.append(lines[i])
                i += 1
                continue

            # Handle variable declarations (member or global)
            var_match = self._match_variable(line, lines, i)
            if var_match:
                var_decl, end_idx = var_match
                indent = self._get_indent(lines[i])
                doc_comment = self._generate_variable_comment(var_decl, indent)
                if doc_comment:
                    output.extend(doc_comment)
                for idx in range(i, end_idx + 1):
                    output.append(lines[idx])
                i = end_idx + 1
                continue

            # Handle closing braces for namespace/class
            if line == '}' and (self.current_class or self.current_namespace):
                if ';' in line:  # End of class/namespace
                    if self.current_class:
                        self.current_class = None
                    else:
                        self.current_namespace = None
                output.append(lines[i])
                i += 1
                continue

            # Regular line - just add it
            output.append(lines[i])
            i += 1

        return output

    def _match_function(self, line: str, lines: List[str], start_idx: int) -> Optional[Tuple[Dict, int]]:
        """
        Try to match a function declaration starting at start_idx.

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

        # Skip constructors/destructors
        if self.current_class and (full_decl.startswith(f'~{self.current_class}(') or
                                   full_decl.startswith(f'{self.current_class}(')):
            return None

        # Skip operator overloads
        if 'operator' in full_decl:
            return None

        # Match function declaration using regex
        pattern = r'(?:(?:virtual|static|inline|explicit|constexpr)\s+)*' \
                  r'(?:(?:[\w:]+|<.*>)\s+)+' \
                  r'(\w+)\s*\((.*?)\)\s*(?:const\s*)?' \
                  r'(?:noexcept\s*(?:\([^)]*\))?\s*)?' \
                  r'(?:\=\s*(?:default|delete|\d+))?\s*'

        match = re.match(pattern, full_decl)
        if not match:
            return None

        return_type = full_decl[:full_decl.find(match.group(1))].strip()
        func_name = match.group(1)
        params = match.group(2)

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

        return {
            'return_type': return_type,
            'name': func_name,
            'params': param_list,
            'noexcept': noexcept,
            'throw': throw_spec,
            'static': 'static' in full_decl,
            'const': 'const' in full_decl.split(')')[-1],
            'full_decl': full_decl
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
        Generate Doxygen comment for a function.

        Args:
            func (Dict): Function information.
            indent (str): Indentation to use.

        Returns:
            List[str]: Doxygen comment lines.
        """
        comment = [f'{indent}/**\n']

        # Brief description
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

        # Return value
        if func['return_type'] not in ('void', '') and not (self.current_class and func['name'] == self.current_class):
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