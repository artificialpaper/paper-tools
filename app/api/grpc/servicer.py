"""gRPC Servicer implementations for paper-tools ToolService and ToolRegistryService."""
import grpc
from proto.tools import execution_pb2, execution_pb2_grpc
from proto.tools import registry_pb2, registry_pb2_grpc
from proto.tools import schemas_pb2
from ...domain.models import ToolCallModel, ToolOutputType
from ...services.executor import ToolExecutionService
from paper_common.logging.logger import get_logger

log = get_logger(__name__)


class ToolServiceServicer(execution_pb2_grpc.ToolServiceServicer):
    """gRPC servicer for tool execution requests."""

    def __init__(self, service: ToolExecutionService) -> None:
        self.service = service

    async def Execute(
        self,
        request: execution_pb2.ToolExecuteRequest,
        context: grpc.aio.ServicerContext,
    ) -> execution_pb2.ToolExecuteResponse:
        p_call = request.call
        domain_call = ToolCallModel(
            call_id=p_call.call_id or "call_1",
            tool_name=p_call.tool_name,
            arguments_json=p_call.arguments,
            timeout_ms=request.timeout_ms or 30000,
            dry_run=request.dry_run,
        )

        domain_res = await self.service.execute_tool(domain_call)

        output_type = execution_pb2.TOOL_OUTPUT_TYPE_TEXT
        if domain_res.output_type == ToolOutputType.JSON:
            output_type = execution_pb2.TOOL_OUTPUT_TYPE_JSON

        proto_result = execution_pb2.ToolResult(
            call_id=domain_res.call_id,
            success=domain_res.success,
            output=domain_res.output_json,
            error=domain_res.error,
            duration_ms=domain_res.duration_ms,
            output_type=output_type,
        )

        return execution_pb2.ToolExecuteResponse(result=proto_result)


class ToolRegistryServiceServicer(registry_pb2_grpc.ToolRegistryServiceServicer):
    """gRPC servicer for tool discovery and registry queries."""

    def __init__(self, service: ToolExecutionService) -> None:
        self.service = service

    async def List(
        self,
        request: registry_pb2.ListToolsRequest,
        context: grpc.aio.ServicerContext,
    ) -> registry_pb2.ListToolsResponse:
        tools = self.service.list_tools(
            category=request.category,
            tags=list(request.tags),
            enabled_only=request.enabled_only,
        )

        summaries = [
            registry_pb2.ToolSummary(
                name=t.name,
                description=t.description,
                category=t.category,
                tags=t.tags,
                enabled=t.enabled,
            )
            for t in tools
        ]

        return registry_pb2.ListToolsResponse(tools=summaries, total_count=len(summaries))

    async def Describe(
        self,
        request: registry_pb2.DescribeToolRequest,
        context: grpc.aio.ServicerContext,
    ) -> registry_pb2.DescribeToolResponse:
        tool = self.service.describe_tool(request.tool_name)
        if not tool:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"Tool '{request.tool_name}' not found")
            return registry_pb2.DescribeToolResponse()

        proto_tool = schemas_pb2.ToolDefinition(
            name=tool.name,
            description=tool.description,
            category=tool.category,
            parameters_schema=tool.parameters_schema,
            tags=tool.tags,
            enabled=tool.enabled,
        )

        return registry_pb2.DescribeToolResponse(tool=proto_tool)
