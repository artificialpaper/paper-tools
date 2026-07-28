"""Tool Execution Orchestration Service."""
from paper_common.logging.logger import get_logger
from paper_common.exceptions.base import NotFoundError
from ..domain.models import ToolCallModel, ToolResultModel, ToolDefinitionModel
from ..domain.ports import BaseToolRegistryPort, BaseSandboxExecutorPort

log = get_logger(__name__)


class ToolExecutionService:
    """Service orchestrating tool lookup, parameter validation, and sandbox execution."""

    def __init__(self, registry: BaseToolRegistryPort, sandbox: BaseSandboxExecutorPort) -> None:
        self.registry = registry
        self.sandbox = sandbox

    def list_tools(self, category: str = "", tags: list[str] | None = None, enabled_only: bool = True) -> list[ToolDefinitionModel]:
        return self.registry.list_tools(category=category, tags=tags, enabled_only=enabled_only)

    def describe_tool(self, name: str) -> ToolDefinitionModel | None:
        return self.registry.get_tool(name)

    async def execute_tool(self, call: ToolCallModel) -> ToolResultModel:
        log.info("tool_service.execute", tool=call.tool_name, call_id=call.call_id, dry_run=call.dry_run)
        tool_def = self.registry.get_tool(call.tool_name)
        if not tool_def:
            log.warning("tool_service.tool_not_found", tool=call.tool_name)
            return ToolResultModel(
                call_id=call.call_id,
                success=False,
                error=f"Tool '{call.tool_name}' not found in registry",
                duration_ms=0,
            )

        return await self.sandbox.execute_tool(call, tool_def)
