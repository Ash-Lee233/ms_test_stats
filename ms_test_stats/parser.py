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
    assert_count: int
    has_docstring: bool
    has_parametrize: bool

def _dotted_name(expr: ast.AST):
    if isinstance(expr, ast.Call):
        return _dotted_name(expr.func)
    if isinstance(expr, ast.Attribute):
        base = _dotted_name(expr.value)
        return f"{base}.{expr.attr}" if base else expr.attr
    if isinstance(expr, ast.Name):
        return expr.id
    return None

def _has_docstring(func: ast.AST) -> bool:
    body = getattr(func, "body", [])
    if not body:
        return False
    first = body[0]
    return (
        isinstance(first, ast.Expr)
        and isinstance(getattr(first, "value", None), ast.Constant)
        and isinstance(first.value.value, str)
    )

def _count_asserts(func: ast.AST) -> int:
    count = 0
    for n in ast.walk(func):
        if isinstance(n, ast.Assert):
            count += 1
        elif isinstance(n, ast.Call):
            fn = n.func
            name = None
            if isinstance(fn, ast.Name):
                name = fn.id
            elif isinstance(fn, ast.Attribute):
                name = fn.attr
            if name and name.lower().startswith("assert"):
                count += 1
    return count

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

        if node.name.startswith("test_"):
            out.append(TestCaseMeta(
                file_path=py_path,
                node_name=node.name,
                level=level,
                markers=markers,
                assert_count=_count_asserts(node),
                has_docstring=_has_docstring(node),
                has_parametrize=("parametrize" in {m.lower() for m in markers}),
            ))

    return out
