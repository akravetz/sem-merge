"""Core semantic merging functionality."""

import asyncio
from pathlib import Path

from openai import AsyncOpenAI  # type: ignore[import-untyped]

from .cache import ContentCache
from .git_ops import GitOperations
from .prompts import build_merge_prompt


class SemanticMerger:
    """Handles semantic merging of documentation files."""

    def __init__(
        self,
        provider: str,
        api_key: str,
        model: str | None = None,
        git_ops: GitOperations | None = None,
        cache: ContentCache | None = None,
    ):
        """Initialize the semantic merger with provider configuration.

        Args:
            provider: Either 'openai' or 'deepseek'
            api_key: API key for the provider
            model: Optional model override
            git_ops: Optional GitOperations instance for dependency injection
            cache: Optional ContentCache instance for caching processed content
        """
        if provider == "openai":
            self.client = AsyncOpenAI(api_key=api_key)  # type: ignore[misc]
            self.model = model or "o3"
        elif provider == "deepseek":
            self.client = AsyncOpenAI(  # type: ignore[misc]
                api_key=api_key, base_url="https://api.deepseek.com"
            )
            self.model = model or "deepseek-chat"
        else:
            raise ValueError(f"Unsupported provider: {provider}")

        self.provider = provider
        self.git_ops = git_ops or GitOperations()
        self.cache = cache or ContentCache()

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

        # Check if current content is already the result of a previous merge
        file_path_str = str(file_path)
        cached_result = self.cache.get_cached_result(
            local_content, remote_content, file_path_str
        )

        if cached_result is not None:
            # Current content is already merged, skip processing
            return True

        # Perform semantic merge - let exceptions bubble up
        merged_content = await self._merge_content(
            local_content, remote_content, file_path
        )

        # Store the result in cache for future use
        self.cache.store_result(remote_content, file_path_str, merged_content)

        # Write back to file
        file_path.write_text(merged_content, encoding="utf-8")
        return True

    async def _merge_content(self, local: str, remote: str, file_path: Path) -> str:
        """Merge content using AI provider."""
        prompt = build_merge_prompt(local, remote, str(file_path))

        # Make API call - let exceptions bubble up for hard failure
        response = await self.client.chat.completions.create(  # type: ignore[misc]
            model=self.model,  # type: ignore[arg-type]
            messages=[{"role": "user", "content": prompt}],  # type: ignore[arg-type]
            max_tokens=4000,
            temperature=0.1,
        )

        content = response.choices[0].message.content  # type: ignore[misc]
        if not content:
            raise ValueError(f"AI provider returned empty content for {file_path}")

        return content.strip()
