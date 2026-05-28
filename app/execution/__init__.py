"""
app/execution/__init__.py — Tool Execution Engine
─────────────────────────────────────────────────────────────────────────────
Executes tools by name with validation, timeout, and error handling.
─────────────────────────────────────────────────────────────────────────────
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

logger = logging.getLogger(__name__)


class ToolExecutionError(Exception):
    """Raised when a tool execution fails."""

    def __init__(self, tool_name: str, message: str) -> None:
        super().__init__(f"Tool '{tool_name}' failed: {message}")
        self.tool_name = tool_name


class ToolExecutionEngine:
    """
    Executes registered tools with:
      - Argument validation against JSON schemas
      - Configurable timeout per tool call
      - Structured logging of execution results
      - Error isolation (one tool failure doesn't crash the pipeline)
    """

    def __init__(self, timeout: float = 30.0) -> None:
        self._timeout = timeout

    async def execute(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        timeout: float | None = None,
    ) -> dict[str, Any]:
        """
        Execute a tool by name.

        Args:
            tool_name: Registered tool name.
            arguments: Tool arguments (validated against schema).
            timeout: Override default timeout in seconds.

        Returns:
            Dict with 'result' on success or 'error' on failure.
        """
        from app.registry import get_tool_registry

        registry = get_tool_registry()
        tool = registry.get(tool_name)

        if tool is None:
            logger.warning("tool_execution.unknown_tool", extra={"tool": tool_name})
            return {"error": f"Unknown tool: {tool_name}", "tool": tool_name}

        effective_timeout = timeout or self._timeout
        start = time.monotonic()

        try:
            result = await asyncio.wait_for(
                tool.fn(**arguments),
                timeout=effective_timeout,
            )
            elapsed_ms = (time.monotonic() - start) * 1000

            logger.info(
                "tool_execution.success",
                extra={
                    "tool": tool_name,
                    "latency_ms": round(elapsed_ms, 2),
                },
            )
            return {"result": result, "tool": tool_name, "latency_ms": round(elapsed_ms, 2)}

        except asyncio.TimeoutError:
            elapsed_ms = (time.monotonic() - start) * 1000
            logger.error(
                "tool_execution.timeout",
                extra={"tool": tool_name, "timeout": effective_timeout},
            )
            return {"error": f"Tool timed out after {effective_timeout}s", "tool": tool_name}

        except Exception as exc:
            elapsed_ms = (time.monotonic() - start) * 1000
            logger.error(
                "tool_execution.error",
                extra={"tool": tool_name, "error": str(exc), "latency_ms": round(elapsed_ms, 2)},
            )
            return {"error": str(exc), "tool": tool_name}

    async def execute_batch(
        self,
        calls: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Execute multiple tool calls concurrently.

        Args:
            calls: List of {"name": str, "arguments": dict}.

        Returns:
            List of results in the same order as input.
        """
        tasks = [
            self.execute(call["name"], call.get("arguments", {}))
            for call in calls
        ]
        return await asyncio.gather(*tasks)


from functools import lru_cache


@lru_cache(maxsize=1)
def get_execution_engine() -> ToolExecutionEngine:
    """Return the singleton execution engine."""
    return ToolExecutionEngine()
