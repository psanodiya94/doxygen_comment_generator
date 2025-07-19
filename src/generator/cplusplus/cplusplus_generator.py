import re
from typing import List, Dict, Optional, Tuple

class CPlusPlusDoxygenGenerator:
    def parse_source(self, filename: str) -> List[str]:
        """
        Parse a C++ source file and return lines with added Doxygen comments.
        Args:
            filename (str): Path to the source file.
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

            # Handle function definitions (very basic, can be improved)
            func_match = re.match(r'([a-zA-Z_][\w:<>\s*&]+)\s+([a-zA-Z_][\w]*)\s*\(([^)]*)\)\s*(const)?\s*\{', line)
            if func_match:
                indent = self._get_indent(lines[i])
                func_name = func_match.group(2)
                doc_comment = [
                    f"{indent}/**",
                    f"{indent} * @brief {func_name} function",
                    f"{indent} *",
                    f"{indent} * @details Detailed description of {func_name}",
                    f"{indent} */\n"
                ]
                output.extend([l + "\n" for l in doc_comment])
                output.append(lines[i])
                i += 1
                continue

            output.append(lines[i])
            i += 1

        return output

    def _get_indent(self, line: str) -> str:
        return line[:len(line) - len(line.lstrip())]