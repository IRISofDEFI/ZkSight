"""Tests for BaseAgent class"""
import pytest
from typing import Dict, Any, Type
from unittest.mock import Mock, MagicMock, patch
from google.protobuf.message import Message as ProtoMessage

from src.messaging.base_agent import BaseAgent
from src.messaging.connection import ConnectionPool


class MockMessage(ProtoMessage):
    """Mock Protocol Buffer message for testing"""
    pass


class TestAgent(BaseAgent):
    """Test agent implementation"""

    def __init__(self, connection_pool: ConnectionPool):
        super().__init__(
            connection_pool=connection_pool,
            agent_name="test_agent",
            routing_keys=["test.request", "test.response"],
        )
        self.handled_messages = []

    def get_routing_key_map(self) -> Dict[str, Type[ProtoMessage]]:
        return {
            "test.request": MockMessage,
            "test.response": MockMessage,
        }

    def route_message(
        self,
        message: ProtoMessage,
        routing_key: str,
        properties: Dict[str, Any]
    ) -> None:
        self.handled_messages.append({
            "message": message,
            "routing_key": routing_key,
            "properties": properties,
        })


@pytest.fixture
def mock_connection_pool():
    """Create mock connection pool"""
    pool = Mock(spec=ConnectionPool)
    pool.get_connection = Mock(return_value=Mock())
    return pool


@pytest.fixture
def test_agent(mock_connection_pool):
    """Create test agent instance"""
    with patch('src.messaging.base_agent.EventPublisher'):
        with patch.object(BaseAgent, '_setup_queue'):
            agent = TestAgent(mock_connection_pool)
            return agent


class TestBaseAgentInitialization:
    """Test BaseAgent initialization"""

    def test_initialization(self, mock_connection_pool):
        """Test agent initializes correctly"""
        with patch('src.messaging.base_agent.EventPublisher'):
            with patch.object(BaseAgent, '_setup_queue'):
                agent = TestAgent(mock_connection_pool)
                
                assert agent.agent_name == "test_agent"
                assert agent.exchange_name == "chimera.events"
                assert agent.routing_keys == ["test.request", "test.response"]
                assert agent._correlation_map == {}

    def test_custom_exchange(self, mock_connection_pool):
        """Test agent with custom exchange name"""
        with patch('src.messaging.base_agent.EventPublisher'):
            with patch.object(BaseAgent, '_setup_queue'):
                
                class CustomAgent(TestAgent):
                    def __init__(self, pool):
                        BaseAgent.__init__(
                            self,
                            connection_pool=pool,
                            agent_name="custom_agent",
                            exchange_name="custom.exchange",
                            routing_keys=["custom.*"],
                        )
                
                agent = CustomAgent(mock_connection_pool)
                assert agent.exchange_name == "custom.exchange"


class TestMessageRouting:
    """Test message routing functionality"""

    def test_get_message_class(self, test_agent):
        """Test getting message class for routing key"""
        message_class = test_agent.get_message_class("test.request")
        assert message_class == MockMessage

    def test_get_message_class_unknown_key(self, test_agent):
        """Test getting message class for unknown routing key"""
        with pytest.raises(ValueError, match="Unknown routing key"):
            test_agent.get_message_class("unknown.key")

    def test_handle_message(self, test_agent):
        """Test message handling"""
        message = MockMessage()
        properties = {
            "routing_key": "test.request",
            "correlation_id": "test-123",
        }

        test_agent.handle_message(message, properties)

        assert len(test_agent.handled_messages) == 1
        assert test_agent.handled_messages[0]["routing_key"] == "test.request"
        assert test_agent.handled_messages[0]["properties"]["correlation_id"] == "test-123"


class TestPublishing:
    """Test publishing functionality"""

    def test_publish_event(self, test_agent):
        """Test publishing an event"""
        message = MockMessage()
        
        correlation_id = test_agent.publish_event(
            message=message,
            routing_key="test.event",
        )

        assert correlation_id is not None
        assert len(correlation_id) > 0
        test_agent.publisher.publish.assert_called_once()

    def test_publish_event_with_correlation_id(self, test_agent):
        """Test publishing event with specific correlation ID"""
        message = MockMessage()
        custom_id = "custom-correlation-123"
        
        correlation_id = test_agent.publish_event(
            message=message,
            routing_key="test.event",
            correlation_id=custom_id,
        )

        assert correlation_id == custom_id

    def test_publish_request(self, test_agent):
        """Test publishing a request"""
        message = MockMessage()
        context = {"user_id": "user123", "query": "test query"}
        
        correlation_id = test_agent.publish_request(
            message=message,
            routing_key="test.request",
            reply_routing_key="test.response",
            context=context,
        )

        assert correlation_id is not None
        assert correlation_id in test_agent._correlation_map
        
        stored = test_agent._correlation_map[correlation_id]
        assert stored["request_routing_key"] == "test.request"
        assert stored["reply_routing_key"] == "test.response"
        assert stored["context"] == context

    def test_publish_response(self, test_agent):
        """Test publishing a response"""
        message = MockMessage()
        correlation_id = "test-correlation-123"
        
        test_agent.publish_response(
            message=message,
            routing_key="test.response",
            correlation_id=correlation_id,
        )

        test_agent.publisher.publish.assert_called_once()
        call_args = test_agent.publisher.publish.call_args
        assert call_args[1]["correlation_id"] == correlation_id


class TestCorrelationTracking:
    """Test correlation ID tracking"""

    def test_get_correlation_context(self, test_agent):
        """Test retrieving correlation context"""
        correlation_id = "test-123"
        context = {"step": 1, "data": "test"}
        
        test_agent._correlation_map[correlation_id] = {
            "context": context,
            "timestamp": test_agent._get_timestamp(),
        }

        retrieved = test_agent.get_correlation_context(correlation_id)
        assert retrieved is not None
        assert retrieved["context"] == context

    def test_get_correlation_context_not_found(self, test_agent):
        """Test retrieving non-existent correlation context"""
        result = test_agent.get_correlation_context("non-existent")
        assert result is None

    def test_clear_correlation(self, test_agent):
        """Test clearing correlation context"""
        correlation_id = "test-123"
        test_agent._correlation_map[correlation_id] = {
            "context": {},
            "timestamp": test_agent._get_timestamp(),
        }

        test_agent.clear_correlation(correlation_id)
        assert correlation_id not in test_agent._correlation_map

    def test_clear_correlation_not_found(self, test_agent):
        """Test clearing non-existent correlation (should not error)"""
        test_agent.clear_correlation("non-existent")  # Should not raise

    def test_cleanup_old_correlations(self, test_agent):
        """Test cleaning up old correlation entries"""
        current_time = test_agent._get_timestamp()
        
        # Add old correlation (2 hours old)
        test_agent._correlation_map["old-1"] = {
            "context": {},
            "timestamp": current_time - (2 * 3600 * 1000),
        }
        
        # Add recent correlation (30 minutes old)
        test_agent._correlation_map["recent-1"] = {
            "context": {},
            "timestamp": current_time - (30 * 60 * 1000),
        }

        # Clean up entries older than 1 hour
        cleaned = test_agent.cleanup_old_correlations(max_age_seconds=3600)

        assert cleaned == 1
        assert "old-1" not in test_agent._correlation_map
        assert "recent-1" in test_agent._correlation_map

    def test_cleanup_no_old_correlations(self, test_agent):
        """Test cleanup when no old correlations exist"""
        current_time = test_agent._get_timestamp()
        
        # Add recent correlation
        test_agent._correlation_map["recent-1"] = {
            "context": {},
            "timestamp": current_time - (30 * 60 * 1000),
        }

        cleaned = test_agent.cleanup_old_correlations(max_age_seconds=3600)
        assert cleaned == 0


class TestRequestResponsePattern:
    """Test request-response pattern"""

    def test_full_request_response_flow(self, test_agent):
        """Test complete request-response workflow"""
        # Publish request
        request = MockMessage()
        context = {"original_query": "test"}
        
        correlation_id = test_agent.publish_request(
            message=request,
            routing_key="test.request",
            reply_routing_key="test.response",
            context=context,
        )

        # Verify context stored
        stored_context = test_agent.get_correlation_context(correlation_id)
        assert stored_context is not None
        assert stored_context["context"]["original_query"] == "test"

        # Simulate receiving response
        response = MockMessage()
        response_properties = {
            "routing_key": "test.response",
            "correlation_id": correlation_id,
        }

        test_agent.handle_message(response, response_properties)

        # Verify message was handled
        assert len(test_agent.handled_messages) == 1

        # Clean up correlation
        test_agent.clear_correlation(correlation_id)
        assert test_agent.get_correlation_context(correlation_id) is None


class TestContextManager:
    """Test context manager functionality"""

    def test_context_manager_enter_exit(self, mock_connection_pool):
        """Test using agent as context manager"""
        with patch('src.messaging.base_agent.EventPublisher'):
            with patch.object(BaseAgent, '_setup_queue'):
                with TestAgent(mock_connection_pool) as agent:
                    assert agent is not None
                    assert agent.agent_name == "test_agent"

    def test_context_manager_cleanup(self, mock_connection_pool):
        """Test context manager calls close on exit"""
        with patch('src.messaging.base_agent.EventPublisher'):
            with patch.object(BaseAgent, '_setup_queue'):
                agent = TestAgent(mock_connection_pool)
                
                with patch.object(agent, 'close') as mock_close:
                    with agent:
                        pass
                    mock_close.assert_called_once()


class TestErrorHandling:
    """Test error handling"""

    def test_handle_message_error_propagates(self, test_agent):
        """Test that errors in route_message propagate"""
        
        class ErrorAgent(TestAgent):
            def route_message(self, message, routing_key, properties):
                raise ValueError("Test error")
        
        with patch('src.messaging.base_agent.EventPublisher'):
            with patch.object(BaseAgent, '_setup_queue'):
                agent = ErrorAgent(test_agent.connection_pool)
                
                message = MockMessage()
                properties = {"routing_key": "test.request"}
                
                with pytest.raises(ValueError, match="Test error"):
                    agent.handle_message(message, properties)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

