"""Safety validator for player-submitted constraint expressions.

Provides ``CreatorRuleValidator`` which validates expressions using
AST-based analysis with a whitelist of allowed node types and variable names.
Used as a safety layer before ``safe_eval`` when accepting user-authored rules.
"""

import ast
import re


class CreatorRuleValidator:
    """Safety validator for player-submitted constraint expressions.

    Only allows boolean/comparison/logic operations on whitelisted variable names.
    Rejects function calls, attribute access, imports, dunder names, and
    variables not in the allowed set.
    """

    MAX_EXPRESSION_LENGTH = 200
    ALLOWED_OPERATORS = {
        ast.Eq, ast.NotEq, ast.Gt, ast.Lt, ast.GtE, ast.LtE,
        ast.And, ast.Or, ast.Not, ast.Constant, ast.Name,
        ast.BoolOp, ast.Compare, ast.UnaryOp, ast.Expression,
        ast.Load,
    }
    FORBIDDEN_NAME_PATTERNS = [
        re.compile(r"^__.*__$"),  # dunder names
        re.compile(r"^_"),        # private variables
    ]

    def __init__(self, allowed_keys: set[str]):
        """Initialize with the set of allowed variable names.

        Args:
            allowed_keys: Set of valid attribute keys (e.g. from clickable_attrs).
        """
        self.allowed_keys = allowed_keys

    def validate(self, expression: str) -> tuple[bool, str]:
        """Validate a player-submitted expression.

        Args:
            expression: The constraint expression string.

        Returns:
            Tuple of (is_valid, reason). reason is "OK" if valid.
        """
        if len(expression) > self.MAX_EXPRESSION_LENGTH:
            return False, f"表达式过长（最大{self.MAX_EXPRESSION_LENGTH}字符，当前{len(expression)}）"

        try:
            tree = ast.parse(expression, mode='eval')
        except SyntaxError as e:
            return False, f"语法错误: {e}"

        for node in ast.walk(tree):
            if type(node) not in self.ALLOWED_OPERATORS:
                return False, f"不允许的语法: {type(node).__name__}"
            if isinstance(node, ast.Name):
                ok, reason = self._validate_name(node.id)
                if not ok:
                    return False, reason
        return True, "OK"

    def _validate_name(self, name: str) -> tuple[bool, str]:
        """Validate a single variable name."""
        # Allow boolean/None literals
        if name.lower() in ("true", "false", "none", "and", "or", "not"):
            return True, "OK"
        # Reject dunder and private variables
        for pattern in self.FORBIDDEN_NAME_PATTERNS:
            if pattern.match(name):
                return False, f"不允许的变量名: {name}"
        # Only allow keys in the allowed set
        if name not in self.allowed_keys:
            sorted_keys = sorted(self.allowed_keys)[:5]
            hint = ', '.join(sorted_keys) + ('...' if len(self.allowed_keys) > 5 else '')
            return False, f"未知属性: {name}（可用: {hint}）"
        return True, "OK"
