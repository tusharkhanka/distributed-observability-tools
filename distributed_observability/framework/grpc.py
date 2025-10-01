"""
gRPC instrumentation for distributed tracing.
"""
import logging

logger = logging.getLogger(__name__)

try:
    from opentelemetry.instrumentation.grpc import GrpcInstrumentorClient, GrpcInstrumentorServer
    GRPC_AVAILABLE = True
except ImportError:
    GRPC_AVAILABLE = False
    logger.warning("gRPC instrumentation not available")


def instrument_grpc_client(channel):
    """
    Instrument gRPC client channel.
    
    Args:
        channel: gRPC channel instance
    
    Returns:
        Instrumented channel
    
    Example:
        >>> import grpc
        >>> from distributed_observability.framework.grpc import instrument_grpc_client
        >>> 
        >>> channel = grpc.insecure_channel('localhost:50051')
        >>> instrumented_channel = instrument_grpc_client(channel)
    """
    if not GRPC_AVAILABLE:
        logger.error("gRPC instrumentation not available. Install: pip install opentelemetry-instrumentation-grpc")
        return channel
    
    return GrpcInstrumentorClient().instrument_channel(channel)


def instrument_grpc_server(server):
    """
    Instrument gRPC server.
    
    Args:
        server: gRPC server instance
    
    Returns:
        Instrumented server
    
    Example:
        >>> import grpc
        >>> from distributed_observability.framework.grpc import instrument_grpc_server
        >>> 
        >>> server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        >>> instrumented_server = instrument_grpc_server(server)
    """
    if not GRPC_AVAILABLE:
        logger.error("gRPC instrumentation not available. Install: pip install opentelemetry-instrumentation-grpc")
        return server
    
    return GrpcInstrumentorServer().instrument_server(server)

