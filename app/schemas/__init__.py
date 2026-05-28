"""
app/schemas/__init__.py — Tool Schema Validation
─────────────────────────────────────────────────────────────────────────────
Validates tool arguments against JSON Schema before execution.
─────────────────────────────────────────────────────────────────────────────
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class SchemaValidationError(Exception):
    """Raised when tool arguments don't match the expected schema."""

    def __init__(self, tool_name: str, errors: list[str]) -> None:
        msg = f"Schema validation failed for '{tool_name}': {'; '.join(errors)}"
        super().__init__(msg)
        self.tool_name = tool_name
        self.errors = errors


def validate_arguments(
    tool_name: str,
    arguments: dict[str, Any],
    schema: dict,
) -> list[str]:
    """
    Validate tool arguments against a JSON Schema.

    Args:
        tool_name: Tool name (for error messages).
        arguments: Arguments to validate.
        schema: JSON Schema dict with 'properties' and 'required'.

    Returns:
        List of validation error strings (empty = valid).
    """
    errors: list[str] = []

    # Check required fields
    required = schema.get("required", [])
    for field in required:
        if field not in arguments:
            errors.append(f"Missing required field: '{field}'")

    # Check types
    properties = schema.get("properties", {})
    type_map = {
        "string": str,
        "integer": int,
        "number": (int, float),
        "boolean": bool,
        "object": dict,
        "array": list,
    }

    for key, value in arguments.items():
        if key not in properties:
            continue  # Extra fields are allowed

        expected_type = properties[key].get("type")
        if expected_type and expected_type in type_map:
            python_type = type_map[expected_type]
            if not isinstance(value, python_type):
                errors.append(
                    f"Field '{key}': expected {expected_type}, got {type(value).__name__}"
                )

    if errors:
        logger.warning(
            "schema_validation.failed",
            extra={"tool": tool_name, "error_count": len(errors)},
        )

    return errors


def validate_or_raise(
    tool_name: str,
    arguments: dict[str, Any],
    schema: dict,
) -> None:
    """Validate arguments and raise SchemaValidationError if invalid."""
    errors = validate_arguments(tool_name, arguments, schema)
    if errors:
        raise SchemaValidationError(tool_name, errors)
