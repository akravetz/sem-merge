# Project Brief: sem-merge Pre-commit Hook

## Project Overview
A pre-commit hook that automatically performs semantic merging of documentation files using DeepSeek R1 AI when triggered by git commits. The tool integrates seamlessly with the pre-commit framework ecosystem.

## Core Requirements

### Primary Functionality
- **Trigger Mechanism**: Activates automatically during git commits via pre-commit framework
- **File Detection**: Targets `.md` and `.mdc` files that differ from remote main branch
- **Semantic Merging**: Uses DeepSeek R1 API to intelligently merge local and remote versions
- **File Updates**: Updates staged files with merged content before commit proceeds

### Integration Requirements
- **Pre-commit Framework**: Must work as a standard pre-commit hook
- **Environment Configuration**: Uses `DEEPSEEK_API_KEY` environment variable
- **File Pattern Control**: Relies on pre-commit's `files` and `exclude` patterns for file selection
- **Fail-safe Operation**: Never blocks commits, gracefully handles API failures

### Quality Requirements
- **Modern Python Tooling**: Uses `uv`, `ruff`, `pyrefly`, and `Taskfile.yml`
- **Type Safety**: Comprehensive type annotations with pyrefly checking
- **Testing**: Unit tests and integration tests with real API calls
- **Documentation**: Complete README and development documentation

## Success Criteria
- Hook installs and runs via standard pre-commit workflow
- Produces semantically merged documentation that combines information from both versions
- Preserves document structure and eliminates duplicates
- Handles errors gracefully without blocking development workflow
- Passes all quality checks (linting, formatting, type checking, testing)

## Technical Constraints
- Must be compatible with pre-commit framework standards
- Requires DeepSeek API access for semantic merging
- Should work across different project types and documentation structures
- Must maintain performance with concurrent file processing

## Distribution Method
**Pre-commit Framework Integration Only**: Distributed as a standard pre-commit hook that users add to their `.pre-commit-config.yaml` files. 