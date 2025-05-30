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
        "- Preserves document structure and formatting\n"
        "- Combines information intelligently\n"
        "- Eliminates duplicates\n"
        "- Maintains consistent tone\n"
        "- Retains all important information\n"
        "- Does not add ``` tags at the beginning or end of the file\n"
        "- Remove any trailing newline or whitespace on the final document\n\n"
        "Return ONLY the merged content, no explanations."
    )
    return prompt
