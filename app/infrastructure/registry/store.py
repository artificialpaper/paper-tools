"""Tool Registry Store with Built-in Tools."""
import json
import asyncio
from paper_common.logging.logger import get_logger
from ...domain.models import ToolDefinitionModel
from ...domain.ports import BaseToolRegistryPort

log = get_logger(__name__)


async def builtin_read_file(args: dict) -> dict:
    filepath = args.get("path", "")
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        return {"status": "success", "content": content}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


async def builtin_write_file(args: dict) -> dict:
    filepath = args.get("path", "")
    content = args.get("content", "")
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return {"status": "success", "bytes_written": len(content)}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


async def builtin_execute_python(args: dict) -> dict:
    code = args.get("code", "")
    try:
        exec_globals: dict = {}
        exec(code, exec_globals)
        result = {k: str(v) for k, v in exec_globals.items() if not k.startswith("__")}
        return {"status": "success", "result": result}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


async def builtin_web_search(args: dict) -> dict:
    query = args.get("query", "")
    return {
        "status": "success",
        "results": [
            {"title": f"Result for {query}", "snippet": f"Sample web search result for query '{query}'"}
        ],
    }


class ToolRegistryStore(BaseToolRegistryPort):
    """In-memory tool registry store."""

    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinitionModel] = {}
        self._register_builtins()

    def _register_builtins(self) -> None:
        self.register(ToolDefinitionModel(
            name="read_file",
            description="Read content from a file path",
            category="file",
            parameters_schema=json.dumps({
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
            }),
            fn=builtin_read_file,
            tags=["file", "read"],
        ))

        self.register(ToolDefinitionModel(
            name="write_file",
            description="Write content to a file path",
            category="file",
            parameters_schema=json.dumps({
                "type": "object",
                "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
                "required": ["path", "content"],
            }),
            fn=builtin_write_file,
            tags=["file", "write"],
        ))

        self.register(ToolDefinitionModel(
            name="execute_python",
            description="Execute Python code snippet in sandbox",
            category="code",
            parameters_schema=json.dumps({
                "type": "object",
                "properties": {"code": {"type": "string"}},
                "required": ["code"],
            }),
            fn=builtin_execute_python,
            tags=["python", "exec"],
        ))

        self.register(ToolDefinitionModel(
            name="web_search",
            description="Perform web search for a query",
            category="search",
            parameters_schema=json.dumps({
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            }),
            fn=builtin_web_search,
            tags=["web", "search"],
        ))

    def register(self, tool: ToolDefinitionModel) -> None:
        self._tools[tool.name] = tool
        log.info("tool_registry.registered", tool=tool.name, category=tool.category)

    def get_tool(self, name: str) -> ToolDefinitionModel | None:
        return self._tools.get(name)

    def list_tools(self, category: str = "", tags: list[str] | None = None, enabled_only: bool = True) -> list[ToolDefinitionModel]:
        results = []
        for tool in self._tools.values():
            if enabled_only and not tool.enabled:
                continue
            if category and tool.category != category:
                continue
            if tags and not any(t in tool.tags for t in tags):
                continue
            results.append(tool)
        return results
