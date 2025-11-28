# GitHub Actions Workflows

This directory contains CI/CD workflows for the Planning Drawing Validator project.

## Workflows Overview

### 1. `code-quality.yml` - Linting and Type Checking

**Triggers**: Push to main/develop, Pull Requests

**Jobs**:
- **lint-and-format**: Ruff linting and formatting checks
  - Checks all three packages
  - Format verification with `ruff format --check`
  - Linting with `ruff check`
- **type-check**: MyPy strict type checking
  - Runs `verify-mypy.sh` script
  - Ensures 0 type errors across all packages
- **frontend-quality**: Frontend code quality
  - ESLint, TypeScript checking, Prettier

**All checks must pass for PRs to be merged**

### 2. `security.yml` - Security Scanning

**Triggers**: Push to main/develop, Pull Requests, Weekly schedule (Monday 9am UTC)

**Jobs**:
- **secret-scanning**: Detect secrets with detect-secrets
- **python-security**: Python security vulnerabilities
  - Bandit for code analysis
  - Safety for dependency vulnerability checking
- **npm-audit**: NPM security audit for frontend dependencies

**Notes**: Some checks use `continue-on-error` to avoid blocking PRs on false positives

### 3. `docs.yml` - Documentation Checks

**Triggers**: Push to main, Pull Requests to main

**Jobs**:
- **check-docs**: Verify all required documentation files exist
  - READMEs for all packages
  - CONTRIBUTING.md, LICENSE, SECURITY.md
  - Example directories with valid Python syntax
- **check-links**: Validate markdown links (uses markdown-link-check)
- **build-docs**: Future Sphinx/MkDocs integration (placeholder)
- **check-docstrings**: Verify docstring coverage with pydocstyle

### 4. `release.yml` - Release Automation

**Triggers**: Git tags matching `v*.*.*` (e.g., v1.0.0)

**Jobs**:
- **build-and-publish**: Build and publish to PyPI
  - Builds Python packages with `build`
  - Publishes to PyPI (requires `PYPI_API_TOKEN` secret)
  - Creates GitHub Release
  - Attaches `.tar.gz` and `.whl` files

**Required Secrets**:
- `PYPI_API_TOKEN`: PyPI publishing token
- `TEST_PYPI_API_TOKEN`: Test PyPI token (optional, for testing releases)

### 5. `pr-checks.yml` - Pull Request Quality Checks

**Triggers**: Pull request opened, synchronized, reopened

**Jobs**:
- **pr-title-check**: Enforce conventional commit format
  - Types: feat, fix, docs, style, refactor, perf, build, ci, chore
- **pr-size-check**: Warn on large PRs (>1000 lines changed)
- **auto-assign-reviewers**: Auto-assign reviewers to PRs
- **labeler**: Auto-label PRs based on file changes
- **comment-on-first-pr**: Welcome first-time contributors
- **check-breaking-changes**: Detect potential breaking changes

## Workflow Dependencies

```
code-quality.yml
├── Requires: UV, Python 3.12, Node.js 18
├── Services: None
└── Secrets: None

security.yml
├── Requires: Python 3.11, Node.js 20
├── Services: None
└── Secrets: None

docs.yml
├── Requires: Python 3.12
├── Services: None
└── Secrets: None

release.yml
├── Requires: UV, Python 3.12
├── Services: None
└── Secrets: PYPI_API_TOKEN

pr-checks.yml
├── Requires: None
├── Services: None
└── Secrets: GITHUB_TOKEN (auto-provided)
```

## Status Badges

Add these to your README.md:

```markdown
[![Code Quality](https://github.com/i-dot-ai/planning-drawing-validator/workflows/Code%20Quality/badge.svg)](https://github.com/i-dot-ai/planning-drawing-validator/actions/workflows/code-quality.yml)
[![Security](https://github.com/i-dot-ai/planning-drawing-validator/workflows/Security/badge.svg)](https://github.com/i-dot-ai/planning-drawing-validator/actions/workflows/security.yml)
```

## Required Secrets Configuration

To enable all workflows, configure these secrets in your GitHub repository settings:

### PyPI Publishing
1. Go to https://pypi.org/manage/account/token/
2. Create a new API token
3. Add to GitHub Secrets as `PYPI_API_TOKEN`

## Local Testing

Test workflows locally with [act](https://github.com/nektos/act):

```bash
# Install act
brew install act  # macOS
# or
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash  # Linux

# Test specific workflow
act -W .github/workflows/code-quality.yml

# Test PR checks
act pull_request -W .github/workflows/pr-checks.yml

# List available workflows
act -l
```

## Maintenance

### Updating Dependencies

Workflows use specific action versions. Update regularly:

```bash
# Check for outdated actions
gh api repos/:owner/:repo/actions/workflows | jq '.workflows[].path'

# Update action versions in all workflow files
# actions/checkout@v4 → latest
# actions/setup-python@v5 → latest
# astral-sh/setup-uv@v3 → latest
```

### Monitoring Workflow Runs

```bash
# View recent workflow runs
gh run list

# View specific run details
gh run view <run-id>

# View workflow logs
gh run view <run-id> --log

# Re-run failed jobs
gh run rerun <run-id> --failed
```

## Troubleshooting

### Type Checking Failures

```bash
# Run mypy verification locally
./verify-mypy.sh

# Should show 0 errors (all packages passing strict mode)
```

### Security Scan False Positives

```bash
# Update bandit configuration in pyproject.toml
[tool.bandit]
exclude_dirs = [".venv"]
skips = ["B101"]  # Skip specific check

# Update safety ignore list
safety check --ignore 51668  # Ignore specific CVE
```

### Release Workflow Issues

```bash
# Test release locally
python -m build
twine check dist/*

# Upload to Test PyPI first
twine upload --repository testpypi dist/*
```

## Best Practices

1. **Keep workflows fast** - use caching, matrix builds
2. **Use secrets** for sensitive data (API keys, tokens)
3. **Monitor workflow costs** - GitHub Actions minutes are limited
4. **Update actions regularly** - security and features
5. **Use pull requests** for workflow changes

## Future Enhancements

- [ ] Add performance benchmarking workflow
- [ ] Set up automated dependency updates (Dependabot)
- [ ] Add Lighthouse CI for frontend performance
- [ ] Set up automated security advisories
- [ ] Set up automated API documentation deployment
