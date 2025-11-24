"""LLM client for narrative generation."""
import logging
from typing import Optional, AsyncGenerator
from openai import AsyncOpenAI
from ..config import AgentConfig

logger = logging.getLogger(__name__)


class LLMClient:
    """Client for OpenAI API with retry logic and streaming support."""

    def __init__(self, config: AgentConfig):
        """
        Initialize LLM client.

        Args:
            config: Agent configuration with OpenAI settings
        """
        self.config = config
        self.client = AsyncOpenAI(api_key=config.openai.api_key)
        self.model = config.openai.model
        self.temperature = config.openai.temperature

    async def generate_text(
        self,
        prompt: str,
        max_tokens: int = 2000,
        temperature: Optional[float] = None,
    ) -> str:
        """
        Generate text using OpenAI API.

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Override default temperature

        Returns:
            Generated text
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature or self.temperature,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"Error generating text: {e}", exc_info=True)
            raise

    async def generate_stream(
        self,
        prompt: str,
        max_tokens: int = 2000,
        temperature: Optional[float] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Generate text stream using OpenAI API.

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Override default temperature

        Yields:
            Text chunks
        """
        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature or self.temperature,
                stream=True,
            )
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error(f"Error generating stream: {e}", exc_info=True)
            raise

