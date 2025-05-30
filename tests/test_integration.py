"""Integration tests for semantic merge functionality."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from sem_merge.__main__ import (
    determine_provider_and_key,
    filter_documentation_files,
    parse_args,
)
from sem_merge.merger import SemanticMerger
from sem_merge.cache import ContentCache


@pytest.mark.skipif(
    not (os.getenv("OPENAI_API_KEY") or os.getenv("DEEPSEEK_API_KEY")),
    reason="No API key available for integration test",
)
@pytest.mark.asyncio
async def test_real_api_integration():
    """Test with real API call (when API key available)."""
    # Determine which provider to use based on available keys
    openai_key = os.getenv("OPENAI_API_KEY")
    deepseek_key = os.getenv("DEEPSEEK_API_KEY")

    if openai_key:
        provider = "openai"
        api_key = openai_key
    else:
        provider = "deepseek"
        api_key = deepseek_key

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test file with different content
        test_file = Path(temp_dir) / "test.md"
        test_file.write_text("# Local Version\nThis is local content.")

        # Create a mock GitOperations instance for dependency injection
        from unittest.mock import Mock
        
        mock_git_ops = Mock()
        mock_git_ops.get_main_branch_content.return_value = (
            "# Remote Version\nThis is remote content."
        )
        
        # Use a temporary cache directory for testing
        cache_dir = Path(temp_dir) / "cache"
        test_cache = ContentCache(cache_dir=cache_dir)

        # Create merger with injected mock GitOperations and test cache
        merger = SemanticMerger(provider, api_key, git_ops=mock_git_ops, cache=test_cache)
        result = await merger.process_files([test_file])

        # Should successfully merge (real API call)
        assert result == 1

        # Content should be changed (merged)
        merged_content = test_file.read_text()
        assert merged_content != "# Local Version\nThis is local content."
        assert len(merged_content) > 0


class TestArgumentParsing:
    """Test argument parsing logic."""

    def test_parse_args_minimal(self):
        """Test parsing with minimal arguments."""
        with patch("sys.argv", ["sem_merge", "file1.md", "file2.md"]):
            args = parse_args()
            assert args.files == ["file1.md", "file2.md"]
            assert args.ai_provider is None
            assert args.model is None

    def test_parse_args_with_provider(self):
        """Test parsing with provider argument."""
        with patch("sys.argv", ["sem_merge", "--ai-provider", "openai", "file.md"]):
            args = parse_args()
            assert args.ai_provider == "openai"
            assert args.files == ["file.md"]

    def test_parse_args_with_model(self):
        """Test parsing with model argument."""
        with patch("sys.argv", ["sem_merge", "--model", "gpt-4", "file.md"]):
            args = parse_args()
            assert args.model == "gpt-4"
            assert args.files == ["file.md"]


class TestProviderDetermination:
    """Test provider determination logic."""

    def test_no_api_keys(self):
        """Test error when no API keys available."""
        with patch("sys.argv", ["sem_merge"]):
            args = parse_args()
            with patch.dict("os.environ", {}, clear=True):
                with pytest.raises(ValueError, match="No API key found"):
                    determine_provider_and_key(args)

    def test_only_openai_key(self):
        """Test auto-selection with only OpenAI key."""
        with patch("sys.argv", ["sem_merge"]):
            args = parse_args()
            with patch.dict(
                "os.environ", {"OPENAI_API_KEY": "test-openai-key"}, clear=True
            ):
                provider, key = determine_provider_and_key(args)
                assert provider == "openai"
                assert key == "test-openai-key"

    def test_only_deepseek_key(self):
        """Test auto-selection with only DeepSeek key."""
        with patch("sys.argv", ["sem_merge"]):
            args = parse_args()
            with patch.dict(
                "os.environ", {"DEEPSEEK_API_KEY": "test-deepseek-key"}, clear=True
            ):
                provider, key = determine_provider_and_key(args)
                assert provider == "deepseek"
                assert key == "test-deepseek-key"

    def test_both_keys_no_provider_flag(self):
        """Test error when both keys present but no provider specified."""
        with patch("sys.argv", ["sem_merge"]):
            args = parse_args()
            env = {
                "OPENAI_API_KEY": "test-openai-key",
                "DEEPSEEK_API_KEY": "test-deepseek-key",
            }
            with patch.dict("os.environ", env, clear=True):
                with pytest.raises(ValueError, match="Must specify --ai-provider"):
                    determine_provider_and_key(args)

    def test_both_keys_with_provider_flag(self):
        """Test explicit provider selection when both keys present."""
        with patch("sys.argv", ["sem_merge", "--ai-provider", "openai"]):
            args = parse_args()

        env = {
            "OPENAI_API_KEY": "test-openai-key",
            "DEEPSEEK_API_KEY": "test-deepseek-key",
        }
        with patch.dict("os.environ", env, clear=True):
            provider, key = determine_provider_and_key(args)
            assert provider == "openai"
            assert key == "test-openai-key"

    def test_provider_flag_without_matching_key(self):
        """Test error when provider flag doesn't match available key."""
        with patch("sys.argv", ["sem_merge", "--ai-provider", "openai"]):
            args = parse_args()

        with patch.dict(
            "os.environ", {"DEEPSEEK_API_KEY": "test-deepseek-key"}, clear=True
        ):
            with pytest.raises(ValueError, match="OPENAI_API_KEY not found"):
                determine_provider_and_key(args)


class TestFileFiltering:
    """Test documentation file filtering."""

    def test_filter_documentation_files(self):
        """Test filtering of documentation files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create various file types
            (temp_path / "doc.md").write_text("markdown")
            (temp_path / "readme.rst").write_text("restructured text")
            (temp_path / "notes.txt").write_text("text")
            (temp_path / "guide.adoc").write_text("asciidoc")
            (temp_path / "script.py").write_text("python code")

            file_paths = [
                str(temp_path / "doc.md"),
                str(temp_path / "readme.rst"),
                str(temp_path / "notes.txt"),
                str(temp_path / "guide.adoc"),
                str(temp_path / "script.py"),
                str(temp_path / "nonexistent.md"),  # doesn't exist
            ]

            filtered = filter_documentation_files(file_paths)

            # Should only include existing documentation files
            assert len(filtered) == 4
            assert all(f.suffix in {".md", ".rst", ".txt", ".adoc"} for f in filtered)
            assert all(f.exists() for f in filtered)

    def test_filter_empty_list(self):
        """Test filtering empty file list."""
        result = filter_documentation_files([])
        assert result == []
