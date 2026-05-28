"""
app/registry/__init__.py — Tool Registry
─────────────────────────────────────────────────────────────────────────────
Central registry for all callable tools. Manages registration, discovery,
and schema export for LLM function calling.
─────────────────────────────────────────────────────────────────────────────
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any, Callable, Awaitable

logger = logging.getLogger(__name__)

ToolFn = Callable[..., Awaitable[Any]]


@dataclass
class ToolDefinition:
    """OpenAI-compatible function/tool definition."""

    name: str
    description: str
    parameters: dict
    fn: ToolFn
    category: str = "general"
    version: str = "1.0.0"
    schema: dict = field(init=False)

    def __post_init__(self) -> None:
        self.schema = {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


class ToolRegistry:
    """
    Singleton registry for all agent-callable tools.

    Supports:
      - Decorator-based registration
      - Category filtering
      - OpenAI-compatible schema export
      - Tool discovery and listing
    """

    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}

    def register(
        self,
        name: str,
        description: str,
        parameters: dict,
        category: str = "general",
    ) -> Callable[[ToolFn], ToolFn]:
        """Decorator to register a tool function."""

        def decorator(fn: ToolFn) -> ToolFn:
            self._tools[name] = ToolDefinition(
                name=name,
                description=description,
                parameters=parameters,
                fn=fn,
                category=category,
            )
            logger.info("tool_registry.registered", extra={"tool": name, "category": category})
            return fn

        return decorator

    def get(self, name: str) -> ToolDefinition | None:
        """Look up a tool by name."""
        return self._tools.get(name)

    def list_tools(self, category: str | None = None) -> list[str]:
        """List all registered tool names, optionally filtered by category."""
        if category:
            return [n for n, t in self._tools.items() if t.category == category]
        return list(self._tools.keys())

    def schemas(self, category: str | None = None) -> list[dict]:
        """Return all tool schemas for LLM function calling."""
        tools = self._tools.values()
        if category:
            tools = [t for t in tools if t.category == category]
        return [t.schema for t in tools]

    def describe(self, name: str) -> dict | None:
        """Get full description of a tool."""
        tool = self._tools.get(name)
        if not tool:
            return None
        return {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.parameters,
            "category": tool.category,
            "version": tool.version,
        }

    def count(self) -> int:
        return len(self._tools)


@lru_cache(maxsize=1)
def get_tool_registry() -> ToolRegistry:
    """Return the singleton ToolRegistry with all built-in tools registered."""
    registry = ToolRegistry()
    _register_builtin_tools(registry)
    return registry


def _register_builtin_tools(registry: ToolRegistry) -> None:
    """Auto-register all built-in tools."""
    from app.builtin.scheduling.calendar_tool import book_meeting, cancel_meeting, check_availability
    from app.builtin.crm.crm_tool import lookup_contact, update_contact
    from app.builtin.email.email_tool import send_email
    from app.builtin.search.search_tool import web_search

    registry.register(
        name="book_meeting",
        description="Book a calendar meeting for the caller.",
        category="scheduling",
        parameters={
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Meeting title"},
                "date": {"type": "string", "description": "Date in YYYY-MM-DD format"},
                "time": {"type": "string", "description": "Time in HH:MM (24h) format"},
                "duration_min": {"type": "integer", "description": "Duration in minutes"},
                "attendee_email": {"type": "string", "description": "Attendee email"},
            },
            "required": ["title", "date", "time", "duration_min"],
        },
    )(book_meeting)

    registry.register(
        name="cancel_meeting",
        description="Cancel an existing meeting.",
        category="scheduling",
        parameters={
            "type": "object",
            "properties": {
                "meeting_id": {"type": "string", "description": "Meeting ID to cancel"},
            },
            "required": ["meeting_id"],
        },
    )(cancel_meeting)

    registry.register(
        name="check_availability",
        description="Check calendar availability for a given date.",
        category="scheduling",
        parameters={
            "type": "object",
            "properties": {
                "date": {"type": "string", "description": "Date in YYYY-MM-DD format"},
            },
            "required": ["date"],
        },
    )(check_availability)

    registry.register(
        name="lookup_contact",
        description="Look up a contact in the CRM by phone number or name.",
        category="crm",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Phone number or name"},
            },
            "required": ["query"],
        },
    )(lookup_contact)

    registry.register(
        name="update_contact",
        description="Update a CRM contact's information.",
        category="crm",
        parameters={
            "type": "object",
            "properties": {
                "contact_id": {"type": "string"},
                "updates": {"type": "object", "description": "Fields to update"},
            },
            "required": ["contact_id", "updates"],
        },
    )(update_contact)

    registry.register(
        name="send_email",
        description="Send a follow-up email to the caller.",
        category="email",
        parameters={
            "type": "object",
            "properties": {
                "to": {"type": "string", "description": "Recipient email"},
                "subject": {"type": "string"},
                "body": {"type": "string"},
            },
            "required": ["to", "subject", "body"],
        },
    )(send_email)

    registry.register(
        name="web_search",
        description="Search the web for information.",
        category="search",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "max_results": {"type": "integer", "description": "Max results", "default": 5},
            },
            "required": ["query"],
        },
    )(web_search)
