# Contributing to Z22SE_Tuner

Thank you for your interest in contributing to Z22SE_Tuner! This document provides guidelines for contributing to the project.

## Table of Contents
- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Coding Standards](#coding-standards)
- [Submitting Changes](#submitting-changes)
- [Testing](#testing)

## Code of Conduct

This project adheres to a code of conduct that all contributors are expected to follow:

- Be respectful and inclusive
- Welcome newcomers and help them learn
- Focus on constructive criticism
- Respect differing viewpoints and experiences
- Accept responsibility for mistakes and learn from them

## How Can I Contribute?

### Reporting Bugs

Before submitting a bug report:
1. Check the [existing issues](https://github.com/zewy9910-ux/Z22SE_Tuner/issues) to avoid duplicates
2. Gather information about the bug:
   - ECU part number and calibration ID
   - Operating system and Python version
   - Steps to reproduce
   - Expected vs actual behavior
   - Error messages or logs (remove sensitive data like PIN codes)

Create a bug report with:
- **Title**: Clear, descriptive summary
- **Description**: Detailed steps to reproduce
- **Environment**: OS, Python version, PyQt6 version
- **Logs**: Relevant error messages or stack traces
- **Files**: Sample ECU files if relevant (anonymize sensitive data)

### Suggesting Enhancements

Enhancement suggestions are welcome! Please include:
- **Use case**: Why this feature would be useful
- **Proposed solution**: How you envision it working
- **Alternatives**: Other approaches you've considered
- **Examples**: Screenshots, mockups, or code snippets if applicable

### Pull Requests

We actively welcome pull requests for:
- Bug fixes
- Documentation improvements
- New features (discuss in an issue first for large changes)
- Code quality improvements
- Test coverage improvements

## Development Setup

### Prerequisites
- Python 3.8 or higher
- Git
- PyQt6 (automatically installed via requirements)

### Setup Steps

1. **Fork and Clone**
```bash
# First, fork the repository on GitHub using the "Fork" button
# Then clone your fork:
git clone https://github.com/YOUR-USERNAME/Z22SE_Tuner.git
cd Z22SE_Tuner
```

2. **Create Virtual Environment** (recommended)
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows
```

3. **Install Dependencies**
```bash
pip install -r requirements.txt
```

4. **Run the Application**
```bash
python Z22SE_Tuner.py
```

5. **Create a Branch**
```bash
git checkout -b feature/your-feature-name
# or
git checkout -b bugfix/issue-number-description
```

## Coding Standards

### Python Style
- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide
- Use 4 spaces for indentation (no tabs)
- Maximum line length: 100 characters (flexible for readability)
- Use descriptive variable names (`ignition_advance` not `ia`)

### Documentation
- Add docstrings to all functions and classes
```python
def apply_stage1(self):
    """
    Apply Stage 1 tune based on verified binary analysis.
    
    Modifications:
    - Ignition: +2 counts WOT, +1 count part-load
    - Fuel: +2 counts WOT, +1 count part-load
    - Lambda: -7 counts WOT (richer AFR target)
    - Trims: +1 count uniform
    """
```
- Update README.md if adding user-facing features
- Comment complex logic or non-obvious code

### Commit Messages
Follow conventional commit format:
```
type(scope): brief description

Detailed explanation if needed.

- Bullet points for multiple changes
- Reference issues: Fixes #123
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, no logic change)
- `refactor`: Code restructuring (no behavior change)
- `test`: Adding or updating tests
- `chore`: Build process, dependencies, etc.

**Examples:**
```
feat(tuning): add E85 ethanol tuning profile

Adds optimized ignition and fuel maps for E85 fuel,
including increased timing advance and lambda targets.

- Ignition: +8° WOT, +5° part-load
- Lambda: -20 counts (target 11.5:1 AFR)
- Rev limit: Unchanged

Closes #45
```

```
fix(gui): prevent crash when loading malformed bin files

Added file size validation and error handling to prevent
application crash when loading non-512KB files.

Fixes #67
```

## Submitting Changes

### Before Submitting
1. **Test your changes thoroughly**
   - Test with real ECU files (anonymize before sharing)
   - Verify no regressions in existing functionality
   - Check edge cases (corrupted files, invalid values, etc.)

2. **Update documentation**
   - README.md for user-facing changes
   - Code comments for implementation details
   - ECU_Mapping_Report.md for new table discoveries

3. **Follow coding standards**
   - Run linter if available
   - Format code consistently with existing style
   - Add docstrings and comments

4. **Create atomic commits**
   - One logical change per commit
   - Clear, descriptive commit messages
   - Squash work-in-progress commits if needed

### Pull Request Process

1. **Push your branch**
```bash
git push origin feature/your-feature-name
```

2. **Create Pull Request**
   - Go to GitHub and create a pull request
   - Fill out the PR template (description, testing, etc.)
   - Link related issues (Fixes #123, Relates to #456)

3. **PR Description Should Include:**
   - **What**: What does this PR do?
   - **Why**: Why is this change needed?
   - **How**: How does it work?
   - **Testing**: How was it tested?
   - **Screenshots**: For UI changes
   - **Breaking Changes**: Any compatibility issues

4. **Code Review**
   - Address reviewer feedback promptly
   - Push additional commits to the same branch
   - Discussion and iteration are expected and encouraged

5. **Merge**
   - Maintainers will merge once approved
   - Your contribution will be credited in release notes

## Testing

### Manual Testing Checklist
- [ ] Load stock ECU file (verify ECU info detection)
- [ ] Apply tuning profile (check change log)
- [ ] Save modified file (verify backup creation)
- [ ] Reset to original (verify changes are reverted)
- [ ] Test with multiple ECU variants (2001 vs 2004 calibrations from `sample_files/`)
- [ ] Test error handling (invalid files, wrong size, etc.)

### Test ECU Files
**Never commit real ECU files with sensitive data!**

When testing:
- Use sample files from the `sample_files/` directory for reference
- Use anonymized test files for testing
- Remove PIN codes, VIN numbers, calibration IDs from any new test files
- Create minimal test fixtures (e.g., 512KB of zeros with specific addresses populated)
- All sample binary files should be stored in `sample_files/` directory

### Repository Organization
- `sample_files/` - Contains all sample ECU binary files (.bin, .ori, .Original, .Stage*)
- Root directory - Python scripts, documentation, and configuration files
- Keep binary files organized in `sample_files/` to maintain clean repository structure

### Future: Automated Testing
We welcome contributions to add automated testing:
- Unit tests for TuneEngine methods
- Integration tests for file I/O
- GUI testing with PyQt Test framework
- Regression tests for known issues

## Additional Resources

- **ECU Mapping**: See [ECU_Mapping_Report.md](ECU_Mapping_Report.md) for detailed memory map
- **Analysis Tool**: [ecu_analysis.py](ecu_analysis.py) for binary diff analysis
- **PyQt6 Documentation**: [https://www.riverbankcomputing.com/static/Docs/PyQt6/](https://www.riverbankcomputing.com/static/Docs/PyQt6/)
- **GMPT-E15 Platform**: Research Delco/Delphi MPC5xx ECU architecture

## Questions?

- Open a [GitHub Discussion](https://github.com/zewy9910-ux/Z22SE_Tuner/discussions) for general questions
- Use [Issues](https://github.com/zewy9910-ux/Z22SE_Tuner/issues) for bugs and feature requests
- Check existing documentation in [README.md](README.md)

## Recognition

All contributors will be:
- Listed in release notes
- Credited in commit history
- Acknowledged in the project README (for significant contributions)

Thank you for contributing to Z22SE_Tuner! 🚀
