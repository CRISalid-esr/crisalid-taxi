"""OpenAlex loading helpers."""

import json
import os
from typing import Any

from loguru import logger


def read_ndjson_entity_dir(base_path: str, dir_name: str) -> list[dict[str, Any]]:
    """Read all NDJSON records from a dated entity directory."""
    entity_dir = os.path.join(base_path, dir_name)
    if not os.path.exists(entity_dir):
        logger.warning(f"Entity directory not found: {entity_dir}")
        return []

    records: list[dict[str, Any]] = []
    try:
        for date_dir in sorted(os.listdir(entity_dir)):
            date_path = os.path.join(entity_dir, date_dir)
            if not os.path.isdir(date_path):
                continue

            for part_file in sorted(os.listdir(date_path)):
                file_path = os.path.join(date_path, part_file)
                try:
                    with open(file_path, encoding="utf-8") as file_handle:
                        for line_num, line in enumerate(file_handle, 1):
                            line = line.strip()
                            if not line:
                                continue
                            try:
                                records.append(json.loads(line))
                            except json.JSONDecodeError as exc:
                                logger.warning(f"JSON parse error in {file_path}:{line_num}: {exc}")
                except IOError as exc:
                    logger.error(f"Failed to read file {file_path}: {exc}")
        logger.info(f"Loaded {len(records)} records from {dir_name}")
    except Exception as exc:
        logger.error(f"Error reading {dir_name}: {exc}")

    return records


def build_name_lookup(records: list[dict[str, Any]]) -> dict[str, str]:
    """Build a display name lookup keyed by record id."""
    return {record["id"]: record.get("display_name", "?") for record in records}


def build_id_lookup(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Build a record lookup keyed by record id."""
    return {record["id"]: record for record in records}


def build_parent_lookup(
    records: list[dict[str, Any]],
    parent_key: str,
) -> dict[str, str]:
    """Build a parent id lookup keyed by record id."""
    return {record["id"]: (record.get(parent_key) or {}).get("id", "") for record in records}


def build_embedding_text(
    ordered_values: list[str],
    keywords: list[str] | None = None,
) -> str:
    """Build a direct concatenated text payload for embeddings."""
    parts = [
        value.strip().rstrip(",. ")
        for value in ordered_values
        if value and value.strip() and value.strip() != "?"
    ]

    parts.extend(
        keyword.strip().rstrip(",. ") for keyword in keywords or [] if keyword and keyword.strip()
    )

    return ", ".join(parts)
