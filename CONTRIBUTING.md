# Contributing

Thank you for your interest in contributing to Planning Drawing Validator!

## Quick Start

1. **Fork and clone** the repository
2. **Set up environment**:
   ```bash
   uv venv .venv && source .venv/bin/activate
   uv pip install -e "planning-drawing-validator[dev]"
   pre-commit install
   ```
3. **Create a branch**: `git checkout -b feature/your-feature`
4. **Make changes**
5. **Submit a pull request**

## Code Style

- **Python**: Ruff formatting, type hints, Google-style docstrings
- Run `ruff check . && ruff format .` before committing

## Pull Request Guidelines

- Keep PRs focused on a single change
- Update documentation as needed
- Use conventional commits: `feat:`, `fix:`, `docs:`, `chore:`

## Reporting Issues

- Check existing issues first
- Provide clear reproduction steps
- Include environment details (OS, Python version)

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
