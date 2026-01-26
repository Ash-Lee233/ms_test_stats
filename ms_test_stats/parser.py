import ast
from dataclasses import dataclass
from typing import Optional, Set
import re

@dataclass
class TestCaseMeta:
    file_path: str
    node_name: str
    level: Optional[str]
    markers: Set[str]

def _dotted_name(expr: ast.AST):
    """Return dotted name for AST nodes like pytest.mark.level0."""
    if isinstance(expr, ast.Call):
        return _dotted_name(expr.func)
    if isinstance(expr, ast.Attribute):
        base = _dotted_name(expr.value)
        return f"{base}.{expr.attr}" if base else expr.attr
    if isinstance(expr, ast.Name):
        return expr.id
    return None

def extract_testcases_from_file(py_path: str, source: str, level_re: re.Pattern):
    tree = ast.parse(source, filename=py_path)
    out = []

    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        markers = set()
        level = None

        for dec in node.decorator_list:
            dn = _dotted_name(dec)
            if not dn:
                continue
            if dn.startswith("pytest.mark."):
                mark = dn.split("pytest.mark.", 1)[1]
                markers.add(mark)
                if level is None and level_re.match(mark):
                    level = mark

        # MindSpore tests typically use test_* naming
        if node.name.startswith("test_"):
            out.append(TestCaseMeta(py_path, node.name, level, markers))

    return out
