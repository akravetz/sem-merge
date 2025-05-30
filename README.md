# sem-merge

[![Tests](https://github.com/akravetz/sem-merge/actions/workflows/test.yml/badge.svg)](https://github.com/akravetz/sem-merge/actions/workflows/test.yml)
[![PyPI version](https://badge.fury.io/py/sem-merge.svg)](https://badge.fury.io/py/sem-merge)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

A pre-commit hook that performs AI-powered semantic merging of documentation files, intelligently combining changes from your local branch with the main branch instead of traditional line-by-line merging.

## Features

- **Multi-Provider AI Support**: Works with both OpenAI (o3) and DeepSeek (R1) models
- **Smart Auto-Detection**: Automatically selects provider based on available API keys
- **Semantic Understanding**: AI comprehends document structure and meaning for intelligent merging
- **Documentation Focus**: Targets `.md`, `.rst`, `.txt`, `.adoc`, and `.asciidoc` files
- **Git Integration**: Seamlessly integrates with your existing pre-commit workflow
- **Async Processing**: Handles multiple files concurrently for better performance
- **Type Safe**: Built with modern Python type hints and strict linting

## Installation

### As a pre-commit hook (recommended)

Add this to your `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/akravetz/sem-merge
    rev: v1.5.0  # Use the latest version
    hooks:
      - id: semantic-merg
        files: \.(md|mdc)$
        exclude: ^(node_modules/|\.git/|docs/generated/)e
```

to update to the latest version (recommended):
```bash
pre-commit autoupdate
```

### Direct installation

```bash
pip install sem-merge
```

## Configuration

### API Keys

Set up your API key for your preferred provider:

**Option 1: OpenAI**
```bash
export OPENAI_API_KEY="your-openai-api-key"
```

**Option 2: DeepSeek**
```bash
export DEEPSEEK_API_KEY="your-deepseek-api-key"
```

**Option 3: Both providers**
```bash
export OPENAI_API_KEY="your-openai-api-key"
export DEEPSEEK_API_KEY="your-deepseek-api-key"
# When both are set, you must specify --ai-provider flag
```

### Provider Selection

The hook automatically selects the provider based on available API keys:

- **Only OPENAI_API_KEY set**: Uses OpenAI with o3 model
- **Only DEEPSEEK_API_KEY set**: Uses DeepSeek with deepseek-r1 model  
- **Both keys set**: Requires explicit `--ai-provider` flag

### Command Line Arguments

```bash
python -m sem_merge [options] [files...]

Options:
  --ai-provider {openai,deepseek}    Force specific AI provider
  --model MODEL                      Override default model for provider
  -h, --help                        Show help message
```

### Examples

```bash
# Auto-detect provider (single API key available)
python -m sem_merge README.md docs/

# Force OpenAI provider (when both keys available)
python -m sem_merge --ai-provider openai README.md

# Use custom model
python -m sem_merge --ai-provider openai --model gpt-4-turbo README.md

# DeepSeek with custom model
python -m sem_merge --ai-provider deepseek --model deepseek-chat README.md
```

## How It Works

1. **File Detection**: Scans staged documentation files in your commit
2. **Content Comparison**: Compares your local changes with the main branch
3. **AI Analysis**: Sends both versions to your configured AI provider with semantic merge instructions
4. **Intelligent Merging**: AI understands context and meaning to create a coherent merged document
5. **Seamless Integration**: Updates files in place, ready for commit

### Semantic vs Traditional Merging

**Traditional Git Merge:**
```diff
<<<<<<< HEAD
## Installation
Run `pip install mypackage` to install.
=======
## Setup
Use `pip install mypackage` for installation.
>>>>>>> main
```

**Semantic Merge Result:**
```markdown
## Installation
Run `pip install mypackage` to install the package.
```

## Requirements

- Python 3.9+
- Valid API key (OpenAI or DeepSeek)
- Git repository

## API Costs

Both providers offer competitive pricing:

- **DeepSeek R1**: ~$2.19 per million input tokens, ~$8.78 per million output tokens
- **OpenAI o3**: Pricing varies by model and usage tier

Documentation files are typically small, so costs are minimal for normal usage.

## Development

This project uses modern Python tooling:

```bash
# Install with development dependencies
pip install -e ".[dev]"

# Run tests
task test

# Format code  
task format

# Type checking
task typecheck

# Lint code
task lint
```

## Troubleshooting

### Common Issues

**Error: "No API key found"**
```bash
# Set the appropriate environment variable
export DEEPSEEK_API_KEY="your-key"  # or OPENAI_API_KEY
```

**Error: "Must specify --ai-provider"**
```bash
# When both API keys are present, be explicit:
git config --global sem-merge.provider "openai"  # or add to .pre-commit-hooks.yaml
```

**Hook fails but doesn't block commit**
```bash
# Check API key validity and network connection
curl -H "Authorization: Bearer $DEEPSEEK_API_KEY" https://api.deepseek.com/v1/models
```

## Breaking Changes in v1.1.0

- **Hard Failure**: Hook now fails if AI API calls fail (no more graceful degradation)
- **Multi-Provider Support**: Constructor and initialization changed significantly
- **Argument Structure**: New command-line argument parsing
- **Model Defaults**: OpenAI uses o3, DeepSeek uses deepseek-r1 by default

If upgrading from v1.0.x, review your configuration for any custom scripting.

## Contributing

Contributions welcome! Please ensure:

1. Tests pass: `task test`
2. Code is formatted: `task format` 
3. Types check: `task typecheck`
4. Linting passes: `task lint`

## License

MIT License - see [LICENSE](LICENSE) for details. 