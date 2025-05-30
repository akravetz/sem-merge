"""Core semantic merging functionality."""

import asyncio
import os
from pathlib import Path

from openai import AsyncOpenAI  # type: ignore[import-untyped]

from .git_ops import GitOperations
from .prompts import build_merge_prompt


class SemanticMerger:
    """Handles semantic merging of documentation files."""

    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)  # type: ignore[misc]
        # Use deepseek-r1 as default model via OpenAI-compatible API
        self.model = os.getenv("DEEPSEEK_MODEL", "deepseek-r1")
        self.max_tokens = int(os.getenv("DEEPSEEK_MAX_TOKENS", "4000"))
        self.git_ops = GitOperations()

    async def process_files(self, files: list[Path]) -> int:
        """Process files for semantic merging.

        Returns count of successfully merged files.
        """
        tasks = [self._process_file(file_path) for file_path in files]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        success_count = sum(1 for result in results if result is True)
        return success_count

    async def _process_file(self, file_path: Path) -> bool:
        """Process a single file. Returns True if successfully merged."""
        try:
            # Read local content
            local_content = file_path.read_text(encoding="utf-8")

            # Get remote content from main branch
            remote_content = self.git_ops.get_main_branch_content(file_path)

            if remote_content is None:
                # File doesn't exist in main branch, skip
                return False

            if local_content == remote_content:
                # No changes, skip
                return False

            # Perform semantic merge
            merged_content = await self._merge_content(
                local_content, remote_content, file_path
            )

            # Write back to file
            file_path.write_text(merged_content, encoding="utf-8")
            return True

        except Exception as e:
            print(f"Warning: Could not process {file_path}: {e}")
            return False  # Don't block commits on errors

    async def _merge_content(self, local: str, remote: str, file_path: Path) -> str:
        """Merge content using DeepSeek R1 API."""
        prompt = build_merge_prompt(local, remote, str(file_path))

        # Type ignore for DeepSeek API call due to strict typing requirements
        response = await self.client.chat.completions.create(  # type: ignore[misc]
            model=self.model,  # type: ignore[arg-type]
            messages=[{"role": "user", "content": prompt}],  # type: ignore[arg-type]
            max_tokens=self.max_tokens,
            temperature=0.1,
        )

        content = response.choices[0].message.content  # type: ignore[misc]
        return content.strip() if content else ""
