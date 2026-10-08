"""Which result-file keys the figure generator actually subscripts.

Resolved with `ast` rather than regular expressions, for one concrete reason:
the generator binds the name `d` to two different result files in two different
functions. Matching over the whole file cross-attributes their keys and reports
failures that are not real, so the question has to be asked one function body at
a time — which is what the syntax tree gives for free.

The scoping has to be literal about it. `ast.walk` from a module-level statement
descends into every function defined below it, which reintroduces exactly the
cross-attribution the tree was brought in to avoid; the walk here stops at each
function boundary and treats that body as its own scope.

Deliberately shallow. It resolves literal string subscripts on names bound to a
`read(...)` call inside the same scope, and nothing else: keys
assembled at runtime are not resolvable here and are not attempted. A cheap
check that catches renames is worth more than a complete one nobody maintains.
"""

from __future__ import annotations

import ast

# "leer" is the pre-translation name of the reader. It is kept so the check
# still resolves keys if an older revision of the generator is ever examined.
READERS = {"read", "leer"}
FUNCTIONS = (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)


def _walk_within_scope(node: ast.AST):
    """Every node below `node`, without crossing into a nested function.

    A function definition yields nothing: it is its own scope and is visited as
    one. Without that, walking the module body descends through every `def`
    below it and the scoping is undone.
    """
    if isinstance(node, FUNCTIONS):
        return
    yield node
    for child in ast.iter_child_nodes(node):
        yield from _walk_within_scope(child)


def _scopes(tree: ast.Module) -> list[list[ast.stmt]]:
    """The module body and each function body, as separate scopes."""
    bodies = [tree.body]
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            bodies.append(node.body)
    return bodies


def _subscript_literals(node: ast.AST) -> tuple[list[str], ast.AST]:
    """Literal keys down a subscript chain, and the expression it rests on."""
    keys: list[str] = []
    while isinstance(node, ast.Subscript):
        if isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, str):
            keys.append(node.slice.value)
        node = node.value
    return keys, node


def _file_read_by(node: ast.AST) -> str | None:
    """The .json literal in `read("x.json")`, including when further subscripted."""
    _, base = _subscript_literals(node)
    if (
        isinstance(base, ast.Call)
        and isinstance(base.func, ast.Name)
        and base.func.id in READERS
        and base.args
        and isinstance(base.args[0], ast.Constant)
        and isinstance(base.args[0].value, str)
        and base.args[0].value.endswith(".json")
    ):
        return base.args[0].value
    return None


def _literal_keys_on(name: str, body: list[ast.stmt]) -> set[str]:
    """Literal string keys subscripted off `name` within this scope only."""
    keys: set[str] = set()
    for statement in body:
        for node in _walk_within_scope(statement):
            if isinstance(node, ast.Subscript):
                chain, base = _subscript_literals(node)
                if isinstance(base, ast.Name) and base.id == name:
                    keys.update(chain)
    return keys


def subscript_keys_by_file(source: str) -> dict[str, set[str]]:
    """Map each result file to the literal keys the generator reads from it."""
    tree = ast.parse(source)
    found: dict[str, set[str]] = {}

    for body in _scopes(tree):
        for statement in body:
            for node in _walk_within_scope(statement):
                if not isinstance(node, ast.Assign) or len(node.targets) != 1:
                    continue
                target = node.targets[0]
                if not isinstance(target, ast.Name):
                    continue
                name = _file_read_by(node.value)
                if name is None:
                    continue
                # Keys taken on the assignment itself, plus those taken on the
                # name anywhere in the scope that bound it.
                on_assignment, _ = _subscript_literals(node.value)
                keys = set(on_assignment) | _literal_keys_on(target.id, body)
                found.setdefault(name, set()).update(keys)

    return found
