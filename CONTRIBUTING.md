# Contributing to PEFT Studio

Thank you for your interest in contributing to PEFT Studio! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Contribution Workflow](#contribution-workflow)
- [Code Style Guidelines](#code-style-guidelines)
- [Testing Requirements](#testing-requirements)
- [Commit Message Conventions](#commit-message-conventions)
- [Pull Request Process](#pull-request-process)
- [Reporting Bugs](#reporting-bugs)
- [Suggesting Features](#suggesting-features)

## Code of Conduct

This project adheres to a Code of Conduct that all contributors are expected to follow. Please read [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before contributing.

## Getting Started

### Prerequisites

Before you begin, ensure you have the following installed:

- **Node.js** 18 or higher
- **Python** 3.10 or higher
- **Git** for version control
- **CUDA GPU** (recommended for testing training features)

### Development Setup

1. **Fork the repository** on GitHub

2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/peft-studio.git
   cd peft-studio
   ```

3. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/Ankesh-007/peft-studio.git
   ```

4. **Install frontend dependencies**:
   ```bash
   npm install
   ```

5. **Set up Python environment**:
   ```bash
   python -m venv peft_env
   
   # Windows
   peft_env\Scripts\activate
   
   # macOS/Linux
   source peft_env/bin/activate
   
   pip install -r backend/requirements.txt
   ```

6. **Run the development servers**:
   ```bash
   # Terminal 1: Frontend development server
   npm run dev
   
   # Terminal 2: Electron application
   npm run electron:dev
   ```

## Contribution Workflow

1. **Create a new branch** for your work:
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```

2. **Make your changes** following the code style guidelines

3. **Test your changes** thoroughly:
   ```bash
   # Run frontend tests
   npm test
   
   # Run backend tests
   cd backend
   pytest
   ```

4. **Commit your changes** using conventional commit messages

5. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create a Pull Request** on GitHub

## Code Style Guidelines

### TypeScript/React (Frontend)

- **Linting**: We use ESLint for code quality
  ```bash
  npm run lint
  ```

- **Formatting**: We use Prettier for code formatting
  ```bash
  npm run format:check  # Check formatting
  npm run format        # Auto-fix formatting
  ```

- **Style Rules**:
  - Use functional components with hooks
  - Use TypeScript for type safety
  - Follow React best practices (avoid inline functions in JSX, use proper key props)
  - Use Tailwind CSS for styling (avoid inline styles)
  - Keep components small and focused
  - Use meaningful variable and function names

- **File Organization**:
  - Components go in `src/components/`
  - Utilities go in `src/lib/`
  - API clients go in `src/api/`
  - Types go in `src/types/`

### Python (Backend)

- **Linting**: We use flake8 for linting
  ```bash
  cd backend
  flake8 .
  ```

- **Formatting**: We use black for code formatting
  ```bash
  cd backend
  black --check .  # Check formatting
  black .          # Auto-fix formatting
  ```

- **Style Rules**:
  - Follow PEP 8 style guide
  - Use type hints for function parameters and return values
  - Write docstrings for all public functions and classes
  - Keep functions small and focused
  - Use meaningful variable and function names

- **File Organization**:
  - Services go in `backend/services/`
  - Tests go in `backend/tests/`
  - Database models in `backend/database.py`
  - Configuration in `backend/config.py`

## Testing Requirements

All contributions must include appropriate tests:

### Frontend Tests

- **Unit Tests**: Test individual components and utilities
- **Integration Tests**: Test component interactions
- **Property-Based Tests**: Use fast-check for complex logic

Run tests:
```bash
npm test              # Run all tests once
npm run test:watch    # Run tests in watch mode
```

### Backend Tests

- **Unit Tests**: Test individual functions and classes
- **Integration Tests**: Test API endpoints
- **Property-Based Tests**: Use Hypothesis for complex logic

Run tests:
```bash
cd backend
pytest                    # Run all tests
pytest -v                 # Verbose output
pytest --cov              # With coverage report
```

### Test Coverage

- Aim for at least 80% code coverage for new code
- All bug fixes should include a test that would have caught the bug
- All new features should include comprehensive tests

## Commit Message Conventions

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- **feat**: A new feature
- **fix**: A bug fix
- **docs**: Documentation changes
- **style**: Code style changes (formatting, missing semicolons, etc.)
- **refactor**: Code refactoring without changing functionality
- **perf**: Performance improvements
- **test**: Adding or updating tests
- **chore**: Maintenance tasks (dependencies, build config, etc.)

### Examples

```
feat(training): add support for QLoRA fine-tuning

Implement QLoRA training method with 4-bit quantization support.
Includes UI components and backend integration.

Closes #123
```

```
fix(dashboard): correct memory usage calculation

The memory usage was incorrectly calculated due to unit conversion error.
Now properly converts bytes to GB.

Fixes #456
```

```
docs(readme): update installation instructions

Add troubleshooting section for common installation issues.
```

### Scope

Common scopes include:
- `training`: Training-related features
- `dashboard`: Dashboard components
- `dataset`: Dataset management
- `model`: Model browser and management
- `inference`: Inference playground
- `ui`: General UI components
- `backend`: Backend services
- `config`: Configuration
- `build`: Build system
- `deps`: Dependencies

## Pull Request Process

1. **Update documentation** if you're changing functionality

2. **Add tests** for new features or bug fixes

3. **Ensure all tests pass**:
   ```bash
   npm test
   cd backend && pytest
   ```

4. **Update CHANGELOG.md** if applicable

5. **Fill out the PR template** completely

6. **Request review** from maintainers

7. **Address review feedback** promptly

8. **Squash commits** if requested before merging

### PR Title Format

Use the same format as commit messages:
```
feat(scope): brief description
```

### PR Description

Include:
- **What**: What changes does this PR introduce?
- **Why**: Why are these changes needed?
- **How**: How were the changes implemented?
- **Testing**: How were the changes tested?
- **Screenshots**: For UI changes, include before/after screenshots
- **Breaking Changes**: List any breaking changes
- **Related Issues**: Link to related issues

## Reporting Bugs

Before creating a bug report:

1. **Check existing issues** to avoid duplicates
2. **Verify the bug** in the latest version
3. **Collect information**:
   - Operating system and version
   - Node.js and Python versions
   - Steps to reproduce
   - Expected vs actual behavior
   - Error messages and stack traces
   - Screenshots if applicable

Create a bug report using the [bug report template](.github/ISSUE_TEMPLATE/bug_report.md).

## Suggesting Features

Before suggesting a feature:

1. **Check existing issues** and discussions
2. **Consider the scope**: Does it fit the project's goals?
3. **Think about implementation**: Is it technically feasible?

Create a feature request using the [feature request template](.github/ISSUE_TEMPLATE/feature_request.md).

## Questions?

- **GitHub Discussions**: For general questions and discussions
- **GitHub Issues**: For bug reports and feature requests
- **Documentation**: Check the [docs](docs/) directory

## License

By contributing to PEFT Studio, you agree that your contributions will be licensed under the MIT License.

## Recognition

Contributors will be recognized in:
- The project README
- Release notes
- The contributors page on GitHub

Thank you for contributing to PEFT Studio! 🎉
