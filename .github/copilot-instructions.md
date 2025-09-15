# GPM - Git Package Manager for Home Assistant

GPM is a Home Assistant custom integration that provides a Git-based package manager for custom_components and dashboard resources. Always reference these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.

## Working Effectively

### Environment Setup
- This project requires Python 3.13+ for development but runs on Python 3.12+ in production.
- The project is designed to run as a Home Assistant custom_component.
- Development is done using the provided VSCode devcontainer or manually with Home Assistant development setup.

### Quick Start (Limited Network Environment)
- Install only essential dependencies that work in constrained environments:
  - `pip install ruff` - for linting and formatting (takes 5-10 seconds)
  - `pip install pytest` - for basic testing framework (takes 10-15 seconds)
- Basic code validation without dependencies:
  - `python3 -m py_compile custom_components/gpm/*.py` - validates Python syntax
  - `python3 -m ruff check .` - lints code (takes <1 second)
  - `python3 -m ruff format . --check` - checks formatting (takes <1 second)
  - `./scripts/lint.sh` - runs linting and formatting (takes <1 second)

### Full Development Setup (Normal Network Environment)
- Run the setup script: `./scripts/setup.sh`
  - This installs the project in editable mode: `python3 -m pip install -e .`
  - **WARNING**: Installation requires Home Assistant dependencies which may fail due to network/firewall limitations
  - **EXPECTED TIME**: 2-5 minutes if successful, will fail with network timeouts in restricted environments
- **NEVER CANCEL** any pip install commands - they may take several minutes in slow network conditions

### Development Environment (VSCode DevContainer)
- Use the provided `.devcontainer.json` for a complete development environment
- The devcontainer includes Home Assistant and all required dependencies
- Port 8123 is forwarded for Home Assistant web interface
- Run `scripts/develop.sh` to start Home Assistant with debug configuration
  - Creates config directory if not present
  - Starts Home Assistant with `--debug` flag
  - **EXPECTED TIME**: 1-2 minutes startup time

## Testing and Validation

### Linting (ALWAYS WORKS)
- Run linting before any commit: `./scripts/lint.sh`
- Individual commands:
  - `python3 -m ruff format .` - auto-formats code (takes <1 second)
  - `python3 -m ruff check . --fix` - fixes linting issues (takes <1 second)
- **CRITICAL**: Always run `python3 -m ruff format . && python3 -m ruff check .` before committing or CI will fail

### Testing (Requires Full Dependencies)
- Run tests: `python3 -m pytest`
- **WARNING**: Tests require Home Assistant dependencies which may not be installable in restricted environments
- **EXPECTED TIME**: Tests take 5-10 seconds when dependencies are available
- **NEVER CANCEL** test runs - wait for completion
- Test files are in `tests/` directory and follow pytest conventions

### Manual Validation Scenarios
- **Basic Syntax Check**: `python3 -m py_compile custom_components/gpm/*.py` - ensures all Python files compile
- **Import Validation**: Test if modules can be imported (requires Home Assistant dependencies)
- **Integration Testing**: Install GPM in a Home Assistant instance using the installation script:
  ```bash
  wget -O - https://raw.githubusercontent.com/tomasbedrich/gpm/refs/heads/main/install/install.sh | bash -
  ```

## Key Project Structure

### Repository Root
```
.devcontainer.json      # VSCode development container config
.github/workflows/      # CI/CD pipelines (lint.yml, test.yml, validate.yml)
custom_components/gpm/  # Main integration code
config/                 # Development Home Assistant configuration
scripts/                # Build and development scripts
tests/                  # Test suite
pyproject.toml         # Python project configuration and dependencies
```

### Core Integration Files
- `custom_components/gpm/__init__.py` - Integration entry point
- `custom_components/gpm/_manager.py` - Core package management logic (25KB)
- `custom_components/gpm/config_flow.py` - Home Assistant configuration flow
- `custom_components/gpm/update.py` - Update entity implementation
- `custom_components/gpm/manifest.json` - Integration metadata

### Scripts Directory
- `scripts/setup.sh` - Installs project dependencies
- `scripts/lint.sh` - Runs ruff formatting and linting
- `scripts/develop.sh` - Starts Home Assistant development server

## Build and CI Information

### GitHub Actions Workflows
- **lint.yml**: Runs ruff formatting and linting checks (takes 1-2 minutes)
- **test.yml**: Runs pytest test suite (takes 2-3 minutes)
- **validate.yml**: Additional validation steps
- **NEVER CANCEL** CI workflows - they include dependency installation which can be slow

### Dependencies
- **Required for runtime**: GitPython~=3.1.43, Home Assistant>=2025.4.4
- **Required for development**: ruff==0.12.12, pytest-homeassistant-custom-component==0.13.278
- **Network issues**: pip install may fail due to firewall limitations or PyPI timeouts

## Common Tasks and Commands

### Before Making Changes
1. Run `python3 -m py_compile custom_components/gpm/*.py` to verify syntax
2. Run `./scripts/lint.sh` to check formatting and linting
3. Make your changes
4. Always run `./scripts/lint.sh` again before committing

### Working with Network Limitations
- If `pip install` fails with network timeouts, you can still:
  - Validate Python syntax with `python3 -m py_compile`
  - Use system-available tools for basic validation
  - Focus on code changes that don't require dependency installation
- Document any commands that fail due to network limitations as "fails due to firewall/network limitations"

### Installation and Usage
- GPM is installed as a Home Assistant custom_component
- Installation script automatically clones the repository and creates symlinks
- Users configure GPM through Home Assistant's integration interface
- GPM manages both custom_components and dashboard resources from Git repositories

## Validation Requirements
- **CRITICAL**: Always run linting (`./scripts/lint.sh`) before committing
- **SYNTAX**: Validate Python files compile: `python3 -m py_compile custom_components/gpm/*.py`
- **MANUAL**: Test end-to-end functionality in a Home Assistant instance when possible
- **CI**: All CI workflows must pass (lint, test, validate)

## Known Issues and Workarounds
- Home Assistant dependencies may not install in restricted network environments
- Use basic Python syntax validation and ruff linting for offline development
- pytest requires full dependency installation to run tests
- Development container provides complete isolated environment when network allows

## Quick Reference Commands
```bash
# Essential validation (always works)
python3 -m py_compile custom_components/gpm/*.py
python3 -m ruff check .
python3 -m ruff format . --check
./scripts/lint.sh

# Full development setup (may fail with network issues)
./scripts/setup.sh
python3 -m pytest
./scripts/develop.sh

# Manual installation for testing
wget -O - https://raw.githubusercontent.com/tomasbedrich/gpm/refs/heads/main/install/install.sh | bash -
```