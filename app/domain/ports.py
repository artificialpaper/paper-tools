"""Domain ports (interfaces) for paper-tools registry and sandbox execution."""
from abc import ABC, abstractmethod
from .models import ToolCallModel, ToolResultModel, ToolDefinitionModel


class BaseToolRegistryPort(ABC):
    """Abstract interface for managing registered tools."""

    @abstractmethod
    def register(self, tool: ToolDefinitionModel) -> None:
        """Register a new tool."""
        pass

    @abstractmethod
    def get_tool(self, name: str) -> ToolDefinitionModel | None:
        """Get a tool definition by name."""
        pass

    @abstractmethod
    def list_tools(self, category: str = "", tags: list[str] | None = None, enabled_only: bool = True) -> list[ToolDefinitionModel]:
        """List registered tools matching filters."""
        pass


class BaseSandboxExecutorPort(ABC):
    """Abstract interface for running tools inside an isolated sandbox."""

    @abstractmethod
    async def execute_tool(self, call: ToolCallModel, tool_def: ToolDefinitionModel) -> ToolResultModel:
        """Execute tool call inside sandbox with timeout and safety controls."""
        pass
