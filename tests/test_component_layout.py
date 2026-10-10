"""Guard the required one-component-per-file MCP layout."""

import ast
from pathlib import Path

import pytest

from bls_escalation_mcp import mcp

COMPONENT_ROOT = Path(mcp.__file__).parent
COMPONENT_FILES = sorted(
    path
    for kind in ("tools", "resources")
    for path in (COMPONENT_ROOT / kind).glob("*.py")
    if path.name != "__init__.py"
)


@pytest.mark.parametrize("path", COMPONENT_FILES, ids=lambda p: p.stem)
def test_one_component_per_module(path):
    tree = ast.parse(path.read_text())
    components = [
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and any(
            isinstance(decorator, ast.Call)
            and isinstance(decorator.func, ast.Attribute)
            and isinstance(decorator.func.value, ast.Name)
            and decorator.func.value.id == "mcp"
            and decorator.func.attr in {"tool", "resource", "prompt"}
            for decorator in node.decorator_list
        )
    ]
    assert len(components) == 1, path
    assert components[0].name == path.stem
    registrations = [
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "register"
    ]
    assert len(registrations) == 1
    register = registrations[0]
    assert components[0] in register.body
    assert ast.unparse(register.args.args[0].annotation) == "FastMCP"
    assert ast.unparse(register.returns) == "None"
