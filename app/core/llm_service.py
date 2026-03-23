"""
SurfSense LLM Service

Provides a unified interface for language model interactions.
Uses Azure OpenAI API for generating responses.
"""

from abc import ABC, abstractmethod

from app.core.logger import LoggerMixin, get_logger

logger = get_logger(__name__)


class BaseLLMProvider(ABC, LoggerMixin):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def generate(self, prompt: str) -> str:
        """
        Generate a response for the given prompt.

        Args:
            prompt: The user's input message.

        Returns:
            The model's response text.
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is ready to use."""
        pass





class OpenAILLMProvider(BaseLLMProvider):
    """
    Azure OpenAI API-based LLM provider.

    Uses the Azure OpenAI API for generating responses.
    """

    SYSTEM_PROMPT = """You are SurfSense, an AI surf trip planning assistant. You help surfers plan trips by:
- Analyzing surf forecasts and conditions
- Recommending spots based on skill level
- Creating multi-day trip itineraries
- Providing safety advice

Be helpful, concise, and knowledgeable about surfing. If you don't know something, say so."""

    def __init__(
        self,
        api_key: str,
        endpoint: str,
        deployment_name: str,
        api_version: str = "2024-10-21",
        max_tokens: int = 2000,
        temperature: float = 0.7,
    ):
        """
        Initialize the Azure OpenAI provider.

        Args:
            api_key: Azure OpenAI API key.
            endpoint: Azure OpenAI endpoint URL.
            deployment_name: Azure deployment name.
            api_version: Azure API version.
            max_tokens: Maximum tokens to generate.
            temperature: Sampling temperature.
        """
        self.api_key = api_key
        self.endpoint = endpoint
        self.deployment_name = deployment_name
        self.api_version = api_version
        self.max_tokens = max_tokens
        self.temperature = temperature
        self._client = None

    def _get_client(self):
        """Lazy initialization of Azure OpenAI client."""
        if self._client is None:
            from openai import AzureOpenAI

            self._client = AzureOpenAI(
                api_key=self.api_key,
                api_version=self.api_version,
                azure_endpoint=self.endpoint,
            )
        return self._client

    def generate(self, prompt: str) -> str:
        """
        Generate a response using Azure OpenAI API.

        Args:
            prompt: The user's input message.

        Returns:
            The model's response text.
        """
        self.logger.debug(f"Sending prompt to Azure OpenAI: {prompt[:100]}...")

        try:
            client = self._get_client()
            response = client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )

            result = response.choices[0].message.content.strip()
            self.logger.debug(f"Received response: {result[:100]}...")
            return result

        except Exception as e:
            self.logger.error(f"Azure OpenAI API error: {e}")
            raise RuntimeError(f"Failed to get response from Azure OpenAI: {e}") from e

    def is_available(self) -> bool:
        """Check if Azure OpenAI API is accessible."""
        return bool(self.api_key and self.endpoint)


class LLMService(LoggerMixin):
    """
    Main LLM service that manages provider selection and interaction.

    This is the primary interface for LLM interactions in SurfSense.
    """

    def __init__(self, provider: BaseLLMProvider):
        """
        Initialize the LLM service with a provider.

        Args:
            provider: The LLM provider to use.
        """
        self._provider = provider

    @classmethod
    def from_settings(cls, settings) -> "LLMService":
        """
        Create an LLM service from application settings.

        Args:
            settings: Application settings object.

        Returns:
            Configured LLMService instance.
        """
        provider = OpenAILLMProvider(
            api_key=settings.azure_openai_api_key,
            endpoint=settings.azure_openai_endpoint,
            deployment_name=settings.azure_openai_deployment_name,
            api_version=settings.azure_openai_api_version,
            max_tokens=settings.llm.max_tokens,
            temperature=settings.llm.temperature,
        )
        return cls(provider)

    def chat(self, message: str) -> str:
        """
        Send a message and get a response.

        Args:
            message: The user's message.

        Returns:
            The assistant's response.
        """
        self.logger.info("Processing chat message")
        return self._provider.generate(message)

    def generate(self, prompt: str) -> str:
        """
        Generate a response for the given prompt.

        Alias for chat() to match the provider interface.

        Args:
            prompt: The prompt/message to send.

        Returns:
            The model's response.
        """
        return self.chat(prompt)

    def is_ready(self) -> bool:
        """Check if the LLM service is ready to use."""
        return self._provider.is_available()

    @property
    def provider_name(self) -> str:
        """Get the name of the current provider."""
        return self._provider.__class__.__name__
