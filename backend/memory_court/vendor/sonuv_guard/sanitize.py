"""Key sanitization for non-Python-safe identifiers.

Provides ``KeySanitizer`` which translates arbitrary attribute keys
(e.g. digit-prefixed names like ``1_extra_place_setting``) into valid
Python identifiers so that expressions can be evaluated safely via
``safe_eval``.

String literals inside expressions are preserved untouched.  External
code should use ``KeySanitizer`` to prepare state dicts before calling
``Guard.verify()``.
"""

import keyword
import re
from typing import Dict


class KeySanitizer:
    """Bidirectional mapper between arbitrary attribute keys and valid
    Python identifiers.

    Typical usage::

        sanitizer = KeySanitizer()
        safe_expr = sanitizer.sanitize_expression(rule.expression)
        safe_env  = sanitizer.sanitize_dict(state_attrs)
        result    = safe_eval(safe_expr, safe_env)

    The sanitizer maintains an internal mapping so that
    ``sanitize_dict`` is consistent across calls within the same
    instance.
    """

    _PREFIX = "_kx_"

    # Matches digit-prefixed identifiers: 1_extra, 4_calibration, 2_b1_son_alive …
    # Does NOT match bare numbers (100, 3.14) because \b requires a
    # word→non-word boundary, and there is none between '100' and ' '.
    _RE_DIGIT_ID = re.compile(r"\b(\d+[a-zA-Z_]\w*)")

    # Matches single- or double-quoted string literals (non-greedy).
    _RE_STRING = re.compile(r"(\".*?\"|'.*?')")

    def __init__(self) -> None:
        # original_key -> sanitized_key
        self._forward: Dict[str, str] = {}
        # sanitized_key -> original_key
        self._reverse: Dict[str, str] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @staticmethod
    def is_valid_identifier(key: str) -> bool:
        """Return True if *key* is a valid Python identifier that is
        neither a keyword nor a dunder name."""
        if not key:
            return False
        if keyword.iskeyword(key):
            return False
        if key.startswith("__") and key.endswith("__"):
            return False
        return key.isidentifier()

    def sanitize_key(self, key: str) -> str:
        """Return a valid Python identifier for *key*, registering the
        mapping so that ``original_key`` can later be recovered."""
        if self.is_valid_identifier(key):
            return key
        if key in self._forward:
            return self._forward[key]
        safe = self._PREFIX + re.sub(r"[^0-9a-zA-Z_]", "_", key)
        self._forward[key] = safe
        self._reverse[safe] = key
        return safe

    def sanitize_expression(self, expr: str) -> str:
        """Replace digit-prefixed identifiers in *expr* with safe names.

        String literals (``'foo'``, ``"bar"``) are extracted before the
        replacement and restored afterwards, so their content is never
        modified.
        """
        if not expr or not expr.strip():
            return expr

        # 1. Extract string literals, replace with placeholders.
        strings: list[str] = []

        def _save_string(m: re.Match) -> str:
            strings.append(m.group(0))
            return f"__STR{len(strings) - 1}__"

        no_strings = self._RE_STRING.sub(_save_string, expr)

        # 2. Replace digit-prefixed identifiers using sanitize_key so that
        # the same prefix is used in both expressions and state dicts.
        def _replace_id(m: re.Match) -> str:
            return self.sanitize_key(m.group(1))

        sanitized = self._RE_DIGIT_ID.sub(_replace_id, no_strings)

        # 3. Restore string literals.
        for i, s in enumerate(strings):
            sanitized = sanitized.replace(f"__STR{i}__", s)

        return sanitized

    def sanitize_dict(self, d: Dict[str, object]) -> Dict[str, object]:
        """Return a new dict with every key sanitized via
        ``sanitize_key``.  Values are unchanged."""
        return {self.sanitize_key(k): v for k, v in d.items()}

    def original_key(self, sanitized_key: str) -> str:
        """Reverse-map a sanitized key back to its original form.
        Returns the input unchanged if it was never remapped."""
        return self._reverse.get(sanitized_key, sanitized_key)
