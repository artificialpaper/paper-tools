"""Tests for paper-tools registry, sandbox execution, and gRPC servicers."""
import json
import pytest
from proto.tools import execution_pb2, registry_pb2
from paper_tools.domain.models import ToolCallModel, ToolDefinitionModel
from paper_tools.infrastructure.registry.store import ToolRegistryStore
from paper_tools.infrastructure.sandbox.runner import SandboxRunner
from paper_tools.services.executor import ToolExecutionService
from paper_tools.api.grpc.servicer import ToolServiceServicer, ToolRegistryServiceServicer
from paper_tools.api.grpc.server import build_app_server


@pytest.mark.asyncio
async def test_tool_registry_list_and_get():
    """Verify tool registration, filtering, and retrieval."""
    registry = ToolRegistryStore()

    tools = registry.list_tools()
    assert len(tools) >= 4  # read_file, write_file, execute_python, web_search

    file_tools = registry.list_tools(category="file")
    assert len(file_tools) >= 2

    tool = registry.get_tool("read_file")
    assert tool is not None
    assert tool.name == "read_file"


@pytest.mark.asyncio
async def test_sandbox_runner_execute():
    """Verify sandbox runner executes python snippet and validates schema."""
    registry = ToolRegistryStore()
    sandbox = SandboxRunner()

    tool_def = registry.get_tool("execute_python")
    assert tool_def is not None

    call = ToolCallModel(
        call_id="call_101",
        tool_name="execute_python",
        arguments_json=json.dumps({"code": "x = 42; y = x * 2"}),
    )

    res = await sandbox.execute_tool(call, tool_def)
    assert res.success is True
    assert "84" in res.output_json


@pytest.mark.asyncio
async def test_sandbox_runner_schema_validation_failure():
    """Verify sandbox runner rejects invalid JSON arguments according to schema."""
    registry = ToolRegistryStore()
    sandbox = SandboxRunner()

    tool_def = registry.get_tool("read_file")
    assert tool_def is not None

    # Missing required 'path' parameter
    call = ToolCallModel(
        call_id="call_102",
        tool_name="read_file",
        arguments_json=json.dumps({}),
    )

    res = await sandbox.execute_tool(call, tool_def)
    assert res.success is False
    assert "Schema validation failed" in res.error


@pytest.mark.asyncio
async def test_tool_grpc_servicers():
    """Verify ToolService and ToolRegistryService gRPC handlers."""
    registry = ToolRegistryStore()
    sandbox = SandboxRunner()
    service = ToolExecutionService(registry, sandbox)

    exec_servicer = ToolServiceServicer(service)
    reg_servicer = ToolRegistryServiceServicer(service)

    # gRPC List
    list_req = registry_pb2.ListToolsRequest(category="search")
    list_res = await reg_servicer.List(list_req, None)
    assert list_res.total_count >= 1
    assert list_res.tools[0].name == "web_search"

    # gRPC Execute (Dry Run)
    exec_req = execution_pb2.ToolExecuteRequest(
        call=execution_pb2.ToolCall(
            call_id="call_200",
            tool_name="web_search",
            arguments=json.dumps({"query": "Paper AI"}),
        ),
        dry_run=True,
    )
    exec_res = await exec_servicer.Execute(exec_req, None)
    assert exec_res.result.success is True
    assert "dry_run" in exec_res.result.output


@pytest.mark.asyncio
async def test_build_app_server():
    """Verify gRPC server builds and binds cleanly."""
    server = build_app_server()
    port = server.add_insecure_port("127.0.0.1:0")
    assert port > 0
    await server.start()
    await server.stop(grace=0)
