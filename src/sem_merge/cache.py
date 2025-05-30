"""Content caching system to prevent infinite processing loops."""

import hashlib
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional

# Cache expiration time in seconds (24 hours)
CACHE_EXPIRATION_SECONDS = 24 * 60 * 60  # 86400 seconds


class ContentCache:
    """Manages caching of processed content to prevent infinite loops."""

    def __init__(self, cache_dir: Path = Path(".sem-merge-cache")):
        """Initialize the content cache.
        
        Args:
            cache_dir: Directory to store cache files
        """
        self.cache_dir = cache_dir
        self.cache_file = cache_dir / "processed.json"
        self.cache_data: Dict[str, Any] = {}
        self._load_cache()

    def _load_cache(self) -> None:
        """Load existing cache data from disk."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.cache_data = json.load(f)
            except (json.JSONDecodeError, OSError):
                # If cache is corrupted, start fresh
                self.cache_data = {}

    def _save_cache(self) -> None:
        """Save cache data to disk."""
        # Ensure cache directory exists
        self.cache_dir.mkdir(exist_ok=True)
        
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache_data, f, indent=2)
        except OSError:
            # If we can't save cache, continue without it
            pass

    def _content_hash(self, local_content: str, remote_content: str, file_path: str) -> str:
        """Generate a hash for the content combination.
        
        Args:
            local_content: Current local file content
            remote_content: Remote branch file content  
            file_path: Path of the file being processed
            
        Returns:
            SHA-256 hash of the content combination
        """
        content_key = f"{file_path}:{local_content}:{remote_content}"
        return hashlib.sha256(content_key.encode('utf-8')).hexdigest()

    def is_processed(self, local_content: str, remote_content: str, file_path: str) -> bool:
        """Check if this content combination has already been processed.
        
        Args:
            local_content: Current local file content
            remote_content: Remote branch file content
            file_path: Path of the file being processed
            
        Returns:
            True if already processed, False otherwise
        """
        content_hash = self._content_hash(local_content, remote_content, file_path)
        
        if content_hash not in self.cache_data:
            return False
            
        # Check if cache entry is still valid (not too old)
        entry = self.cache_data[content_hash]
        current_time = time.time()
        
        # Cache expires after the defined expiration time
        if current_time - entry.get('timestamp', 0) > CACHE_EXPIRATION_SECONDS:
            del self.cache_data[content_hash]
            self._save_cache()
            return False
            
        return True

    def get_cached_result(self, local_content: str, remote_content: str, file_path: str) -> Optional[str]:
        """Get cached merge result if available.
        
        Args:
            local_content: Current local file content
            remote_content: Remote branch file content
            file_path: Path of the file being processed
            
        Returns:
            Cached merged content if available, None otherwise
        """
        if not self.is_processed(local_content, remote_content, file_path):
            return None
            
        content_hash = self._content_hash(local_content, remote_content, file_path)
        return self.cache_data[content_hash].get('merged_content')

    def store_result(self, local_content: str, remote_content: str, file_path: str, merged_content: str) -> None:
        """Store a merge result in the cache.
        
        Args:
            local_content: Current local file content
            remote_content: Remote branch file content
            file_path: Path of the file being processed
            merged_content: The AI-generated merged content
        """
        content_hash = self._content_hash(local_content, remote_content, file_path)
        
        self.cache_data[content_hash] = {
            'merged_content': merged_content,
            'timestamp': time.time(),
            'file_path': file_path
        }
        
        try:
            self._save_cache()
        except OSError:
            # If save fails, cache will still work in memory
            pass

    def clear_cache(self) -> None:
        """Clear all cached data."""
        self.cache_data = {}
        if self.cache_file.exists():
            try:
                self.cache_file.unlink()
            except OSError:
                pass
                
    def cleanup_old_entries(self, max_age_hours: int = 168) -> None:  # Default: 1 week
        """Remove old cache entries.
        
        Args:
            max_age_hours: Maximum age in hours before entries are removed
        """
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        expired_keys = [
            key for key, entry in self.cache_data.items()
            if current_time - entry.get('timestamp', 0) > max_age_seconds
        ]
        
        for key in expired_keys:
            del self.cache_data[key]
            
        if expired_keys:
            self._save_cache() 