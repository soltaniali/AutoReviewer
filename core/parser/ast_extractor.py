import ast
from typing import List, Dict

class ASTExtractor(ast.NodeVisitor):
    """
    Extracts function and class definitions, and their body's line numbers.
    Used to get precise chunks out of large Python files based on changed lines.
    """
    def __init__(self):
        self.functions = []
        self.classes = []

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self.functions.append({
            "name": node.name,
            "start_line": node.lineno,
            "end_line": node.end_lineno,
            "docstring": ast.get_docstring(node)
        })
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self.functions.append({
            "name": node.name,
            "start_line": node.lineno,
            "end_line": node.end_lineno,
            "docstring": ast.get_docstring(node)
        })
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        self.classes.append({
            "name": node.name,
            "start_line": node.lineno,
            "end_line": node.end_lineno,
            "docstring": ast.get_docstring(node)
        })
        self.generic_visit(node)

def extract_code_elements(source_code: str) -> Dict[str, List[dict]]:
    """
    Extracts defined classes and functions from Python source code.
    Returns: {"classes": [...], "functions": [...]}
    """
    try:
        tree = ast.parse(source_code)
    except SyntaxError as e:
        return {"error": f"Syntax error in code: {e}"}

    extractor = ASTExtractor()
    extractor.visit(tree)

    return {
        "classes": extractor.classes,
        "functions": extractor.functions
    }

def get_context_for_lines(source_code: str, target_lines: List[int]) -> str:
    """
    Given a list of modified lines, use AST parsing to return only the source code
    of the functions/classes containing those lines to optimize context length.
    """
    elements = extract_code_elements(source_code)
    if "error" in elements:
        return source_code  # Fallback to full source
    
    code_lines = source_code.splitlines()
    context_blocks = []
    included_ranges = set()

    all_blocks = elements.get("classes", []) + elements.get("functions", [])

    for line in target_lines:
        for block in all_blocks:
            start, end = block["start_line"], block["end_line"]
            if start <= line <= end:
                range_tuple = (start, end)
                if range_tuple not in included_ranges:
                    included_ranges.add(range_tuple)
                    block_code = "\n".join(code_lines[start-1:end])
                    context_blocks.append(f"--- {block.get('name')} (Lines {start}-{end}) ---\n{block_code}")

    if not context_blocks:
        return source_code  # Fallback if no matching blocks found

    return "\n\n".join(context_blocks)
