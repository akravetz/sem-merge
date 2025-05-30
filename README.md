# sem-merge

AI-powered semantic document merging for git repositories via pre-commit framework.

## Overview

`sem-merge` is a pre-commit hook that automatically merges documentation files (`.md`, `.mdc`) with their counterparts from the remote main branch using AI-powered semantic understanding. It helps maintain consistent documentation across team collaborations by intelligently combining changes while preserving structure and eliminating duplicates.

## Installation

### Prerequisites

- Python 3.13+
- Git repository with a `main` branch
- DeepSeek API key

### Setup

1. Add to your `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/akravetz/sem-merge
    rev: v1.0.0
    hooks:
      - id: semantic-merge
        files: \.(md|mdc)$
        exclude: ^(node_modules/|\.git/|docs/generated/)
```

2. Set your DeepSeek API key:

```bash
export DEEPSEEK_API_KEY="your-api-key-here"
```

3. Install pre-commit hooks:

```bash
pre-commit install
```

## Configuration

### File Selection

Control which files are processed using pre-commit's `files` and `exclude` patterns:

```yaml
- id: semantic-merge
  files: \.(md|mdc|rst)$          # Process these file types
  exclude: ^(docs/generated/|build/|node_modules/)  # Skip these directories
```

### Environment Variables

- `DEEPSEEK_API_KEY` (required): Your DeepSeek API key
- `DEEPSEEK_MODEL` (optional): AI model to use (default: `deepseek-r1`)
- `DEEPSEEK_MAX_TOKENS` (optional): Maximum tokens for AI response (default: `4000`)
- `SEMMERGE_LOG_LEVEL` (optional): Logging level (default: `INFO`)

### Example Configuration

```bash
# Required
export DEEPSEEK_API_KEY="your-deepseek-api-key"

# Optional customization
export DEEPSEEK_MODEL="deepseek-r1"
export DEEPSEEK_MAX_TOKENS="6000"
export SEMMERGE_LOG_LEVEL="DEBUG"
```

## How It Works

1. **Pre-commit Trigger**: When you commit changes, pre-commit runs this hook on modified `.md` and `.mdc` files
2. **Remote Comparison**: For each file, fetches the latest version from `origin/main`
3. **Change Detection**: Skips files that don't exist remotely or are identical
4. **AI Merging**: Uses DeepSeek R1 to semantically merge local and remote versions
5. **File Update**: Updates the staged file with merged content
6. **Commit Continuation**: Allows the commit to proceed with merged documentation

## Features

- **Fail-safe Operation**: Never blocks commits (gracefully handles API failures)
- **Intelligent Merging**: Preserves document structure and eliminates duplicates
- **Parallel Processing**: Handles multiple files concurrently for speed
- **Configurable**: Support for different AI models and parameters
- **Zero Configuration**: Works out of the box with sensible defaults

## Example Usage

```bash
# Make changes to documentation
echo "# New Section\nSome new content" >> README.md

# Stage and commit
git add README.md
git commit -m "Update documentation"

# Output:
# Semantically merged 1/1 files
# [main abc1234] Update documentation
```

## Development

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/your-org/sem-merge
cd sem-merge

# Install dependencies
uv sync --dev

# Run tests
task test

# Run all checks
task check
```

### Available Tasks

- `task test` - Run tests
- `task test-cov` - Run tests with coverage
- `task test-integration` - Run integration tests (requires DEEPSEEK_API_KEY)
- `task lint` - Run ruff linting
- `task format` - Format code with ruff
- `task typecheck` - Run pyrefly type checking
- `task check` - Run all checks
- `task build` - Build package
- `task test-hook` - Test hook locally

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run `task check` to ensure quality
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Troubleshooting

### Common Issues

**Hook doesn't run**: Ensure your files match the `files` pattern in your pre-commit configuration.

**API key not found**: Set the `DEEPSEEK_API_KEY` environment variable.

**Git fetch fails**: Ensure you have network access and the remote repository is accessible.

**Large files**: Consider increasing `DEEPSEEK_MAX_TOKENS` for very large documentation files.

### Debug Mode

Enable debug logging to see detailed operation:

```bash
export SEMMERGE_LOG_LEVEL=DEBUG
git commit
``` 