# Contributing to PEFT Studio

Thank you for your interest in contributing to PEFT Studio! We welcome contributions from the community.

## 🤝 How to Contribute

### Reporting Bugs

If you find a bug, please create an issue using the bug report template. Include:
- Clear description of the issue
- Steps to reproduce
- Expected vs actual behavior
- Your environment (OS, Node version, Python version)
- Screenshots if applicable

### Suggesting Features

We love new ideas! Create a feature request issue with:
- Clear description of the feature
- Use case and benefits
- Possible implementation approach (optional)

### Code Contributions

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**
   - Write clean, readable code
   - Follow existing code style
   - Add tests for new features
   - Update documentation

4. **Test your changes**
   ```bash
   # Frontend tests
   npm test
   npm run lint
   
   # Backend tests
   cd backend
   pytest
   ```

5. **Commit your changes**
   - Use clear, descriptive commit messages
   - Follow conventional commits format:
     - `feat: add new feature`
     - `fix: resolve bug`
     - `docs: update documentation`
     - `test: add tests`
     - `refactor: code improvements`

6. **Push and create a Pull Request**
   ```bash
   git push origin feature/your-feature-name
   ```

## 📋 Development Setup

### Prerequisites
- Node.js 18+ and npm
- Python 3.10+
- Git

### Setup Steps

1. Clone the repository
   ```bash
   git clone https://github.com/YOUR_USERNAME/peft-studio.git
   cd peft-studio
   ```

2. Install frontend dependencies
   ```bash
   npm install
   ```

3. Install backend dependencies
   ```bash
   cd backend
   pip install -r requirements.txt
   cd ..
   ```

4. Run development servers
   ```bash
   # Terminal 1 - Frontend
   npm run dev
   
   # Terminal 2 - Backend
   cd backend
   python main.py
   ```

## 🎨 Code Style

### TypeScript/React
- Use TypeScript for type safety
- Follow React best practices
- Use functional components with hooks
- Keep components small and focused
- Use meaningful variable names

### Python
- Follow PEP 8 style guide
- Use type hints
- Write docstrings for functions and classes
- Keep functions focused and testable

### General
- Write self-documenting code
- Add comments for complex logic
- Keep files under 500 lines when possible
- Use consistent naming conventions

## ✅ Pull Request Guidelines

### Before Submitting
- [ ] Code follows project style guidelines
- [ ] All tests pass
- [ ] New tests added for new features
- [ ] Documentation updated
- [ ] No console.log or debug statements
- [ ] Commit messages are clear

### PR Description
Include:
- What changes were made
- Why the changes were needed
- How to test the changes
- Screenshots (for UI changes)
- Related issue numbers

### Review Process
- Maintainers will review your PR
- Address any requested changes
- Once approved, your PR will be merged
- Your contribution will be credited

## 🧪 Testing

### Running Tests
```bash
# All frontend tests
npm test

# Watch mode
npm test -- --watch

# Coverage
npm test -- --coverage

# Backend tests
cd backend
pytest

# With coverage
pytest --cov=services
```

### Writing Tests
- Write unit tests for new functions
- Write integration tests for features
- Aim for good coverage, not 100%
- Test edge cases and error conditions

## 📚 Documentation

### Code Documentation
- Add JSDoc comments for TypeScript functions
- Add docstrings for Python functions
- Document complex algorithms
- Explain "why" not just "what"

### User Documentation
- Update README if needed
- Add to `/docs` for major features
- Include examples and screenshots
- Keep language clear and simple

## 🐛 Debugging

### Frontend
- Use React DevTools
- Check browser console
- Use debugger statements
- Check network tab for API calls

### Backend
- Use Python debugger (pdb)
- Check backend logs
- Test API endpoints with curl/Postman
- Verify database state

## 🔒 Security

- Never commit secrets or API keys
- Use environment variables for sensitive data
- Report security issues privately
- Follow secure coding practices

## 📞 Getting Help

- Check existing issues and discussions
- Read the documentation in `/docs`
- Ask questions in GitHub Discussions
- Be respectful and patient

## 🎯 Good First Issues

Look for issues labeled `good first issue` - these are great for newcomers!

## 📜 Code of Conduct

Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md).

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

> **Note**: Before publishing, replace `YOUR_USERNAME` with your actual GitHub username or organization name.

---

Thank you for contributing to PEFT Studio! 🚀
