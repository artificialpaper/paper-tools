"""Domain models for paper-tools execution and registry."""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Awaitable

ToolFn = Callable[..., Awaitable[Any]]


class ToolOutputType(str, Enum):
    TEXT = "text"
    JSON = "json"
    TABLE = "table"
    BINARY = "binary"


@dataclass
class ToolDefinitionModel:
    name: str
    description: str
    category: str = "general"
    parameters_schema: str = "{}"
    fn: ToolFn | None = None
    tags: list[str] = field(default_factory=list)
    enabled: bool = True


@dataclass
class ToolCallModel:
    call_id: str
    tool_name: str
    arguments_json: str
    timeout_ms: int = 30000
    dry_run: bool = False


@dataclass
class ToolResultModel:
    call_id: str
    success: bool
    output_json: str = "{}"
    error: str = ""
    duration_ms: int = 0
    output_type: ToolOutputType = ToolOutputType.TEXT
