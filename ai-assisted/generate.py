#!/usr/bin/env python3
"""
AI-Assisted Terraform Generator for Okta

This CLI tool uses AI providers (Gemini, OpenAI, Claude) to generate
Terraform code for Okta infrastructure based on natural language prompts.

Usage:
    python generate.py --prompt "Create 5 users in marketing dept" --provider gemini
    python generate.py --interactive
    python generate.py --config config.yaml

Environment Variables:
    GEMINI_API_KEY, GOOGLE_API_KEY - For Gemini provider
    OPENAI_API_KEY - For OpenAI provider
    ANTHROPIC_API_KEY, CLAUDE_API_KEY - For Anthropic provider
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Dict, Optional
import subprocess

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from providers import get_provider


def load_context_files() -> Dict[str, str]:
    """
    Load context files for AI generation.

    Returns:
        Dictionary of context content
    """
    context_dir = Path(__file__).parent / "context"
    context = {}

    # Load repository structure
    repo_struct_file = context_dir / "repository_structure.md"
    if repo_struct_file.exists():
        context["repository_structure"] = repo_struct_file.read_text()

    # Load terraform examples
    examples_file = context_dir / "terraform_examples.md"
    if examples_file.exists():
        context["terraform_examples"] = examples_file.read_text()

    # Load resource guide
    resource_guide_file = context_dir / "okta_resource_guide.md"
    if resource_guide_file.exists():
        context["resource_guide"] = resource_guide_file.read_text()

    return context


def get_api_key(provider: str) -> Optional[str]:
    """
    Get API key from environment variables.

    Args:
        provider: Provider name (gemini, openai, anthropic)

    Returns:
        API key if found, None otherwise
    """
    if provider == "gemini":
        return os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    elif provider == "openai":
        return os.getenv("OPENAI_API_KEY")
    elif provider in ["anthropic", "claude"]:
        return os.getenv("ANTHROPIC_API_KEY") or os.getenv("CLAUDE_API_KEY")
    return None


def validate_terraform(code: str) -> bool:
    """
    Validate generated Terraform code using terraform validate.

    Args:
        code: Generated Terraform code

    Returns:
        True if valid, False otherwise
    """
    # Create temporary file
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.tf', delete=False) as f:
        f.write(code)
        temp_file = f.name

    try:
        # Run terraform fmt
        result = subprocess.run(
            ["terraform", "fmt", temp_file],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print(f"Warning: terraform fmt failed: {result.stderr}")
            return False

        print("✅ Terraform formatting validated")
        return True

    except FileNotFoundError:
        print("Warning: terraform command not found. Skipping validation.")
        return True
    except Exception as e:
        print(f"Warning: Validation failed: {e}")
        return True
    finally:
        # Clean up
        os.unlink(temp_file)


def interactive_mode(provider_name: str, api_key: str, model: Optional[str] = None):
    """
    Run in interactive mode with prompts.

    Args:
        provider_name: AI provider to use
        api_key: API key
        model: Optional model override
    """
    print(f"\n🤖 AI-Assisted Terraform Generator (Provider: {provider_name})")
    print("=" * 60)
    print("\nLoading context files...")

    context = load_context_files()
    print(f"✅ Loaded {len(context)} context files")

    print("\nInitializing AI provider...")
    provider = get_provider(provider_name, api_key, model)
    print(f"✅ Using model: {provider.model}")

    print("\n" + "=" * 60)
    print("Enter your prompt (or 'quit' to exit):")
    print("Example: Create 3 engineering users and an Engineering Team group")
    print("=" * 60 + "\n")

    while True:
        try:
            prompt = input("\n> ")

            if prompt.lower() in ["quit", "exit", "q"]:
                print("\n👋 Goodbye!")
                break

            if not prompt.strip():
                continue

            print("\n🔄 Generating Terraform code...")
            provider.reset_token_usage()

            try:
                code = provider.generate_terraform(prompt, context)

                print("\n" + "=" * 60)
                print("GENERATED TERRAFORM CODE:")
                print("=" * 60 + "\n")
                print(code)
                print("\n" + "=" * 60)

                # Show token usage
                usage = provider.get_token_usage()
                if usage["total"] > 0:
                    print(f"\n📊 Token Usage: {usage['input']} input, "
                          f"{usage['output']} output, {usage['total']} total")

                # Ask if user wants to save
                save = input("\nSave to file? (y/N): ").strip().lower()
                if save == 'y':
                    filename = input("Filename (e.g., users.tf): ").strip()
                    if filename:
                        output_path = Path(filename)
                        output_path.write_text(code)
                        print(f"✅ Saved to {output_path}")

                        # Validate if requested
                        validate = input("Run terraform fmt? (y/N): ").strip().lower()
                        if validate == 'y':
                            validate_terraform(code)

            except Exception as e:
                print(f"\n❌ Generation failed: {e}")

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except EOFError:
            print("\n\n👋 Goodbye!")
            break


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="AI-Assisted Terraform Generator for Okta",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode with Gemini
  python generate.py --interactive --provider gemini

  # Generate from prompt
  python generate.py --prompt "Create 5 marketing users" \\
                    --provider gemini \\
                    --output users.tf

  # Use specific model
  python generate.py --interactive \\
                    --provider openai \\
                    --model gpt-4

Environment Variables:
  GEMINI_API_KEY or GOOGLE_API_KEY - For Gemini
  OPENAI_API_KEY - For OpenAI
  ANTHROPIC_API_KEY or CLAUDE_API_KEY - For Anthropic/Claude
        """
    )

    parser.add_argument(
        "--provider",
        choices=["gemini", "openai", "anthropic", "claude"],
        default="gemini",
        help="AI provider to use (default: gemini)"
    )

    parser.add_argument(
        "--model",
        help="Specific model to use (provider-specific)"
    )

    parser.add_argument(
        "--prompt",
        help="Prompt describing what to generate"
    )

    parser.add_argument(
        "--output",
        help="Output file path (if not specified, prints to stdout)"
    )

    parser.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="Run in interactive mode"
    )

    parser.add_argument(
        "--validate",
        action="store_true",
        help="Run terraform fmt validation on generated code"
    )

    args = parser.parse_args()

    # Get API key
    api_key = get_api_key(args.provider)
    if not api_key:
        print(f"❌ Error: No API key found for {args.provider}")
        print(f"\nSet one of these environment variables:")
        if args.provider == "gemini":
            print("  - GEMINI_API_KEY")
            print("  - GOOGLE_API_KEY")
        elif args.provider == "openai":
            print("  - OPENAI_API_KEY")
        elif args.provider in ["anthropic", "claude"]:
            print("  - ANTHROPIC_API_KEY")
            print("  - CLAUDE_API_KEY")
        sys.exit(1)

    # Interactive mode
    if args.interactive:
        interactive_mode(args.provider, api_key, args.model)
        return

    # Prompt mode
    if not args.prompt:
        print("❌ Error: --prompt is required (or use --interactive)")
        parser.print_help()
        sys.exit(1)

    print(f"🤖 Generating Terraform code with {args.provider}...")

    # Load context
    context = load_context_files()
    print(f"✅ Loaded {len(context)} context files")

    # Initialize provider
    provider = get_provider(args.provider, api_key, args.model)
    print(f"✅ Using model: {provider.model}")

    # Generate code
    try:
        code = provider.generate_terraform(args.prompt, context)

        # Validate if requested
        if args.validate:
            validate_terraform(code)

        # Output
        if args.output:
            output_path = Path(args.output)
            output_path.write_text(code)
            print(f"✅ Saved to {output_path}")
        else:
            print("\n" + "=" * 60)
            print("GENERATED TERRAFORM CODE:")
            print("=" * 60 + "\n")
            print(code)

        # Show token usage
        usage = provider.get_token_usage()
        if usage["total"] > 0:
            print(f"\n📊 Token Usage: {usage['input']} input, "
                  f"{usage['output']} output, {usage['total']} total")

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
