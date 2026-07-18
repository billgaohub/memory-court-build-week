import json
import os
import copy
import logging
from .models import CognitiveState

logger = logging.getLogger(__name__)

CURRENT_SCHEMA_VERSION = 1

class StateStore:
    def __init__(self, storage_dir: str = None):
        self.storage_dir = storage_dir
        self._memory_db = {}
        if storage_dir:
            os.makedirs(storage_dir, exist_ok=True)

    def _validate_npc_id(self, npc_id: str):
        if ".." in npc_id or "/" in npc_id or "\\" in npc_id:
            raise ValueError(f"Invalid npc_id: {npc_id}")

    def load(self, npc_id: str) -> dict:
        """Loads state from memory cache or file storage."""
        self._validate_npc_id(npc_id)
        if npc_id in self._memory_db:
            return copy.deepcopy(self._memory_db[npc_id])

        if self.storage_dir:
            filepath = os.path.join(self.storage_dir, f"{npc_id}.json")
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    file_version = data.get("schema_version", 0)
                    if file_version < CURRENT_SCHEMA_VERSION:
                        logger.warning(f"Save file for {npc_id} has schema v{file_version}, "
                                       f"current is v{CURRENT_SCHEMA_VERSION}. Migrating...")
                        data = self._migrate(data, file_version)
                    self._memory_db[npc_id] = data
                    return copy.deepcopy(data)
                except (json.JSONDecodeError, OSError) as e:
                    logger.error(f"Corrupted save file for {npc_id}: {e}")
                    return None

        # Return a fresh state if not found
        default_state = CognitiveState(npc_id).to_dict()
        return default_state

    def _migrate(self, data: dict, from_version: int) -> dict:
        migrated = data.copy()
        if from_version < 1:
            old_keys = {k for k in migrated.get("attributes", {}) if k and not k[0].isalpha()}
            for k in old_keys:
                logger.info(f"Removing legacy key '{k}' from save")
                migrated["attributes"].pop(k, None)
        migrated["schema_version"] = CURRENT_SCHEMA_VERSION
        return migrated

    def save(self, npc_id: str, state_dict: dict):
        """Saves state to cache and persistence files."""
        state_dict = {**state_dict, "schema_version": CURRENT_SCHEMA_VERSION}
        self._memory_db[npc_id] = copy.deepcopy(state_dict)

        if self.storage_dir:
            filepath = os.path.join(self.storage_dir, f"{npc_id}.json")
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(state_dict, f, indent=2, ensure_ascii=False)
            except Exception as e:
                print(f"Error saving persistence state for {npc_id}: {e}")

    def snapshot(self, npc_id: str) -> dict:
        """Obtains a read-only deepcopy snapshot of the state."""
        return copy.deepcopy(self.load(npc_id))
