"""
Google Gemini provider for AI-assisted Terraform generation.
"""

from typing import Dict
from .base import AIProvider


class GeminiProvider(AIProvider):
    """Google Gemini API provider."""

    def get_default_model(self) -> str:
        """Get default Gemini model."""
        return "gemini-1.5-pro"

    def generate_terraform(self, prompt: str, context: Dict[str, str]) -> str:
        """
        Generate Terraform code using Google Gemini.

        Args:
            prompt: User's prompt
            context: Context dictionary

        Returns:
            Generated Terraform code

        Raises:
            ImportError: If google-generativeai is not installed
            Exception: If generation fails
        """
        try:
            import google.generativeai as genai
        except ImportError:
            raise ImportError(
                "google-generativeai package is required for Gemini provider.\n"
                "Install with: pip install google-generativeai"
            )

        # Configure Gemini
        genai.configure(api_key=self.api_key)

        # Build full prompt with context
        full_prompt = self._build_full_prompt(prompt, context)

        # Add specific instructions for Terraform generation
        system_instruction = """You are an expert Terraform developer specializing in Okta infrastructure.

Generate clean, production-ready Terraform code following these rules:
1. Use exact patterns from the provided examples
2. Always escape template strings with $$ (e.g., "$${source.login}")
3. Set status = "ACTIVE" for all resources
4. Include descriptive comments
5. Follow HCL formatting conventions
6. Use proper resource naming (snake_case)
7. Include depends_on where appropriate
8. Generate only valid Terraform HCL code

Output only the Terraform code, no explanations unless specifically requested."""

        try:
            # Create model with system instruction
            model = genai.GenerativeModel(
                model_name=self.model,
                system_instruction=system_instruction
            )

            # Generate content
            response = model.generate_content(full_prompt)

            # Extract code from response
            generated_code = response.text

            # Remove markdown code fences if present
            if "```hcl" in generated_code:
                generated_code = generated_code.split("```hcl")[1].split("```")[0].strip()
            elif "```terraform" in generated_code:
                generated_code = generated_code.split("```terraform")[1].split("```")[0].strip()
            elif "```" in generated_code:
                # Generic code fence
                parts = generated_code.split("```")
                if len(parts) >= 3:
                    generated_code = parts[1].strip()

            # Track token usage if available
            if hasattr(response, 'usage_metadata'):
                self.token_usage["input"] += response.usage_metadata.prompt_token_count
                self.token_usage["output"] += response.usage_metadata.candidates_token_count
                self.token_usage["total"] = self.token_usage["input"] + self.token_usage["output"]

            # Validate generated code
            if not self.validate_terraform_code(generated_code):
                raise ValueError(
                    "Generated code failed validation. "
                    "Please check the output and try again with more specific instructions."
                )

            return generated_code

        except Exception as e:
            raise Exception(f"Gemini generation failed: {str(e)}")

    def generate_with_streaming(self, prompt: str, context: Dict[str, str]):
        """
        Generate Terraform code with streaming response.

        Args:
            prompt: User's prompt
            context: Context dictionary

        Yields:
            Chunks of generated text

        Raises:
            ImportError: If google-generativeai is not installed
        """
        try:
            import google.generativeai as genai
        except ImportError:
            raise ImportError(
                "google-generativeai package is required for Gemini provider.\n"
                "Install with: pip install google-generativeai"
            )

        genai.configure(api_key=self.api_key)
        full_prompt = self._build_full_prompt(prompt, context)

        system_instruction = """You are an expert Terraform developer specializing in Okta infrastructure.
Generate clean, production-ready Terraform code following the provided examples and patterns."""

        model = genai.GenerativeModel(
            model_name=self.model,
            system_instruction=system_instruction
        )

        response = model.generate_content(full_prompt, stream=True)

        for chunk in response:
            if chunk.text:
                yield chunk.text
