"""
Author: Shawny
"""
import ast
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Set
import re

@dataclass
class TestCaseMeta:
    file_path: str
    node_name: str
    level: Optional[str]
    markers: Set[str]                 # marker names only (e.g. level0, skip, parametrize)
    pytest_decorators: List[str]           # full pytest decorator names (e.g. pytest.mark.parametrize); keeps duplicates
    assert_count: int
    has_docstring: bool
    has_parametrize: bool

def _dotted_name(expr: ast.AST) -> Optional[str]:
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

def _build_alias_map(tree: ast.Module) -> Dict[str, str]:
    aliases: Dict[str, str] = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
            continue
        name = node.targets[0].id
        dn = _dotted_name(node.value)
        if dn and dn.startswith("pytest.mark."):
            aliases[name] = dn
    return aliases

def _extract_pytest_decorators(decorators: Iterable[ast.AST], alias_map: Dict[str, str]) -> List[str]:
    out: List[str] = []
    for dec in decorators:
        dn = _dotted_name(dec)
        if not dn:
            continue
        if dn in alias_map:
            dn = alias_map[dn]
        if dn.startswith("pytest."):
            out.append(dn)
    return out

def _extract_marks_from_decorators(decorators: Iterable[ast.AST], alias_map: Dict[str, str]) -> Set[str]:
    out: Set[str] = set()
    for dec in decorators:
        dn = _dotted_name(dec)
        if not dn:
            continue
        if dn in alias_map:
            dn = alias_map[dn]
        if dn.startswith("pytest.mark."):
            out.add(dn.split("pytest.mark.", 1)[1])
    return out

def _extract_pytestmark(tree: ast.Module, alias_map: Dict[str, str]) -> Set[str]:
    out: Set[str] = set()

    def add_expr(e: ast.AST):
        dn = _dotted_name(e)
        if not dn:
            return
        if dn in alias_map:
            dn = alias_map[dn]
        if dn.startswith("pytest.mark."):
            out.add(dn.split("pytest.mark.", 1)[1])

    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        targets = [t.id for t in node.targets if isinstance(t, ast.Name)]
        if "pytestmark" not in targets:
            continue
        val = node.value
        if isinstance(val, (ast.List, ast.Tuple)):
            for elt in val.elts:
                add_expr(elt)
        else:
            add_expr(val)

    return out

def _pick_level(markers: Set[str], level_re: re.Pattern) -> Optional[str]:
    for m in markers:
        if level_re.match(m):
            return m
    return None

def extract_testcases_from_file(py_path: str, source: str, level_re: re.Pattern) -> List[TestCaseMeta]:
    tree = ast.parse(source, filename=py_path)

    alias_map = _build_alias_map(tree)
    module_marks = _extract_pytestmark(tree, alias_map)

    out: List[TestCaseMeta] = []

    def record_test(func: ast.AST, name: str, inherited_marks: Set[str], inherited_pytest_decs: List[str]):
        func_marks = _extract_marks_from_decorators(getattr(func, "decorator_list", []), alias_map)
        func_pytest = _extract_pytest_decorators(getattr(func, "decorator_list", []), alias_map)

        markers = set(inherited_marks) | func_marks
        pytest_decs = list(inherited_pytest_decs) + list(func_pytest)

        level = _pick_level(markers, level_re)

        out.append(TestCaseMeta(
            file_path=py_path,
            node_name=name,
            level=level,
            markers=markers,
            pytest_decorators=pytest_decs,
            assert_count=_count_asserts(func),
            has_docstring=_has_docstring(func),
            has_parametrize=("parametrize" in {m.lower() for m in markers}),
        ))

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_"):
            record_test(node, node.name, module_marks, [])
            continue

        if isinstance(node, ast.ClassDef):
            class_marks = module_marks | _extract_marks_from_decorators(node.decorator_list, alias_map)
            class_pytest = _extract_pytest_decorators(node.decorator_list, alias_map)

            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name.startswith("test_"):
                    record_test(item, f"{node.name}.{item.name}", class_marks, class_pytest)

    return out
