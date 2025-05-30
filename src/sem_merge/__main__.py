"""Entry point for pre-commit hook execution."""

import asyncio
import os
import sys
from pathlib import Path

from .merger import SemanticMerger


async def main() -> int:
    """Main entry point - process files passed by pre-commit."""
    # Get API key from environment
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("Warning: DEEPSEEK_API_KEY not set, skipping semantic merge")
        return 0  # Don't block commits

    # Get files from command line (pre-commit passes them)
    files = [Path(f) for f in sys.argv[1:] if Path(f).exists()]

    if not files:
        return 0

    # Process files
    merger = SemanticMerger(api_key)
    success_count = await merger.process_files(files)

    print(f"Semantically merged {success_count}/{len(files)} files")
    return 0  # Never block commits


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
