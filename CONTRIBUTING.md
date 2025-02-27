# Contributing to PhotoMeta Restore

Thank you for your interest in contributing to PhotoMeta Restore! This document provides guidelines and instructions for contributing to this project.

## Code of Conduct

By participating in this project, you agree to abide by a respectful and collaborative environment. Please be kind and courteous to others, and respect differing viewpoints and experiences.

## How Can I Contribute?

### Reporting Bugs

- Use the bug report template when creating an issue
- Check if the bug has already been reported
- Include detailed steps to reproduce the bug
- Mention your environment (OS, Python version, etc.)
- Include any relevant logs or screenshots

### Suggesting Features

- Use the feature request template when creating an issue
- Clearly describe the feature and the problem it solves
- Consider whether your idea fits within the scope of the project

### Pull Requests

1. Fork the repository
2. Create a new branch (`git checkout -b feature/my-feature`)
3. Make your changes
4. Add tests if applicable
5. Run existing tests to ensure nothing broke
6. Commit your changes (`git commit -m 'Add some feature'`)
7. Push to the branch (`git push origin feature/my-feature`)
8. Create a Pull Request using our template

## Development Setup

1. Clone the repository
   ```bash
   git clone https://github.com/axatjpr/photometa-restore.git
   cd photometa-restore
   ```

2. Install development dependencies
   ```bash
   pip install -r requirements.txt
   pip install -e .
   ```

3. Run the application
   ```bash
   python run.py
   ```

## Style Guidelines

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide
- Use descriptive variable names
- Add docstrings to all functions and classes
- Keep lines under 100 characters where possible
- Use 4 spaces for indentation (no tabs)

## Testing

- Add tests for new features
- Ensure all tests pass before submitting a pull request
- Run tests using:
  ```bash
  python -m unittest discover tests
  ```

## Documentation

- Update the README.md if your changes affect the user experience
- Add or update docstrings for any modified code
- Comment complex code sections

## License

By contributing, you agree that your contributions will be licensed under the same [MIT License](LICENSE) that covers the project.

## Questions?

If you have any questions or need help, feel free to reach out by creating an issue. 