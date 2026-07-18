from .models import CommitAction, VerificationResult
from .store import StateStore
import copy

class CommitEngine:
    def __init__(self, store: StateStore, max_history: int = 100):
        self.store = store
        self.history = {} # Maps npc_id -> stack of state snapshots
        self.max_history = max_history

    def execute(self, npc_id: str, result: VerificationResult) -> VerificationResult:
        """Executes the transaction action (COMMIT, REPAIR, REJECT, FORGET)."""
        if result.action in (CommitAction.COMMIT, CommitAction.REPAIR):
            if npc_id not in self.history:
                self.history[npc_id] = []
            current_snapshot = self.store.snapshot(npc_id)
            self.history[npc_id].append(current_snapshot)
            if len(self.history[npc_id]) > self.max_history:
                self.history[npc_id] = self.history[npc_id][-self.max_history:]
            self.store.save(npc_id, result.state)
            
        elif result.action == CommitAction.FORGET:
            self.forget(npc_id, result.forget_keys)
            
        elif result.action == CommitAction.REJECT:
            # No-op: keep current store state untouched
            pass

        return result

    def rollback(self, npc_id: str) -> bool:
        """Rolls back the NPC's state to the last successfully committed transaction."""
        if npc_id in self.history and self.history[npc_id]:
            previous_state = self.history[npc_id].pop()
            self.store.save(npc_id, previous_state)
            return True
        return False

    def forget(self, npc_id: str, target_keys: list):
        """Physically purges target keys from the state attributes."""
        current_state = self.store.load(npc_id)
        old_attributes = current_state.get("attributes", {})
        # Immutable: build a brand-new dict, never mutate the original
        new_attributes = {
            k: (None if k in target_keys else v)
            for k, v in old_attributes.items()
        }
        new_state = {**current_state, "attributes": new_attributes}
        self.store.save(npc_id, new_state)

class PromptBuilder:
    @staticmethod
    def build(verified_state: dict, base_persona: str, player_input: str) -> str:
        """
        Builds a compact prompt containing persona, verified JSON states, and input dialogue.
        Excludes raw context histories to optimize token window usage.
        """
        attributes = verified_state.get("attributes", {})
        active_attrs = {k: v for k, v in attributes.items() if v is not None}
        
        return f"""Persona: {base_persona}
Cognitive State: {active_attrs}
Input: "{player_input}"
Generate a concise response matching the State. Do not reveal raw JSON variables."""
