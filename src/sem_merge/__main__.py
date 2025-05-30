#!/usr/bin/env python3
"""Entry point for semantic merge pre-commit hook."""

import argparse
import asyncio
import os
import sys
from pathlib import Path

from .merger import SemanticMerger


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Semantic merge pre-commit hook")
    parser.add_argument(
        "--ai-provider",
        choices=["openai", "deepseek"],
        help="AI provider to use (required if both API keys present)",
    )
    parser.add_argument("--model", help="Model to use (overrides default for provider)")
    parser.add_argument("files", nargs="*", help="Files to process")
    return parser.parse_args()


def determine_provider_and_key(args: argparse.Namespace) -> tuple[str, str]:
    """Determine AI provider and API key based on environment and arguments."""
    openai_key = os.getenv("OPENAI_API_KEY")
    deepseek_key = os.getenv("DEEPSEEK_API_KEY")

    # Count available keys
    available_keys = sum([bool(openai_key), bool(deepseek_key)])

    if available_keys == 0:
        raise ValueError("No API key found. Set OPENAI_API_KEY or DEEPSEEK_API_KEY")

    if available_keys == 2:
        # Both keys present - require explicit provider flag
        if not args.ai_provider:
            raise ValueError(
                "Both OPENAI_API_KEY and DEEPSEEK_API_KEY found. "
                "Must specify --ai-provider (openai or deepseek)"
            )
        provider = args.ai_provider
        if provider == "openai":
            assert openai_key is not None  # We know it exists from available_keys check
            api_key = openai_key
        else:
            assert (
                deepseek_key is not None
            )  # We know it exists from available_keys check
            api_key = deepseek_key
    else:
        # Only one key present - auto-select provider
        if args.ai_provider:
            # User specified provider but key doesn't match
            if args.ai_provider == "openai" and not openai_key:
                raise ValueError(
                    "--ai-provider=openai specified but OPENAI_API_KEY not found"
                )
            if args.ai_provider == "deepseek" and not deepseek_key:
                raise ValueError(
                    "--ai-provider=deepseek specified but DEEPSEEK_API_KEY not found"
                )

        # Auto-select based on available key
        if openai_key:
            provider = "openai"
            api_key = openai_key
        else:
            assert deepseek_key is not None  # We know exactly one key exists
            provider = "deepseek"
            api_key = deepseek_key

    return provider, api_key


def filter_documentation_files(file_paths: list[str]) -> list[Path]:
    """Filter for documentation files that exist."""
    doc_extensions = {".md", ".rst", ".txt", ".adoc", ".asciidoc"}

    filtered = []
    for file_path in file_paths:
        path = Path(file_path)
        if path.suffix.lower() in doc_extensions and path.exists():
            filtered.append(path)

    return filtered


async def main() -> int:
    """Main entry point."""
    args = parse_args()

    # Determine provider and API key
    provider, api_key = determine_provider_and_key(args)

    # Filter files
    documentation_files = filter_documentation_files(args.files)

    if not documentation_files:
        print("No documentation files to process")
        return 0

    print(f"Processing {len(documentation_files)} files with {provider}")

    # Initialize merger and process files
    merger = SemanticMerger(provider, api_key, args.model)
    merged_count = await merger.process_files(documentation_files)

    print(f"Successfully merged {merged_count} files")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
