"""Validate LLM categorization responses against predefined category lists."""

from __future__ import annotations

import json
import re
from typing import Any

from backend.categorizer.prompts import VALID_CATEGORIES


def parse_llm_response(raw: str) -> dict[str, Any]:
    """Parse raw LLM response string into a dict.

    Handles JSON wrapped in markdown code fences or buried in reasoning text.
    Returns empty dict on any parse failure.
    """
    text = raw.strip()
    # Strip markdown code fences if present
    if text.startswith("```"):
        # Remove first line (```json or ```)
        first_newline = text.find("\n")
        if first_newline != -1:
            text = text[first_newline + 1 :]
        # Remove trailing ```
        if text.rstrip().endswith("```"):
            text = text.rstrip()[: -len("```")].rstrip()

    # Try direct parse first
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        pass

    # ponytail: extract last JSON object from mixed text (LLM reasoning + JSON)
    matches = re.findall(r"\{[^{}]*\}", text)
    if matches:
        try:
            return json.loads(matches[-1])
        except (json.JSONDecodeError, ValueError):
            pass

    return {}


def validate_category(dimension: str, value: str | None) -> str:
    """Validate a single category value against the predefined list.

    Returns the value if valid, 'Not specified' if None and dimension supports it,
    'Other' otherwise. Invalid values also map to 'Not specified' or 'Other'.
    """
    valid = VALID_CATEGORIES.get(dimension, [])
    if not valid:
        return "Other"

    not_specified = "Not specified" if "Not specified" in valid else "Other"

    if value is None:
        return not_specified

    # Exact match
    if value in valid:
        return value

    # Case-insensitive match
    lower_map = {v.lower(): v for v in valid}
    if value.lower() in lower_map:
        return lower_map[value.lower()]

    # Invalid → not specified (dimensions with numeric meaning) or Other
    if dimension in ("size", "inquiry_volume"):
        return not_specified
    return "Other"


def validate_response(raw: str) -> dict[str, Any]:
    """Parse and validate an LLM response, returning cleaned categorization dict.

    - Parses JSON (handles code fences)
    - Validates each dimension against predefined lists
    - Maps invalid values to fallback ('Other' or sensible default)
    - Converts inquiry_volume bucket to integer for DB storage
    - Returns empty dict if parsing fails entirely
    """
    data = parse_llm_response(raw)
    if not data:
        return {}

    result = {}
    for dim in VALID_CATEGORIES:
        value = data.get(dim)
        result[dim] = validate_category(dim, value)

    return result
