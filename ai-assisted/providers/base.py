"""
Base provider class for AI-assisted Terraform generation.

All AI provider implementations must inherit from this base class.
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional


class AIProvider(ABC):
    """Abstract base class for AI providers."""

    def __init__(self, api_key: str, model: Optional[str] = None):
        """
        Initialize the AI provider.

        Args:
            api_key: API key for the provider
            model: Optional model name (provider-specific default if not specified)
        """
        self.api_key = api_key
        self.model = model or self.get_default_model()
        self.token_usage = {"input": 0, "output": 0, "total": 0}

    @abstractmethod
    def get_default_model(self) -> str:
        """
        Get the default model name for this provider.

        Returns:
            Default model identifier
        """
        pass

    @abstractmethod
    def generate_terraform(self, prompt: str, context: Dict[str, str]) -> str:
        """
        Generate Terraform code using the AI provider.

        Args:
            prompt: User's prompt describing what to generate
            context: Dictionary of context information (repository structure, examples, etc.)

        Returns:
            Generated Terraform code

        Raises:
            Exception: If generation fails
        """
        pass

    def get_token_usage(self) -> Dict[str, int]:
        """
        Get token usage statistics.

        Returns:
            Dictionary with input, output, and total token counts
        """
        return self.token_usage.copy()

    def reset_token_usage(self):
        """Reset token usage counters."""
        self.token_usage = {"input": 0, "output": 0, "total": 0}

    def _build_full_prompt(self, prompt: str, context: Dict[str, str]) -> str:
        """
        Build the full prompt including context.

        Args:
            prompt: User's prompt
            context: Context dictionary

        Returns:
            Complete prompt with context prepended
        """
        context_str = ""

        if "repository_structure" in context:
            context_str += f"# Repository Structure\n\n{context['repository_structure']}\n\n"

        if "terraform_examples" in context:
            context_str += f"# Terraform Examples\n\n{context['terraform_examples']}\n\n"

        if "resource_guide" in context:
            context_str += f"# Resource Guide\n\n{context['resource_guide']}\n\n"

        context_str += "---\n\n# USER REQUEST\n\n"
        context_str += prompt

        return context_str

    def validate_terraform_code(self, code: str) -> bool:
        """
        Perform basic validation on generated Terraform code.

        Args:
            code: Generated Terraform code

        Returns:
            True if code passes basic validation, False otherwise
        """
        # Check for common issues
        if not code.strip():
            return False

        # Check for proper HCL syntax indicators
        if "resource" not in code and "data" not in code:
            return False

        # Check for improperly escaped template strings (should be $$ not $)
        # Allow ${var. and ${local. but flag ${source. without $$
        if "${source." in code and "$${source." not in code:
            return False

        return True
