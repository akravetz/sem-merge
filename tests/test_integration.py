"""Integration tests for semantic merger with real API calls."""

import os
from unittest.mock import Mock, patch

import pytest

from sem_merge.merger import SemanticMerger

# Skip integration tests if no API key is available
pytestmark = pytest.mark.skipif(
    not os.getenv("DEEPSEEK_API_KEY"),
    reason="DEEPSEEK_API_KEY not set - skipping integration tests",
)


class TestSemanticMergerIntegration:
    """Integration tests that make real API calls to DeepSeek."""

    @pytest.fixture
    def mock_git_ops(self):
        """Mock git operations for integration tests."""
        with patch("sem_merge.merger.GitOperations") as mock_class:
            mock_instance = Mock()
            mock_class.return_value = mock_instance
            yield mock_instance

    @pytest.fixture
    def merger(self, mock_git_ops):
        """Create a real SemanticMerger instance with API key."""
        api_key = os.getenv("DEEPSEEK_API_KEY")
        return SemanticMerger(api_key)

    @pytest.fixture
    def sample_files(self):
        """Sample documentation content for merging."""
        local_content = """# Project Documentation

## Overview
This project provides a comprehensive solution for document management.

## Features
- Document storage
- Version control
- User permissions

## Installation
1. Clone the repository
2. Install dependencies
3. Configure settings

## Usage
Start the application and access the web interface.
"""

        remote_content = """# Project Documentation

## Overview
This project is a powerful document management system.

## Features
- Document storage and retrieval
- Advanced search capabilities
- User authentication

## Setup
1. Download the software
2. Run the installer
3. Launch the application

## API Documentation
The REST API provides programmatic access to all features.
"""
        return local_content, remote_content

    @pytest.mark.asyncio
    async def test_real_semantic_merge(
        self, merger, mock_git_ops, sample_files, tmp_path
    ):
        """Test semantic merging with real DeepSeek API call."""
        local_content, remote_content = sample_files

        # Create a test file
        test_file = tmp_path / "test_doc.md"
        test_file.write_text(local_content)

        # Mock git operations to return remote content
        mock_git_ops.get_main_branch_content.return_value = remote_content

        # Process the file (this will make a real API call)
        result = await merger._process_file(test_file)

        # Verify the merge was successful
        assert result is True

        # Read the merged content
        merged_content = test_file.read_text()

        # Verify merged content is longer than both inputs
        assert len(merged_content) > len(local_content), (
            f"Merged content ({len(merged_content)} chars) should be longer "
            f"than local ({len(local_content)} chars)"
        )
        assert len(merged_content) > len(remote_content), (
            f"Merged content ({len(merged_content)} chars) should be longer "
            f"than remote ({len(remote_content)} chars)"
        )

        # Verify merged content contains elements from both sources
        # Check for common elements that should be preserved
        assert "# Project Documentation" in merged_content
        assert "## Overview" in merged_content
        assert "## Features" in merged_content

        # Check that it combines information (both installation and setup
        # should be present in some form)
        merged_lower = merged_content.lower()
        assert any(
            word in merged_lower for word in ["install", "setup", "configure"]
        ), "Merged content should contain installation/setup information"

        # Verify it's not just concatenation (should be intelligently merged)
        assert merged_content != local_content + remote_content
        assert merged_content != remote_content + local_content

        print("✓ Integration test passed:")
        print(f"  Local content: {len(local_content)} characters")
        print(f"  Remote content: {len(remote_content)} characters")
        print(f"  Merged content: {len(merged_content)} characters")
        print(f"  Merged content preview: {merged_content[:200]}...")

    @pytest.mark.asyncio
    async def test_merge_preserves_structure(self, merger, mock_git_ops, tmp_path):
        """Test that merging preserves markdown structure."""
        local_content = """# Main Title

## Section A
Content A from local.

## Section B
Local content for section B.
"""

        remote_content = """# Main Title

## Section A
Content A from remote with additional details.

## Section C
New section C from remote.
"""

        # Create test file
        test_file = tmp_path / "structure_test.md"
        test_file.write_text(local_content)

        # Mock git operations
        mock_git_ops.get_main_branch_content.return_value = remote_content

        # Process file
        result = await merger._process_file(test_file)
        assert result is True

        # Verify structure is preserved
        merged_content = test_file.read_text()

        # Should contain main title
        assert "# Main Title" in merged_content

        # Should have section headers (## format)
        section_count = merged_content.count("## Section")
        assert section_count >= 2, "Should preserve multiple sections"

        # Should be longer than inputs
        assert len(merged_content) > len(local_content)
        assert len(merged_content) > len(remote_content)

        print("✓ Structure preservation test passed:")
        print(f"  Sections found: {section_count}")
        print(f"  Total length: {len(merged_content)} characters")
