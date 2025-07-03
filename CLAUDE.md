# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Testing
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_config_manager/test_tc0001_001_basic_operations.py

# Run with verbose output
pytest -v

# Run with short traceback
pytest --tb=short

# Run only unit tests
pytest tests/01_unit_tests/

# Run specific test pattern
pytest -k "test_tc0001"
```

### Python Environment
```bash
# Activate the required conda environment
source /home/tony/programs/miniconda3/etc/profile.d/conda.sh && conda activate base_python3.12

# Run simple test
conda run -n base_python3.12 python simple_test.py

# Run configuration collection
conda run -n base_python3.12 python collect.py

# Install dependencies
conda run -n base_python3.12 pip install -e .
```

### Linting and Code Quality
```bash
# Run ruff linting (preferred over flake8)
conda run -n base_python3.12 ruff check src/ tests/

# Auto-fix ruff issues
conda run -n base_python3.12 ruff check --fix src/ tests/

# Format code with ruff
conda run -n base_python3.12 ruff format src/ tests/
```

## Project Architecture

### Core Components
- **ConfigManager**: Main singleton configuration manager class (production mode), supports multi-instance in test mode
- **ConfigManagerCore**: Core implementation inheriting from ConfigNode, provides all configuration management features
- **ConfigNode**: Base configuration node class with dynamic debug_mode support
- **PathResolver**: Handles path resolution and project root detection
- **FileOperations**: Manages YAML file operations using ruamel.yaml for comment preservation
- **AutosaveManager**: Handles threaded automatic configuration saving
- **CallChainTracker**: Tracks method call chains for debugging (retained feature)
- **TestEnvironmentManager**: Manages test mode isolation and path replacement

### Key Design Patterns
- **Global Singleton**: Single instance in production, multi-instance in test mode
- **Thread Safety**: All operations are thread-safe with proper locking
- **Auto Persistence**: Configuration changes are automatically saved
- **Type Safety**: Complete type hints throughout the codebase
- **Cross Platform**: Supports Windows and Ubuntu (reduced from broader OS support)

### Directory Structure
- `src/config_manager/`: Main package source code
- `src/config_manager/core/`: Core implementation modules
- `src/config_manager/logger/`: Minimal logging implementation
- `src/config/`: Configuration files (config.yaml, backups)
- `tests/`: Test suite with 01_unit_tests/ and integration tests
- `docs/`: Requirements, architecture and design documentation
- `temp/`: Temporary files (must be cleaned after use)

## Configuration Management

### Usage Patterns
```python
# Get configuration manager (auto-setup enabled)
from config_manager import get_config_manager
config = get_config_manager()

# Test mode usage
config = get_config_manager(test_mode=True)

# Access configuration via attributes (no default values)
value = config.some_setting  # Will raise AttributeError if not set
```

### Path Handling
- Only `base_dir` supports automatic single-path to multi-platform configuration conversion
- Fields ending with `_dir` automatically create directories
- Test mode replaces `base_dir` with temporary directory for isolation
- Use `setup_project_paths()` for path configuration initialization

## Development Guidelines

### Code Standards
- Use 4 spaces for indentation
- Function names use snake_case, class names use PascalCase
- Prefer ruamel.yaml over pyyaml for YAML comment preservation
- Test files must start with `test_`
- Use relative imports within the package
- Files/variables should not contain 'test' except in test cases (to avoid pytest conflicts)
- Path handling: use `os.path` or `pathlib` for cross-platform compatibility

### Testing Requirements
- All tests must pass before committing
- Test environments use `test_mode=True` parameter
- Test files should be isolated in temp/ directory
- Clean up temporary files after use
- Use `conftest.py` for shared test configuration
- **Critical**: Always run tests with conda environment activated:
  ```bash
  source /home/tony/programs/miniconda3/etc/profile.d/conda.sh && conda activate base_python3.12 && pytest
  ```

### Function Definition Standards
- All functions must have explicit `return` statements or `pass` statements
- All functions must have explicit type signatures
- Only return single variables, multiple variables, or empty `return` - no expressions
- Single main return path in primary logic flow
- Instance methods not using `self` should be converted to static methods

### Documentation Updates
After code changes, update relevant documentation:
- Requirements documents in `docs/01_requirements/`
- Architecture design in `docs/02_architecture/`
- Design documents in `docs/03_design/`
- Delete outdated descriptions to match current implementation

### Error Handling
- No try-except for unexpected errors (error transparency)
- No fallback or degradation logic
- No default values for attribute access (natural error propagation)

## Important Notes

### Multiprocessing Support
- Use `SerializableConfigData` and `create_serializable_config()` for multiprocessing scenarios
- Configuration data can be serialized and shared between processes

### Test Mode Features
- Isolated instances prevent test interference
- Automatic path replacement to temporary directories
- Retains CallChainTracker functionality for debugging
- Automatic directory creation for `_dir` fields

### Platform Support
- Only supports Windows 10 and Ubuntu Linux (reduced scope)
- Uses `CrossPlatformPath` for cross-platform path handling
- Automatic platform-specific path conversion

### Environment Configuration
**Critical**: This project requires conda environment `base_python3.12`:
```bash
# Always activate environment before running Python commands
source /home/tony/programs/miniconda3/etc/profile.d/conda.sh && conda activate base_python3.12

# Or use conda run for single commands
conda run -n base_python3.12 python your_script.py
```

### Git Configuration
- Use email `Tony.xiao@gmail.com` for commits
- Do not use "claude code" related terms in commit messages
- Follow conventional commit format for consistency

### Key API Usage
```python
# Main application (must provide first_start_time)
from datetime import datetime
from config_manager import get_config_manager

start_time = datetime.now()
config = get_config_manager(first_start_time=start_time)

# Library/module usage (no first_start_time needed)
config = get_config_manager()

# Test mode usage
config = get_config_manager(test_mode=True)
```

### File Naming Conventions
- Test files: `test_tc{4digits}_{3digits}_{description}.py`
- Source files: Use descriptive names, avoid 'test' in non-test files
- Maximum line length: 120 characters
- File size limit: 300 lines (split if exceeded)