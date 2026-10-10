from typing import Dict, Any, Optional
import openai
import anthropic
from abc import ABC, abstractmethod

class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate text from the LLM.
        
        Args:
            prompt: Input prompt
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Generated text response
        """
        pass

class OpenAIProvider(LLMProvider):
    """OpenAI API provider implementation."""
    
    def __init__(self, api_key: str):
        """Initialize OpenAI provider.
        
        Args:
            api_key: OpenAI API key
        """
        self.client = openai.OpenAI(api_key=api_key)
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate text using OpenAI's API.
        
        Args:
            prompt: Input prompt
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
            
        Returns:
            Generated text response
        """
        response = await self.client.chat.completions.create(
            model=kwargs.get("model", "gpt-4"),
            messages=[{"role": "user", "content": prompt}],
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens", 150)
        )
        return response.choices[0].message.content

class AnthropicProvider(LLMProvider):
    """Anthropic API provider implementation."""
    
    def __init__(self, api_key: str):
        """Initialize Anthropic provider.
        
        Args:
            api_key: Anthropic API key
        """
        self.client = anthropic.Anthropic(api_key=api_key)
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate text using Anthropic's API.
        
        Args:
            prompt: Input prompt
            **kwargs: Additional parameters
            
        Returns:
            Generated text response
        """
        response = await self.client.messages.create(
            model=kwargs.get("model", "claude-3-sonnet-20240229"),
            max_tokens=kwargs.get("max_tokens", 150),
            temperature=kwargs.get("temperature", 0.7),
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text

class LLMIntegrator:
    """Manages interactions with different LLM providers."""
    
    def __init__(self, config_manager=None):
        """Initialize the LLM integrator.
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config = config_manager
        self.providers: Dict[str, LLMProvider] = {}
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize configured LLM providers."""
        if not self.config:
            return
            
        api_keys = self.config.get("llm.api_keys", {})
        
        if openai_key := api_keys.get("openai"):
            self.providers["openai"] = OpenAIProvider(openai_key)
            
        if anthropic_key := api_keys.get("anthropic"):
            self.providers["anthropic"] = AnthropicProvider(anthropic_key)
    
    async def generate(
        self,
        prompt: str,
        provider: Optional[str] = None,
        **kwargs
    ) -> str:
        """Generate text using the specified or default LLM provider.
        
        Args:
            prompt: Input prompt
            provider: Name of the provider to use
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Generated text response
            
        Raises:
            ValueError: If no suitable provider is available
        """
        if not provider:
            provider = self.config.get("llm.default_provider", "openai")
            
        if provider not in self.providers:
            raise ValueError(f"Provider '{provider}' not configured")
            
        return await self.providers[provider].generate(
            prompt,
            temperature=self.config.get("llm.temperature", 0.7),
            max_tokens=self.config.get("llm.max_tokens", 150),
            **kwargs
        )