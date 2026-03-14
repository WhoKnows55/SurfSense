"""
SurfSense LLM Service

Provides a unified interface for language model interactions.
Supports both OpenAI API and local Hugging Face models (like Phi-3 mini).
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

    def chat_with_tools(self, messages: list[dict], tools: list[dict] | None = None):
        """Full chat completion with optional function-calling tools.

        Subclasses that support function-calling should override this.
        """
        raise NotImplementedError(f"{self.__class__.__name__} does not support chat_with_tools")

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is ready to use."""
        pass


class AzureOpenAIProvider(BaseLLMProvider):
    """Azure OpenAI provider with function-calling support."""

    def __init__(
        self,
        endpoint: str,
        api_key: str,
        deployment_name: str,
        api_version: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ):
        self.deployment_name = deployment_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        from openai import AzureOpenAI

        self._client = AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version=api_version,
        )

    def generate(self, prompt: str) -> str:
        """Simple single-turn generation (backward compat)."""
        response = self._client.chat.completions.create(
            model=self.deployment_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        return response.choices[0].message.content.strip()

    def chat_with_tools(self, messages: list[dict], tools: list[dict] | None = None):
        """Full chat completion with optional function-calling tools.

        Args:
            messages: OpenAI-format message list.
            tools:    OpenAI function-calling tool definitions (optional).

        Returns:
            The raw ChatCompletion object.
        """
        kwargs = {
            "model": self.deployment_name,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"
        return self._client.chat.completions.create(**kwargs)

    def is_available(self) -> bool:
        return bool(self._client)


class LocalLLMProvider(BaseLLMProvider):
    """
    Local LLM provider using Hugging Face transformers.

    Uses models like Phi-3 mini that can run locally without API keys.
    """

    # Chat template for Phi-3 style models
    CHAT_TEMPLATE = "<|user|>\n{user_input}<|end|>\n<|assistant|>\n"

    # System prompt for SurfSense persona
    SYSTEM_PROMPT = """You are SurfSense, an AI surf trip planning assistant. You help surfers plan trips by:
- Analyzing surf forecasts and conditions
- Recommending spots based on skill level
- Creating multi-day trip itineraries
- Providing safety advice

Be helpful, concise, and knowledgeable about surfing. If you don't know something, say so."""

    def __init__(
        self,
        model_name: str = "microsoft/Phi-3-mini-4k-instruct",
        max_new_tokens: int = 500,
        temperature: float = 0.7,
        use_cpu: bool = False,
    ):
        """
        Initialize the local LLM provider.

        Args:
            model_name: Hugging Face model name or path.
            max_new_tokens: Maximum tokens to generate.
            temperature: Sampling temperature.
            use_cpu: Force CPU usage (disable CUDA).
        """
        self.model_name = model_name
        self.max_new_tokens = max_new_tokens
        self.temperature = temperature
        self.use_cpu = use_cpu
        self._pipeline = None
        self._initialized = False

    def _get_device_config(self) -> tuple:
        """
        Determine device configuration for model loading.

        Returns:
            Tuple of (device_map, dtype) for model loading.
        """
        try:
            import torch

            if not self.use_cpu and torch.cuda.is_available():
                self.log_info("CUDA available, using GPU")
                return "auto", torch.float16
            elif not self.use_cpu and torch.backends.mps.is_available():
                self.log_info("MPS available, using Apple Silicon GPU")
                return "mps", torch.float16
            else:
                self.log_info("Using CPU for inference")
                return None, None
        except ImportError:
            self.log_warning("PyTorch not available, using CPU")
            return None, None

    def _initialize(self) -> None:
        """Lazy initialization of the model pipeline."""
        if self._initialized:
            return

        self.logger.info(f"Loading local model: {self.model_name}")

        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

            device_map, dtype = self._get_device_config()

            # Load tokenizer
            tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                trust_remote_code=True,
            )

            # Load model with appropriate settings
            model_kwargs = {"trust_remote_code": True}
            if device_map is not None:
                model_kwargs["device_map"] = device_map
            if dtype is not None:
                model_kwargs["torch_dtype"] = dtype

            model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                **model_kwargs,
            )

            # Disable cache to avoid compatibility issues
            try:
                model.config.use_cache = False
            except Exception:
                pass

            # Set pad token if not set
            if tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token

            # Create pipeline
            self._pipeline = pipeline(
                "text-generation",
                model=model,
                tokenizer=tokenizer,
                max_new_tokens=self.max_new_tokens,
                temperature=self.temperature,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id,
                return_full_text=False,
            )

            self._initialized = True
            self.logger.info(f"Model loaded successfully: {self.model_name}")

        except Exception as e:
            self.logger.error(f"Failed to load model: {e}")
            raise RuntimeError(f"Failed to initialize local LLM: {e}") from e

    def generate(self, prompt: str) -> str:
        """
        Generate a response using the local model.

        Args:
            prompt: The user's input message.

        Returns:
            The model's response text.
        """
        self._initialize()

        # Format with chat template
        formatted_prompt = self.CHAT_TEMPLATE.format(user_input=prompt)

        self.logger.debug(f"Generating response for prompt: {prompt[:100]}...")

        try:
            output = self._pipeline(formatted_prompt, use_cache=False)

            if isinstance(output, list) and len(output) > 0 and "generated_text" in output[0]:
                response = output[0]["generated_text"].strip()
            else:
                response = str(output).strip()

            self.logger.debug(f"Generated response: {response[:100]}...")
            return response

        except Exception as e:
            self.logger.error(f"Generation error: {e}")
            raise RuntimeError(f"Failed to generate response: {e}") from e

    def is_available(self) -> bool:
        """Check if the local model can be loaded."""
        try:
            import transformers  # noqa: F401
            return True
        except ImportError:
            return False


class OpenAILLMProvider(BaseLLMProvider):
    """
    OpenAI API-based LLM provider.

    Uses the OpenAI API for generating responses.
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
        model_name: str = "gpt-4-turbo-preview",
        max_tokens: int = 2000,
        temperature: float = 0.7,
    ):
        """
        Initialize the OpenAI provider.

        Args:
            api_key: OpenAI API key.
            model_name: OpenAI model name.
            max_tokens: Maximum tokens to generate.
            temperature: Sampling temperature.
        """
        self.api_key = api_key
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.temperature = temperature
        self._client = None

    def _get_client(self):
        """Lazy initialization of OpenAI client."""
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI(api_key=self.api_key)
        return self._client

    def generate(self, prompt: str) -> str:
        """
        Generate a response using OpenAI API.

        Args:
            prompt: The user's input message.

        Returns:
            The model's response text.
        """
        self.logger.debug(f"Sending prompt to OpenAI: {prompt[:100]}...")

        try:
            client = self._get_client()
            response = client.chat.completions.create(
                model=self.model_name,
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
            self.logger.error(f"OpenAI API error: {e}")
            raise RuntimeError(f"Failed to get response from OpenAI: {e}") from e

    def chat_with_tools(self, messages: list[dict], tools: list[dict] | None = None):
        """Full chat completion with optional function-calling tools.

        Args:
            messages: OpenAI-format message list.
            tools:    OpenAI function-calling tool definitions (optional).

        Returns:
            The raw ChatCompletion object.
        """
        client = self._get_client()
        kwargs = {
            "model": self.model_name,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"
        return client.chat.completions.create(**kwargs)

    def is_available(self) -> bool:
        """Check if OpenAI API is accessible."""
        return bool(self.api_key)


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
        if getattr(settings, "azure_openai", None) and settings.azure_openai.endpoint and settings.azure_openai.api_key:
            provider = AzureOpenAIProvider(
                endpoint=settings.azure_openai.endpoint,
                api_key=settings.azure_openai.api_key,
                deployment_name=settings.azure_openai.deployment_name,
                api_version=settings.azure_openai.api_version,
                temperature=settings.azure_openai.temperature,
                max_tokens=settings.azure_openai.max_tokens,
            )
        elif settings.llm.provider == "openai":
            provider = OpenAILLMProvider(
                api_key=settings.openai_api_key,
                model_name=settings.llm.model_name,
                max_tokens=settings.llm.max_tokens,
                temperature=settings.llm.temperature,
            )
        else:
            provider = LocalLLMProvider(
                model_name=settings.llm.model_name,
                max_new_tokens=settings.llm.max_tokens,
                temperature=settings.llm.temperature,
                use_cpu=settings.llm.use_cpu,
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
