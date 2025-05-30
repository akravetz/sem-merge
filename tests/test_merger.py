"""Tests for semantic merger functionality."""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from sem_merge.merger import SemanticMerger


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response."""
    response = MagicMock()
    response.choices = [MagicMock()]
    response.choices[0].message.content = "merged content"
    return response


@pytest.fixture
def semantic_merger_openai():
    """Create a SemanticMerger instance with OpenAI provider."""
    return SemanticMerger("openai", "test-key", "gpt-4")


@pytest.fixture
def semantic_merger_deepseek():
    """Create a SemanticMerger instance with DeepSeek provider."""
    return SemanticMerger("deepseek", "test-key")


class TestSemanticMerger:
    """Tests for SemanticMerger class."""

    def test_init_openai_provider(self):
        """Test initialization with OpenAI provider."""
        merger = SemanticMerger("openai", "test-key")
        assert merger.provider == "openai"
        assert merger.model == "o3"
        assert merger.client.api_key == "test-key"

    def test_init_deepseek_provider(self):
        """Test initialization with DeepSeek provider."""
        merger = SemanticMerger("deepseek", "test-key")
        assert merger.provider == "deepseek"
        assert merger.model == "deepseek-r1"
        assert merger.client.api_key == "test-key"
        assert merger.client.base_url == "https://api.deepseek.com"

    def test_init_custom_model(self):
        """Test initialization with custom model."""
        merger = SemanticMerger("openai", "test-key", "custom-model")
        assert merger.model == "custom-model"

    def test_init_invalid_provider(self):
        """Test initialization with invalid provider raises error."""
        with pytest.raises(ValueError, match="Unsupported provider: invalid"):
            SemanticMerger("invalid", "test-key")

    @pytest.mark.asyncio
    async def test_process_files_success(
        self, semantic_merger_openai, mock_openai_response
    ):
        """Test successful file processing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test file
            test_file = Path(temp_dir) / "test.md"
            test_file.write_text("local content")

            # Mock git operations and API calls
            with (
                patch.object(
                    semantic_merger_openai.git_ops,
                    "get_main_branch_content",
                    return_value="remote content",
                ),
                patch.object(
                    semantic_merger_openai.client.chat.completions,
                    "create",
                    new_callable=AsyncMock,
                ) as mock_create,
            ):
                mock_create.return_value = mock_openai_response

                result = await semantic_merger_openai.process_files([test_file])

                assert result == 1
                assert test_file.read_text() == "merged content"
                mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_files_no_remote_content(self, semantic_merger_openai):
        """Test processing when file doesn't exist in main branch."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.md"
            test_file.write_text("local content")

            with patch.object(
                semantic_merger_openai.git_ops,
                "get_main_branch_content",
                return_value=None,
            ):
                result = await semantic_merger_openai.process_files([test_file])

                assert result == 0
                assert test_file.read_text() == "local content"  # Unchanged

    @pytest.mark.asyncio
    async def test_process_files_no_changes(self, semantic_merger_openai):
        """Test processing when local and remote content are identical."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.md"
            test_file.write_text("same content")

            with patch.object(
                semantic_merger_openai.git_ops,
                "get_main_branch_content",
                return_value="same content",
            ):
                result = await semantic_merger_openai.process_files([test_file])

                assert result == 0
                assert test_file.read_text() == "same content"  # Unchanged

    @pytest.mark.asyncio
    async def test_merge_content_openai(
        self, semantic_merger_openai, mock_openai_response
    ):
        """Test content merging with OpenAI provider."""
        with patch.object(
            semantic_merger_openai.client.chat.completions,
            "create",
            new_callable=AsyncMock,
        ) as mock_create:
            mock_create.return_value = mock_openai_response

            result = await semantic_merger_openai._merge_content(
                "local", "remote", Path("test.md")
            )

            assert result == "merged content"
            mock_create.assert_called_once()

            # Check the call was made with correct model and parameters
            call_args = mock_create.call_args
            assert call_args.kwargs["model"] == "gpt-4"
            assert call_args.kwargs["max_tokens"] == 4000
            assert call_args.kwargs["temperature"] == 0.1
            assert len(call_args.kwargs["messages"]) == 1
            assert call_args.kwargs["messages"][0]["role"] == "user"
            assert "local" in call_args.kwargs["messages"][0]["content"]
            assert "remote" in call_args.kwargs["messages"][0]["content"]

    @pytest.mark.asyncio
    async def test_merge_content_deepseek(
        self, semantic_merger_deepseek, mock_openai_response
    ):
        """Test content merging with DeepSeek provider."""
        with patch.object(
            semantic_merger_deepseek.client.chat.completions,
            "create",
            new_callable=AsyncMock,
        ) as mock_create:
            mock_create.return_value = mock_openai_response

            result = await semantic_merger_deepseek._merge_content(
                "local", "remote", Path("test.md")
            )

            assert result == "merged content"
            mock_create.assert_called_once()

            # Check the call was made with correct model and parameters
            call_args = mock_create.call_args
            assert call_args.kwargs["model"] == "deepseek-r1"
            assert call_args.kwargs["max_tokens"] == 4000
            assert call_args.kwargs["temperature"] == 0.1
            assert len(call_args.kwargs["messages"]) == 1
            assert call_args.kwargs["messages"][0]["role"] == "user"
            assert "local" in call_args.kwargs["messages"][0]["content"]
            assert "remote" in call_args.kwargs["messages"][0]["content"]

    @pytest.mark.asyncio
    async def test_merge_content_empty_response(self, semantic_merger_openai):
        """Test handling of empty API response."""
        response = MagicMock()
        response.choices = [MagicMock()]
        response.choices[0].message.content = None

        with patch.object(
            semantic_merger_openai.client.chat.completions,
            "create",
            new_callable=AsyncMock,
        ) as mock_create:
            mock_create.return_value = response

            with pytest.raises(ValueError, match="AI provider returned empty content"):
                await semantic_merger_openai._merge_content(
                    "local", "remote", Path("test.md")
                )
