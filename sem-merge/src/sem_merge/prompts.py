"""AI prompts for semantic merging."""


def build_merge_prompt(local: str, remote: str, file_path: str) -> str:
    """Build prompt for semantic merging with DeepSeek R1."""
    return f"""You are an expert technical writer. Semantically merge two versions of a documentation file.

File: {file_path}

LOCAL VERSION (current changes):
```
{local}
```

REMOTE MAIN VERSION:
```
{remote}
```

Create a merged version that:
1. Preserves document structure and formatting
2. Combines information intelligently
3. Eliminates duplicates
4. Maintains consistent tone
5. Retains all important information

Return ONLY the merged content, no explanations."""
