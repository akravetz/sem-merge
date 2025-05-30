"""Tests for the semantic merger."""

from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from sem_merge.merger import SemanticMerger


@pytest.fixture
def mock_git_ops():
    """Mock git operations."""
    with patch("sem_merge.merger.GitOperations") as mock_class:
        mock_instance = Mock()
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def merger(mock_git_ops):
    """Create a SemanticMerger instance with mocked dependencies."""
    with patch("sem_merge.merger.AsyncOpenAI") as mock_openai:
        mock_client = AsyncMock()
        mock_openai.return_value = mock_client

        merger = SemanticMerger("test-api-key")
        merger.client = mock_client
        yield merger


class TestSemanticMerger:
    """Tests for SemanticMerger class."""

    def test_init(self, mock_git_ops):
        """Test SemanticMerger initialization."""
        with patch("sem_merge.merger.AsyncOpenAI"):
            merger = SemanticMerger("test-key")
            assert merger.model == "deepseek-r1"
            assert merger.max_tokens == 4000

    @pytest.mark.asyncio
    async def test_process_files_empty_list(self, merger):
        """Test processing empty file list."""
        result = await merger.process_files([])
        assert result == 0

    @pytest.mark.asyncio
    async def test_process_file_no_remote_content(self, merger, tmp_path, mock_git_ops):
        """Test processing file with no remote content."""
        # Create a test file
        test_file = tmp_path / "test.md"
        test_file.write_text("# Test Content")

        # Mock git operations to return None (file doesn't exist in remote)
        mock_git_ops.get_main_branch_content.return_value = None

        result = await merger._process_file(test_file)
        assert result is False

    @pytest.mark.asyncio
    async def test_process_file_identical_content(self, merger, tmp_path, mock_git_ops):
        """Test processing file with identical local and remote content."""
        # Create a test file
        test_file = tmp_path / "test.md"
        content = "# Test Content"
        test_file.write_text(content)

        # Mock git operations to return same content
        mock_git_ops.get_main_branch_content.return_value = content

        result = await merger._process_file(test_file)
        assert result is False

    @pytest.mark.asyncio
    async def test_merge_content(self, merger):
        """Test content merging with mocked API response."""
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "# Merged Content"

        merger.client.chat.completions.create = AsyncMock(return_value=mock_response)

        result = await merger._merge_content("local", "remote", Path("test.md"))
        assert result == "# Merged Content"

        # Verify API was called with correct parameters
        merger.client.chat.completions.create.assert_called_once()
