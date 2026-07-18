import ast
import re

_TRUE_FALSE_RE = re.compile(r'\btrue\b|\bfalse\b', re.IGNORECASE)

def _replace_true_false(expr: str) -> str:
    """Replace 'true'/'false' with 'True'/'False' using word boundaries."""
    def _replace(m):
        return 'True' if m.group(0).lower() == 'true' else 'False'
    return _TRUE_FALSE_RE.sub(_replace, expr)


class _SafeEval(ast.NodeVisitor):
    """AST node visitor that evaluates safe expressions (comparisons, bool ops, unary ops)."""

    def __init__(self, env: dict):
        self.env = env

    def eval(self, node: ast.AST) -> bool:
        return bool(self.visit(node))

    def visit_Expression(self, node: ast.Expression) -> bool:
        return self.visit(node.body)

    def visit_BoolOp(self, node: ast.BoolOp) -> bool:
        if isinstance(node.op, ast.And):
            return all(self.visit(v) for v in node.values)
        elif isinstance(node.op, ast.Or):
            return any(self.visit(v) for v in node.values)
        raise ValueError(f"Unsupported BoolOp: {type(node.op).__name__}")

    def visit_Compare(self, node: ast.Compare) -> bool:
        left = self.visit(node.left)
        for op, comparator in zip(node.ops, node.comparators):
            right = self.visit(comparator)
            if not self._compare(left, op, right):
                return False
            left = right
        return True

    def visit_UnaryOp(self, node: ast.UnaryOp) -> bool:
        if isinstance(node.op, ast.Not):
            return not self.visit(node.operand)
        raise ValueError(f"Unsupported UnaryOp: {type(node.op).__name__}")

    def visit_Constant(self, node: ast.Constant) -> bool:
        return node.value

    def visit_Name(self, node: ast.Name) -> bool:
        if node.id in self.env:
            return self.env[node.id]
        return None  # Missing variable returns None (falsy)

    def visit_Call(self, node: ast.Call) -> bool:
        raise ValueError("Function calls are not allowed")

    def visit_Attribute(self, node: ast.Attribute) -> bool:
        raise ValueError("Attribute access is not allowed")

    def visit_Import(self, node: ast.Import) -> bool:
        raise ValueError("Imports are not allowed")

    def visit_ImportFrom(self, node: ast.ImportFrom) -> bool:
        raise ValueError("Imports are not allowed")

    def visit_Lambda(self, node: ast.Lambda) -> bool:
        raise ValueError("Lambda expressions are not allowed")

    def visit_ListComp(self, node: ast.ListComp) -> bool:
        raise ValueError("List comprehensions are not allowed")

    def visit_DictComp(self, node: ast.DictComp) -> bool:
        raise ValueError("Dict comprehensions are not allowed")

    def visit_SetComp(self, node: ast.SetComp) -> bool:
        raise ValueError("Set comprehensions are not allowed")

    def visit_GeneratorExp(self, node: ast.GeneratorExp) -> bool:
        raise ValueError("Generator expressions are not allowed")

    def visit_Subscript(self, node: ast.Subscript) -> bool:
        raise ValueError("Subscript access is not allowed")

    def visit_JoinedStr(self, node: ast.JoinedStr) -> bool:
        raise ValueError("F-strings are not allowed")

    def visit_Starred(self, node: ast.Starred) -> bool:
        raise ValueError("Starred expressions are not allowed")

    def visit_IfExp(self, node: ast.IfExp) -> bool:
        if self.visit(node.test):
            return self.visit(node.body)
        return self.visit(node.orelse)

    def _compare(self, left, op, right) -> bool:
        try:
            if isinstance(op, ast.Eq):
                return left == right
            elif isinstance(op, ast.NotEq):
                return left != right
            elif isinstance(op, ast.Gt):
                return left > right
            elif isinstance(op, ast.GtE):
                return left >= right
            elif isinstance(op, ast.Lt):
                return left < right
            elif isinstance(op, ast.LtE):
                return left <= right
            raise ValueError(f"Unsupported comparison: {type(op).__name__}")
        except TypeError:
            return False


def safe_eval(expr: str, env: dict) -> bool:
    """Evaluate an expression safely using AST parsing.

    Args:
        expr: The expression string to evaluate.
        env: Dictionary of variable names to values.

    Returns:
        Boolean result of the expression.

    Raises:
        ValueError: If the expression contains disallowed constructs.
    """
    expr = _replace_true_false(expr.strip())
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError as e:
        raise ValueError(f"Syntax error: {e}") from e

    # Check for dunder names in the AST
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id.startswith('__') and node.id.endswith('__'):
            raise ValueError(f"Dunder names are not allowed: {node.id}")

    evaluator = _SafeEval(env)
    return evaluator.eval(tree)
