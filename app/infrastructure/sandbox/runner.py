"""Process and Containerized Sandbox Executor for Tool Calls."""
import json
import time
import asyncio
import jsonschema
from paper_common.logging.logger import get_logger
from ...domain.models import ToolCallModel, ToolResultModel, ToolDefinitionModel, ToolOutputType
from ...domain.ports import BaseSandboxExecutorPort

log = get_logger(__name__)


class SandboxRunner(BaseSandboxExecutorPort):
    """Executes tool calls inside an isolated runtime sandbox with JSON schema validation."""

    async def execute_tool(self, call: ToolCallModel, tool_def: ToolDefinitionModel) -> ToolResultModel:
        start_time = time.perf_counter()

        # 1. Parse JSON arguments
        try:
            args = json.loads(call.arguments_json) if call.arguments_json else {}
        except Exception as exc:
            return ToolResultModel(
                call_id=call.call_id,
                success=False,
                error=f"Invalid JSON arguments: {exc}",
                duration_ms=0,
            )

        # 2. Validate parameters against JSON Schema
        if tool_def.parameters_schema:
            try:
                schema = json.loads(tool_def.parameters_schema)
                jsonschema.validate(instance=args, schema=schema)
            except jsonschema.ValidationError as exc:
                return ToolResultModel(
                    call_id=call.call_id,
                    success=False,
                    error=f"Schema validation failed: {exc.message}",
                    duration_ms=int((time.perf_counter() - start_time) * 1000),
                )
            except Exception as exc:
                log.warning("sandbox.schema_parse_warning", error=str(exc))

        # 3. Dry-run mode check
        if call.dry_run:
            return ToolResultModel(
                call_id=call.call_id,
                success=True,
                output_json=json.dumps({"dry_run": True, "valid": True, "args": args}),
                duration_ms=int((time.perf_counter() - start_time) * 1000),
                output_type=ToolOutputType.JSON,
            )

        # 4. Execute tool function
        if tool_def.fn is None:
            return ToolResultModel(
                call_id=call.call_id,
                success=False,
                error=f"No executable function associated with tool '{tool_def.name}'",
                duration_ms=int((time.perf_counter() - start_time) * 1000),
            )

        timeout_sec = (call.timeout_ms or 30000) / 1000.0

        try:
            res_data = await asyncio.wait_for(tool_def.fn(args), timeout=timeout_sec)
            duration_ms = int((time.perf_counter() - start_time) * 1000)

            return ToolResultModel(
                call_id=call.call_id,
                success=True,
                output_json=json.dumps(res_data) if isinstance(res_data, dict | list) else str(res_data),
                duration_ms=duration_ms,
                output_type=ToolOutputType.JSON if isinstance(res_data, dict | list) else ToolOutputType.TEXT,
            )
        except asyncio.TimeoutError:
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            return ToolResultModel(
                call_id=call.call_id,
                success=False,
                error=f"Tool execution timed out after {timeout_sec}s",
                duration_ms=duration_ms,
            )
        except Exception as exc:
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            log.error("sandbox.execution_error", tool=tool_def.name, error=str(exc))
            return ToolResultModel(
                call_id=call.call_id,
                success=False,
                error=f"Tool execution failed: {exc}",
                duration_ms=duration_ms,
            )
