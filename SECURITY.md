# Security Policy

## Supported Versions

We release patches for security vulnerabilities. Currently supported versions:

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability, please follow these steps:

### 1. Do Not Open a Public Issue

Please **do not** open a public GitHub issue for security vulnerabilities.

### 2. Report Privately

Send a detailed report to the project maintainers via:
- GitHub Security Advisories (preferred)
- Email to the maintainers (check GitHub profile)

### 3. Include Details

Your report should include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)
- Your contact information

### 4. Response Timeline

- **24 hours**: Initial acknowledgment
- **7 days**: Detailed response with assessment
- **30 days**: Fix released (for confirmed vulnerabilities)

## Security Best Practices

### For Users

1. **Keep Software Updated**
   - Always use the latest version
   - Enable auto-updates when available

2. **Protect Credentials**
   - Never share API keys or tokens
   - Use environment variables for secrets
   - Rotate credentials regularly

3. **Secure Your Environment**
   - Use strong passwords
   - Enable 2FA on connected services
   - Keep your OS and dependencies updated

### For Contributors

1. **Code Security**
   - Never commit secrets or credentials
   - Use `.env` files for sensitive data
   - Validate all user inputs
   - Sanitize data before database operations

2. **Dependencies**
   - Keep dependencies updated
   - Review security advisories
   - Use `npm audit` and `pip-audit`
   - Avoid packages with known vulnerabilities

3. **Authentication**
   - Use secure authentication methods
   - Implement proper session management
   - Follow OAuth best practices
   - Hash and salt passwords

## Known Security Considerations

### API Keys and Credentials

This application handles API keys for various services. Users should:
- Store keys securely in environment variables
- Never commit keys to version control
- Use read-only keys when possible
- Rotate keys if compromised

### Data Storage

- Local database files may contain sensitive information
- Ensure proper file permissions
- Consider encryption for sensitive data
- Regular backups with secure storage

### Network Security

- API calls should use HTTPS
- Validate SSL certificates
- Implement rate limiting
- Use secure WebSocket connections

## Security Updates

Security updates will be released as:
- Patch versions for minor issues
- Minor versions for moderate issues
- Immediate hotfixes for critical issues

Subscribe to releases to stay informed.

## Acknowledgments

We appreciate security researchers who responsibly disclose vulnerabilities. Contributors will be acknowledged (with permission) in:
- Release notes
- Security advisories
- Project documentation

## Questions?

For general security questions (not vulnerabilities), please:
- Open a GitHub Discussion
- Check existing documentation
- Contact maintainers

---

Thank you for helping keep PEFT Studio secure! 🔒
