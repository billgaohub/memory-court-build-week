import re
from .ast_eval import safe_eval
from .models import CommitAction, VerificationResult
from .sanitize import KeySanitizer


class ConstraintRule:
    def __init__(self, name: str, expression: str, action_on_fail: str, repair_delta: dict = None, forget_keys: list = None):
        self.name = name
        self.expression = expression # e.g., "witnessed_murder == True and suspicion < 50"
        self.action_on_fail = action_on_fail # "reject", "repair", "forget"
        self.repair_delta = repair_delta if repair_delta is not None else {}
        self.forget_keys = forget_keys if forget_keys is not None else []

    def evaluate(self, state_attrs: dict) -> bool:
        """Evaluates the constraint expression safely against state attributes."""
        sanitizer = KeySanitizer()

        # Normalize C# style logical operators to Python equivalents
        expr = self.expression
        expr = expr.replace("&&", " and ").replace("||", " or ")

        # Handle logical NOT: replace '!' not followed by '=' with ' not '
        expr = re.sub(r'!(?!=)', ' not ', expr)

        # Sanitize non-Python-safe identifiers (e.g. 1_extra -> _kx_1_extra)
        # so ast.parse doesn't reject them as invalid decimal literals.
        expr = sanitizer.sanitize_expression(expr)
        safe_env = sanitizer.sanitize_dict(state_attrs)
        try:
            return bool(safe_eval(expr, safe_env))
        except ValueError:
            return False

class Guard:
    def __init__(self, constraints: list[ConstraintRule] = None, recursive: bool = False):
        self.constraints = constraints if constraints is not None else []
        self.recursive = recursive
        self._recursion_depth = 0

    def verify(self, current_state: dict, proposed_delta: dict) -> VerificationResult:
        """
        Validates the proposed delta against constraint rules.
        Returns a VerificationResult specifying COMMIT, REPAIR, REJECT, or FORGET.
        """
        new_attributes = current_state.get("attributes", {}).copy()
        for k, v in proposed_delta.items():
            new_attributes[k] = v

        proposed_state = current_state.copy()
        proposed_state["attributes"] = new_attributes

        for rule in self.constraints:
            if rule.evaluate(new_attributes):
                if rule.action_on_fail == "reject":
                    return VerificationResult(
                        CommitAction.REJECT, 
                        current_state, 
                        f"Violated: {rule.name}"
                    )
                elif rule.action_on_fail == "repair":
                    repaired_attributes = new_attributes.copy()
                    for k, v in rule.repair_delta.items():
                        repaired_attributes[k] = v
                    if self.recursive:
                        repaired_state = {**current_state, "attributes": repaired_attributes}
                        if self._recursion_depth >= 5:
                            import logging
                            logging.error(f"REPAIR recursion depth exceeded ({self._recursion_depth}). "
                                          f"Rules may form a cycle. Returning REJECT.")
                            return VerificationResult(CommitAction.REJECT, current_state,
                                                      "Recursion depth exceeded")
                        child = Guard(self.constraints, recursive=True)
                        child._recursion_depth = self._recursion_depth + 1
                        child_result = child.verify(repaired_state, {})
                        if child_result.action == CommitAction.COMMIT:
                            proposed_state["attributes"] = repaired_attributes
                            return VerificationResult(
                                CommitAction.REPAIR, proposed_state,
                                f"Repaired by: {rule.name}"
                            )
                        return child_result
                    proposed_state["attributes"] = repaired_attributes
                    return VerificationResult(
                        CommitAction.REPAIR, 
                        proposed_state, 
                        f"Repaired by: {rule.name}"
                    )
                elif rule.action_on_fail == "forget":
                    return VerificationResult(
                        CommitAction.FORGET,
                        current_state,
                        f"Forget triggered by: {rule.name}",
                        forget_keys=rule.forget_keys,
                    )
                else:
                    raise ValueError(f"Unknown action_on_fail: {rule.action_on_fail}")

        return VerificationResult(CommitAction.COMMIT, proposed_state, "Verified.")
