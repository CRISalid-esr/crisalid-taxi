"""Unit tests for the StateTracker class."""

import json
import os
import tempfile
import pytest

from app.services.loading.state import StateTracker


def test_state_tracker_no_previous_state(temp_openalex_dir):
    """Test that all levels are marked as changed when there is no state file."""
    state_file = os.path.join(temp_openalex_dir, "state.json")
    tracker = StateTracker(base_path=temp_openalex_dir, state_file=state_file)

    tracker.compute_changed_levels()

    assert tracker.changed_levels == {"domains", "fields", "subfields", "topics"}
    assert all(mtime > 0.0 for mtime in tracker.level_mtimes.values())


def test_state_tracker_save_and_detect_no_changes(temp_openalex_dir):
    """Test that no changes are detected after saving the state."""
    state_file = os.path.join(temp_openalex_dir, "state.json")
    tracker = StateTracker(base_path=temp_openalex_dir, state_file=state_file)

    # First run: computes changes and saves state
    tracker.compute_changed_levels()
    tracker.save_state()

    assert os.path.exists(state_file)

    # Second run: should detect NO changes
    new_tracker = StateTracker(base_path=temp_openalex_dir, state_file=state_file)
    new_tracker.compute_changed_levels()

    assert new_tracker.changed_levels == set()


def test_state_tracker_detect_modified_level(temp_openalex_dir):
    """Test that changes are detected for a level if a file in it is modified."""
    state_file = os.path.join(temp_openalex_dir, "state.json")
    tracker = StateTracker(base_path=temp_openalex_dir, state_file=state_file)

    tracker.compute_changed_levels()
    tracker.save_state()

    # Modify one of the level files (e.g. fields)
    field_file = os.path.join(temp_openalex_dir, "fields", "20260101", "part_0.ndjson")

    # Update modification time to be in the future
    current_mtime = os.path.getmtime(field_file)
    os.utime(field_file, (current_mtime + 10, current_mtime + 10))

    # Re-run tracker
    new_tracker = StateTracker(base_path=temp_openalex_dir, state_file=state_file)
    new_tracker.compute_changed_levels()

    assert new_tracker.changed_levels == {"fields"}
