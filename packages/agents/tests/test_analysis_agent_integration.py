"""Integration tests for Analysis Agent."""
import pytest
from unittest.mock import Mock, MagicMock, patch
from src.analysis.agent import AnalysisAgent
from src.analysis.models import DataPoint, DataSeries
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
    config.influxdb = Mock()
    config.mongodb = Mock()
    return config


@pytest.fixture
def sample_data_series():
    """Create sample data series."""
    points = [
        DataPoint(timestamp=1000, value=10.0),
        DataPoint(timestamp=2000, value=20.0),
        DataPoint(timestamp=3000, value=30.0),
    ]
    return DataSeries(metric="test_metric", points=points)


class TestAnalysisAgentIntegration:
    """Integration tests for Analysis Agent."""

    def test_agent_initialization(self, mock_connection_pool, mock_config):
        """Test agent initializes correctly."""
        with patch('src.analysis.agent.AnalysisPipeline'):
            with patch('src.analysis.agent.AnalysisResultRepository'):
                with patch.object(AnalysisAgent, '_setup_queue'):
                    agent = AnalysisAgent(
                        connection_pool=mock_connection_pool,
                        config=mock_config,
                    )
                    assert agent.agent_name == "analysis_agent"
                    assert agent.pipeline is not None

    def test_pipeline_execution(self, mock_connection_pool, mock_config, sample_data_series):
        """Test pipeline execution with sample data."""
        with patch('src.analysis.agent.AnalysisPipeline') as mock_pipeline_class:
            with patch('src.analysis.agent.AnalysisResultRepository'):
                with patch.object(AnalysisAgent, '_setup_queue'):
                    mock_pipeline = Mock()
                    mock_pipeline.run.return_value = Mock()
                    mock_pipeline_class.return_value = mock_pipeline

                    agent = AnalysisAgent(
                        connection_pool=mock_connection_pool,
                        config=mock_config,
                    )

                    result = agent._run_pipeline([sample_data_series])
                    assert result is not None
                    mock_pipeline.run.assert_called_once()

