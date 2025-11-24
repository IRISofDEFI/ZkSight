"""Integration tests for Narrative Agent."""
import pytest
from unittest.mock import Mock, patch
from src.narrative.agent import NarrativeAgent
from src.messaging.connection import ConnectionPool
from src.config import AgentConfig


@pytest.fixture
def mock_connection_pool():
    """Create mock connection pool."""
    pool = Mock(spec=ConnectionPool)
    pool.get_connection = Mock(return_value=Mock())
    return pool


@pytest.fixture
def mock_config():
    """Create mock config."""
    config = Mock(spec=AgentConfig)
    config.openai = Mock()
    config.openai.api_key = "test-key"
    config.openai.model = "gpt-4"
    config.openai.temperature = 0.7
    config.mongodb = Mock()
    config.mongodb.uri = "mongodb://localhost:27017"
    config.mongodb.database = "test"
    return config


class TestNarrativeAgentIntegration:
    """Integration tests for Narrative Agent."""

    def test_agent_initialization(self, mock_connection_pool, mock_config):
        """Test agent initializes correctly."""
        with patch('src.narrative.agent.LLMClient'):
            with patch('src.narrative.agent.NarrativeStorage'):
                with patch.object(NarrativeAgent, '_setup_queue'):
                    agent = NarrativeAgent(
                        connection_pool=mock_connection_pool,
                        config=mock_config,
                    )
                    assert agent.agent_name == "narrative_agent"
                    assert agent.report_builder is not None
                    assert agent.viz_builder is not None

