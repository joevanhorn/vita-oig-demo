"""
AI provider implementations for Terraform generation.
"""

from .base import AIProvider
from .gemini import GeminiProvider
from .openai import OpenAIProvider
from .anthropic import AnthropicProvider

__all__ = [
    "AIProvider",
    "GeminiProvider",
    "OpenAIProvider",
    "AnthropicProvider",
]

# Provider registry
PROVIDERS = {
    "gemini": GeminiProvider,
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "claude": AnthropicProvider,  # Alias
}


def get_provider(provider_name: str, api_key: str, model: str = None) -> AIProvider:
    """
    Get an AI provider instance.

    Args:
        provider_name: Name of the provider (gemini, openai, anthropic)
        api_key: API key for the provider
        model: Optional model override

    Returns:
        Initialized provider instance

    Raises:
        ValueError: If provider name is not recognized
    """
    provider_name = provider_name.lower()

    if provider_name not in PROVIDERS:
        raise ValueError(
            f"Unknown provider: {provider_name}. "
            f"Available providers: {', '.join(PROVIDERS.keys())}"
        )

    provider_class = PROVIDERS[provider_name]
    return provider_class(api_key=api_key, model=model)
