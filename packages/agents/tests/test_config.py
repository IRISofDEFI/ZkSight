"""Tests for configuration management"""
import pytest
from pydantic import ValidationError
from src.config import (
    AgentConfig,
    RabbitMQConfig,
    InfluxDBConfig,
    MongoDBConfig,
    RedisConfig,
    OpenAIConfig,
)


def test_rabbitmq_config_defaults() -> None:
    """Test RabbitMQ configuration with defaults"""
    config = RabbitMQConfig()
    assert config.host == "localhost"
    assert config.port == 5672
    assert config.username == "guest"
    assert config.password == "guest"
    assert config.vhost == "/"


def test_rabbitmq_config_invalid_port() -> None:
    """Test RabbitMQ configuration with invalid port"""
    with pytest.raises(ValidationError):
        RabbitMQConfig(port=70000)


def test_influxdb_config_defaults() -> None:
    """Test InfluxDB configuration with defaults"""
    config = InfluxDBConfig()
    assert config.url == "http://localhost:8086"
    assert config.org == "chimera"
    assert config.bucket == "zcash_metrics"


def test_mongodb_config_defaults() -> None:
    """Test MongoDB configuration with defaults"""
    config = MongoDBConfig()
    assert config.uri == "mongodb://localhost:27017"
    assert config.database == "chimera"


def test_redis_config_defaults() -> None:
    """Test Redis configuration with defaults"""
    config = RedisConfig()
    assert config.host == "localhost"
    assert config.port == 6379
    assert config.password is None
    assert config.db == 0


def test_redis_config_invalid_db() -> None:
    """Test Redis configuration with invalid database number"""
    with pytest.raises(ValidationError):
        RedisConfig(db=20)


def test_openai_config_defaults() -> None:
    """Test OpenAI configuration with defaults"""
    config = OpenAIConfig()
    assert config.model == "gpt-4"
    assert config.temperature == 0.7


def test_openai_config_invalid_temperature() -> None:
    """Test OpenAI configuration with invalid temperature"""
    with pytest.raises(ValidationError):
        OpenAIConfig(temperature=3.0)


def test_agent_config_defaults() -> None:
    """Test main agent configuration with defaults"""
    config = AgentConfig()
    assert config.environment == "development"
    assert config.log_level == "INFO"
    assert isinstance(config.rabbitmq, RabbitMQConfig)
    assert isinstance(config.influxdb, InfluxDBConfig)
    assert isinstance(config.mongodb, MongoDBConfig)
    assert isinstance(config.redis, RedisConfig)
    assert isinstance(config.openai, OpenAIConfig)


def test_agent_config_invalid_environment() -> None:
    """Test agent configuration with invalid environment"""
    with pytest.raises(ValidationError):
        AgentConfig(environment="invalid")


def test_agent_config_invalid_log_level() -> None:
    """Test agent configuration with invalid log level"""
    with pytest.raises(ValidationError):
        AgentConfig(log_level="INVALID")
