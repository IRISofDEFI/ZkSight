"""
Example of using distributed tracing with agents.

This example demonstrates how to:
1. Initialize tracing for an agent
2. Process messages with automatic trace propagation
3. View traces in Jaeger UI
"""
import logging
import time
from typing import Dict, Any, Type

from ..config import load_config
from ..messaging import ConnectionPool, BaseAgent, get_connection_pool
from ..init_tracing import init_agent_tracing, shutdown_agent_tracing
from ..tracing import trace_agent_operation, set_span_attribute, add_span_event

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ExampleTracedAgent(BaseAgent):
    """
    Example agent demonstrating distributed tracing.
    
    This agent:
    - Receives messages on "example.request" routing key
    - Processes them with traced operations
    - Publishes responses on "example.response" routing key
    """
    
    AGENT_NAME = "example_traced_agent"
    EXCHANGE_NAME = "chimera.events"
    
    ROUTING_KEY_REQUEST = "example.request"
    ROUTING_KEY_RESPONSE = "example.response"
    
    def get_routing_key_map(self) -> Dict[str, Type]:
        """No proto messages for this example"""
        return {}
    
    def route_message(
        self,
        message: Any,
        routing_key: str,
        properties: Dict[str, Any]
    ) -> None:
        """Route incoming messages"""
        if routing_key == self.ROUTING_KEY_REQUEST:
            self._handle_request(message, properties)
        else:
            logger.warning(f"Unknown routing key: {routing_key}")
    
    def _handle_request(
        self,
        message: Any,
        properties: Dict[str, Any]
    ) -> None:
        """
        Handle example request with tracing.
        
        This method demonstrates:
        - Automatic trace context extraction from message headers
        - Manual span creation for operations
        - Adding custom attributes and events
        """
        correlation_id = properties.get("correlation_id", "unknown")
        
        logger.info(f"Processing request: {correlation_id}")
        
        # Perform some traced operations
        result = self.process_with_tracing(correlation_id)
        
        logger.info(f"Request processed: {correlation_id}, result={result}")
    
    @trace_agent_operation("process_example_request")
    def process_with_tracing(self, correlation_id: str) -> Dict[str, Any]:
        """
        Example processing with tracing decorators.
        
        The @trace_agent_operation decorator automatically:
        - Creates a span for this operation
        - Records exceptions if they occur
        - Sets the span status
        """
        # Add custom attributes
        set_span_attribute("request.correlation_id", correlation_id)
        set_span_attribute("processing.stage", "validation")
        
        # Simulate validation
        add_span_event("validation.start")
        time.sleep(0.1)  # Simulate work
        add_span_event("validation.complete")
        
        # Simulate processing
        set_span_attribute("processing.stage", "execution")
        add_span_event("execution.start")
        time.sleep(0.2)  # Simulate work
        add_span_event("execution.complete")
        
        # Simulate data storage
        set_span_attribute("processing.stage", "storage")
        add_span_event("storage.start")
        time.sleep(0.1)  # Simulate work
        add_span_event("storage.complete")
        
        return {
            "status": "success",
            "correlation_id": correlation_id,
            "processing_time_ms": 400,
        }


def main():
    """
    Main function demonstrating agent with tracing.
    
    Steps:
    1. Initialize tracing (connects to Jaeger)
    2. Create and start agent
    3. Agent processes messages with automatic trace propagation
    4. View traces at http://localhost:16686 (Jaeger UI)
    """
    logger.info("Starting example traced agent...")
    
    # Step 1: Initialize tracing
    # This must be done before creating the agent
    init_agent_tracing(
        agent_name="example_traced_agent",
        service_version="1.0.0",
        jaeger_endpoint="http://localhost:4317",
        enable_console_export=True,  # Also print traces to console
    )
    
    # Step 2: Load configuration
    config = load_config()
    
    # Step 3: Create connection pool
    connection_pool = get_connection_pool(
        host=config.rabbitmq.host,
        port=config.rabbitmq.port,
        username=config.rabbitmq.username,
        password=config.rabbitmq.password,
        vhost=config.rabbitmq.vhost,
    )
    
    # Step 4: Create agent
    agent = ExampleTracedAgent(
        connection_pool=connection_pool,
        agent_name=ExampleTracedAgent.AGENT_NAME,
        exchange_name=ExampleTracedAgent.EXCHANGE_NAME,
        routing_keys=[ExampleTracedAgent.ROUTING_KEY_REQUEST],
    )
    
    logger.info("Agent started. Waiting for messages...")
    logger.info("View traces at: http://localhost:16686")
    logger.info("Press Ctrl+C to stop")
    
    try:
        # Step 5: Start consuming messages
        agent.start_consuming()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        # Step 6: Cleanup
        agent.close()
        shutdown_agent_tracing()
        logger.info("Agent stopped")


if __name__ == "__main__":
    main()
