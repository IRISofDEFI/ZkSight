"""Configuration management with validation for agents"""
from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class RabbitMQConfig(BaseSettings):
    """RabbitMQ connection configuration"""
    host: str = Field(default="localhost", description="RabbitMQ host")
    port: int = Field(default=5672, description="RabbitMQ port")
    username: str = Field(default="guest", description="RabbitMQ username")
    password: str = Field(default="guest", description="RabbitMQ password")
    vhost: str = Field(default="/", description="RabbitMQ virtual host")
    
    @field_validator("port")
    @classmethod
    def validate_port(cls, v: int) -> int:
        if not 1 <= v <= 65535:
            raise ValueError("Port must be between 1 and 65535")
        return v


class InfluxDBConfig(BaseSettings):
    """InfluxDB connection configuration"""
    url: str = Field(default="http://localhost:8086", description="InfluxDB URL")
    token: str = Field(default="", description="InfluxDB authentication token")
    org: str = Field(default="chimera", description="InfluxDB organization")
    bucket: str = Field(default="zcash_metrics", description="InfluxDB bucket")


class MongoDBConfig(BaseSettings):
    """MongoDB connection configuration"""
    uri: str = Field(
        default="mongodb://localhost:27017",
        description="MongoDB connection URI"
    )
    database: str = Field(default="chimera", description="MongoDB database name")


class RedisConfig(BaseSettings):
    """Redis connection configuration"""
    host: str = Field(default="localhost", description="Redis host")
    port: int = Field(default=6379, description="Redis port")
    password: Optional[str] = Field(default=None, description="Redis password")
    db: int = Field(default=0, description="Redis database number")
    
    @field_validator("port")
    @classmethod
    def validate_port(cls, v: int) -> int:
        if not 1 <= v <= 65535:
            raise ValueError("Port must be between 1 and 65535")
        return v
    
    @field_validator("db")
    @classmethod
    def validate_db(cls, v: int) -> int:
        if not 0 <= v <= 15:
            raise ValueError("Redis DB must be between 0 and 15")
        return v


class OpenAIConfig(BaseSettings):
    """OpenAI API configuration"""
    api_key: str = Field(default="", description="OpenAI API key")
    model: str = Field(default="gpt-4", description="OpenAI model to use")
    temperature: float = Field(default=0.7, description="Model temperature")
    
    @field_validator("temperature")
    @classmethod
    def validate_temperature(cls, v: float) -> float:
        if not 0.0 <= v <= 2.0:
            raise ValueError("Temperature must be between 0.0 and 2.0")
        return v


class AgentConfig(BaseSettings):
    """Main agent configuration"""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=False
    )
    
    environment: str = Field(default="development", description="Environment name")
    log_level: str = Field(default="INFO", description="Logging level")
    
    rabbitmq: RabbitMQConfig = Field(default_factory=RabbitMQConfig)
    influxdb: InfluxDBConfig = Field(default_factory=InfluxDBConfig)
    mongodb: MongoDBConfig = Field(default_factory=MongoDBConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    openai: OpenAIConfig = Field(default_factory=OpenAIConfig)
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        return v_upper
    
    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        valid_envs = ["development", "staging", "production"]
        v_lower = v.lower()
        if v_lower not in valid_envs:
            raise ValueError(f"Environment must be one of {valid_envs}")
        return v_lower


def load_config() -> AgentConfig:
    """Load and validate configuration"""
    return AgentConfig()
