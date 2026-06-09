"""State management mixin for OpenAlexLoader."""

import json
import os
from loguru import logger


class StateTrackerMixin:
    """Manages modification timestamps to detect changed OpenAlex data."""

    def _get_level_mtime(self, level: str) -> float:
        """Calculate the max modification time of all files in a level directory."""
        if not getattr(self, "base_path", None):
            return 0.0
        
        level_dir = os.path.join(self.base_path, level)
        if not os.path.exists(level_dir):
            return 0.0
            
        max_mtime = 0.0
        for root, _, files in os.walk(level_dir):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    mtime = os.path.getmtime(file_path)
                    max_mtime = max(max_mtime, mtime)
                except OSError:
                    continue
        return max_mtime

    def _load_previous_state(self) -> dict:
        """Read the previous state from the state file."""
        previous_state = {}
        if getattr(self, "_state_file", None) and os.path.exists(self._state_file):
            try:
                with open(self._state_file, "r") as f:
                    previous_state = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to read state file {self._state_file}: {e}")
        return previous_state

    def _compute_changed_levels(self) -> None:
        """Compare current mtimes against previous state to find changed levels."""
        previous_state = self._load_previous_state()
        self._changed_levels = set()
        self._level_mtimes = {}

        for level in ["domains", "fields", "subfields", "topics"]:
            current_mtime = self._get_level_mtime(level)
            self._level_mtimes[level] = current_mtime
            prev_mtime = previous_state.get(level, 0.0)
            
            if current_mtime > prev_mtime:
                self._changed_levels.add(level)

        if self._changed_levels:
            logger.info(f"Detected changes in levels: {', '.join(self._changed_levels)}")
        else:
            logger.info("No changes detected in OpenAlex data files since last run.")

    def _save_state(self) -> None:
        """Persist the current mtimes to the state file."""
        if getattr(self, "_state_file", None) and getattr(self, "_level_mtimes", None):
            try:
                with open(self._state_file, "w") as f:
                    json.dump(self._level_mtimes, f, indent=2)
                logger.info(f"[OpenAlexLoader] Successfully updated {self._state_file}")
            except Exception as e:
                logger.error(f"Failed to write state file {self._state_file}: {e}")
