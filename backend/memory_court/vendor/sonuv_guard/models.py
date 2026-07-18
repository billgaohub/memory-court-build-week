from enum import Enum
import time

class CommitAction(Enum):
    COMMIT = 1   # Allowed to save normally
    REPAIR = 2   # Modified before saving to resolve boundaries
    REJECT = 3   # Complete rejection of proposed change
    FORGET = 4   # Erases specific memory blocks and resets

class VerificationResult:
    def __init__(self, action: CommitAction, state: dict, reason: str = "", forget_keys: list = None):
        self.action = action
        self.state = state
        self.reason = reason
        self.forget_keys = forget_keys or []

    def __repr__(self):
        return f"<VerificationResult action={self.action.name} reason='{self.reason}'>"

class CognitiveState:
    def __init__(self, npc_id: str, attributes: dict = None, version: int = 1, timestamp: float = None):
        self.npc_id = npc_id
        self.attributes = attributes if attributes is not None else {}
        self.version = version
        self.timestamp = timestamp if timestamp is not None else time.time()

    def to_dict(self) -> dict:
        return {
            "npc_id": self.npc_id,
            "version": self.version,
            "timestamp": self.timestamp,
            "attributes": self.attributes
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'CognitiveState':
        return cls(
            npc_id=data.get("npc_id"),
            attributes=data.get("attributes", {}),
            version=data.get("version", 1),
            timestamp=data.get("timestamp")
        )
