"""AI prompts for semantic merging."""


def build_merge_prompt(local: str, remote: str, file_path: str) -> str:
    """Build prompt for semantic merging with DeepSeek R1."""
    prompt = (
        "You are an expert technical writer. "
        "Semantically merge two versions of a documentation file.\n\n"
        f"File: {file_path}\n\n"
        "LOCAL VERSION (current changes):\n"
        f"```\n{local}\n```\n\n"
        "REMOTE MAIN VERSION:\n"
        f"```\n{remote}\n```\n\n"
        "Create a merged version that:\n"
        "1. Preserves document structure and formatting\n"
        "2. Combines information intelligently\n"
        "3. Eliminates duplicates\n"
        "4. Maintains consistent tone\n"
        "5. Retains all important information\n\n"
        "Return ONLY the merged content, no explanations."
    )
    return prompt
