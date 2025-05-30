"""Git operations for retrieving remote content."""

from pathlib import Path

from git import InvalidGitRepositoryError, Repo


class GitOperations:
    """Handle git operations for semantic merging."""

    def __init__(self):
        try:
            self.repo = Repo(search_parent_directories=True)
        except InvalidGitRepositoryError as err:
            raise RuntimeError("Not in a git repository") from err

    def get_main_branch_content(self, file_path: Path) -> str | None:
        """Get file content from remote main branch."""
        try:
            # Fetch latest from remote
            origin = self.repo.remote("origin")
            origin.fetch()

            # Get content from origin/main
            blob = self.repo.commit("origin/main").tree / str(file_path)
            return blob.data_stream.read().decode("utf-8")

        except (KeyError, Exception):
            # If file doesn't exist in remote main or we can't fetch remote,
            # return None (skip merge)
            return None
