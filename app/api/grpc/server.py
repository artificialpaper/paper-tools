"""gRPC Server bootstrap for paper-tools."""
import grpc.aio
from proto.tools import execution_pb2_grpc, registry_pb2_grpc
from paper_common.grpc.server import create_server, GRPCServerConfig
from paper_common.grpc.interceptors import TraceIDInterceptor, LoggingInterceptor
from paper_common.grpc.health import PaperHealthServicer
from paper_common.logging.logger import get_logger
from ...config.settings import get_settings
from ...infrastructure.registry.store import ToolRegistryStore
from ...infrastructure.sandbox.runner import SandboxRunner
from ...services.executor import ToolExecutionService
from .servicer import ToolServiceServicer, ToolRegistryServiceServicer

log = get_logger(__name__)


def build_app_server() -> grpc.aio.Server:
    """Build and configure paper-tools gRPC server."""
    settings = get_settings()

    # 1. Initialize registry, sandbox & service
    registry = ToolRegistryStore()
    sandbox = SandboxRunner()
    service = ToolExecutionService(registry, sandbox)

    # 2. Create gRPC server with paper-common interceptors
    cfg = GRPCServerConfig(
        host=settings.grpc_host,
        port=settings.grpc_port,
        interceptors=[
            TraceIDInterceptor(),
            LoggingInterceptor(log),
        ],
    )
    server = create_server(config=cfg)

    # 3. Register servicers
    exec_servicer = ToolServiceServicer(service)
    reg_servicer = ToolRegistryServiceServicer(service)
    health_servicer = PaperHealthServicer(service_name=settings.service_name)

    execution_pb2_grpc.add_ToolServiceServicer_to_server(exec_servicer, server)
    registry_pb2_grpc.add_ToolRegistryServiceServicer_to_server(reg_servicer, server)
    health_servicer.register(server)

    log.info("paper_tools.server_built", host=settings.grpc_host, port=settings.grpc_port)
    return server
