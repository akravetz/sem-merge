"""Tests for content caching functionality."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from sem_merge.cache import CACHE_EXPIRATION_SECONDS, ContentCache


class TestContentCache:
    """Tests for ContentCache class."""

    @pytest.fixture
    def temp_cache_dir(self):
        """Create a temporary directory for cache testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def cache(self, temp_cache_dir):
        """Create a ContentCache instance with temporary directory."""
        return ContentCache(cache_dir=temp_cache_dir)

    def test_cache_initialization(self, temp_cache_dir):
        """Test cache initializes correctly."""
        cache = ContentCache(cache_dir=temp_cache_dir)
        assert cache.cache_dir == temp_cache_dir
        assert cache.cache_file == temp_cache_dir / "processed.json"
        assert cache.cache_data == {}

    def test_content_hash_generation(self, cache):
        """Test content hash generation is consistent."""
        merged = "merged content"
        remote = "remote content"
        file_path = "test.md"

        hash1 = cache._content_hash(merged, remote, file_path)
        hash2 = cache._content_hash(merged, remote, file_path)

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex string length

        # Different content should produce different hash
        hash3 = cache._content_hash("different merged", remote, file_path)
        assert hash1 != hash3

    def test_cache_miss_initially(self, cache):
        """Test cache miss for new content."""
        assert not cache.is_processed("current local", "remote", "test.md")
        assert cache.get_cached_result("current local", "remote", "test.md") is None

    def test_store_and_retrieve_result(self, cache):
        """Test storing and retrieving cached results."""
        remote = "remote content"
        file_path = "test.md"
        merged = "merged content result"

        # Store result
        cache.store_result(remote, file_path, merged)

        # Current content matching merged content should be marked as processed
        assert cache.is_processed(merged, remote, file_path)

        # Should return the current content (which matches merged content)
        result = cache.get_cached_result(merged, remote, file_path)
        assert result == merged

        # Different current content should not be processed
        assert not cache.is_processed("different current", remote, file_path)

    def test_cache_persistence(self, temp_cache_dir):
        """Test cache data persists across instances."""
        remote = "remote content"
        file_path = "test.md"
        merged = "merged content result"

        # Store in first cache instance
        cache1 = ContentCache(cache_dir=temp_cache_dir)
        cache1.store_result(remote, file_path, merged)

        # Create new instance and verify data persists
        cache2 = ContentCache(cache_dir=temp_cache_dir)
        assert cache2.is_processed(merged, remote, file_path)
        assert cache2.get_cached_result(merged, remote, file_path) == merged

    def test_cache_expiration(self, cache):
        """Test cache entries expire after the defined expiration time."""
        remote = "remote content"
        file_path = "test.md"
        merged = "merged content result"

        # Store result with old timestamp
        with patch("sem_merge.cache.time.time", return_value=1000):
            cache.store_result(remote, file_path, merged)

        # Check it's cached (at the same time)
        with patch("sem_merge.cache.time.time", return_value=1000):
            assert cache.is_processed(merged, remote, file_path)

        # Simulate time after expiration (1 hour past expiration)
        expiration_time = 1000 + CACHE_EXPIRATION_SECONDS + 3600
        with patch("sem_merge.cache.time.time", return_value=expiration_time):
            assert not cache.is_processed(merged, remote, file_path)
            assert cache.get_cached_result(merged, remote, file_path) is None

    def test_different_content_different_cache(self, cache):
        """Test different content combinations have separate cache entries."""
        merged1 = "merged content 1"
        merged2 = "merged content 2"

        # Store two different content combinations
        cache.store_result("remote1", "test.md", merged1)
        cache.store_result("remote2", "test.md", merged2)

        # Both should be cached separately
        # Check if current content matches merged content
        assert cache.get_cached_result(merged1, "remote1", "test.md") == merged1
        assert cache.get_cached_result(merged2, "remote2", "test.md") == merged2

    def test_same_content_different_files(self, cache):
        """Test same content in different files have separate cache entries."""
        remote = "remote content"
        merged1 = "merged content 1"
        merged2 = "merged content 2"

        # Store same content for different files
        cache.store_result(remote, "file1.md", merged1)
        cache.store_result(remote, "file2.md", merged2)

        # Should be cached separately - check if current content matches merged content
        assert cache.get_cached_result(merged1, remote, "file1.md") == merged1
        assert cache.get_cached_result(merged2, remote, "file2.md") == merged2

    def test_clear_cache(self, cache, temp_cache_dir):
        """Test clearing the cache."""
        merged = "merged content"
        cache.store_result("remote", "test.md", merged)
        assert cache.is_processed(merged, "remote", "test.md")

        cache.clear_cache()

        assert not cache.is_processed(merged, "remote", "test.md")
        assert not (temp_cache_dir / "processed.json").exists()

    def test_cleanup_old_entries(self, cache):
        """Test cleanup of old cache entries."""
        # Current time will be 1000 + 300 * 3600 = 1081000
        # Expiration limit for is_processed check
        # So the remaining entry should be newer than current_time -
        # CACHE_EXPIRATION_SECONDS

        # Store entries with different ages
        with patch(
            "sem_merge.cache.time.time", return_value=1000
        ):  # Very old - should be removed
            cache.store_result("remote1", "test1.md", "merged1")

        with patch(
            "sem_merge.cache.time.time", return_value=1000 + 100 * 3600
        ):  # Old - should be removed
            cache.store_result("remote2", "test2.md", "merged2")

        # Make this entry recent enough to pass the is_processed expiration check
        with patch(
            "sem_merge.cache.time.time", return_value=1000 + 295 * 3600
        ):  # 5 hours old - should remain
            cache.store_result("remote3", "test3.md", "merged3")

        # All should be present initially
        assert len(cache.cache_data) == 3

        # Cleanup entries older than 150 hours
        with patch("sem_merge.cache.time.time", return_value=1000 + 300 * 3600):
            cache.cleanup_old_entries(max_age_hours=150)

        # Only the newest entry should remain (merged3)
        assert len(cache.cache_data) == 1

        with patch("sem_merge.cache.time.time", return_value=1000 + 300 * 3600):
            assert cache.is_processed("merged3", "remote3", "test3.md")

    def test_corrupted_cache_file_handling(self, temp_cache_dir):
        """Test handling of corrupted cache files."""
        cache_file = temp_cache_dir / "processed.json"
        cache_file.parent.mkdir(exist_ok=True)

        # Create corrupted cache file
        with open(cache_file, "w") as f:
            f.write("invalid json content")

        # Should handle gracefully and start with empty cache
        cache = ContentCache(cache_dir=temp_cache_dir)
        assert cache.cache_data == {}

    def test_cache_file_creation_permission_error(self, cache):
        """Test handling of cache file creation errors."""
        # Mock OSError during save - should be caught and handled gracefully
        with patch.object(cache, "_save_cache", side_effect=OSError):
            # Should not raise error, just continue without persisting to disk
            cache.store_result("remote", "test.md", "merged")

        # Cache should still work in memory (but not persisted to disk)
        assert cache.is_processed("merged", "remote", "test.md")
