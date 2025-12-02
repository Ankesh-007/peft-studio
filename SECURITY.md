# Security Policy

## Supported Versions

We release patches for security vulnerabilities in the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take the security of PEFT Studio seriously. If you believe you have found a security vulnerability, please report it to us as described below.

### Where to Report

**Please do NOT report security vulnerabilities through public GitHub issues.**

Instead, please report them via email to: [INSERT SECURITY EMAIL]

You should receive a response within 48 hours. If for some reason you do not, please follow up via email to ensure we received your original message.

### What to Include

Please include the following information in your report:

- **Type of vulnerability** (e.g., buffer overflow, SQL injection, cross-site scripting, etc.)
- **Full paths of source file(s)** related to the manifestation of the vulnerability
- **Location of the affected source code** (tag/branch/commit or direct URL)
- **Step-by-step instructions** to reproduce the issue
- **Proof-of-concept or exploit code** (if possible)
- **Impact of the vulnerability**, including how an attacker might exploit it

This information will help us triage your report more quickly.

### What to Expect

After you submit a report, we will:

1. **Acknowledge receipt** of your vulnerability report within 48 hours
2. **Confirm the vulnerability** and determine its impact
3. **Work on a fix** and prepare a security advisory
4. **Release a patch** as soon as possible
5. **Publicly disclose the vulnerability** after the patch is released

### Disclosure Policy

- We will coordinate with you on the disclosure timeline
- We prefer to fully disclose vulnerabilities as soon as a fix is available
- We will credit you in the security advisory (unless you prefer to remain anonymous)

## Security Best Practices

When using PEFT Studio, we recommend following these security best practices:

### For Users

1. **Keep Software Updated**
   - Always use the latest version of PEFT Studio
   - Regularly update dependencies and system packages
   - Enable automatic updates when possible

2. **Protect Credentials**
   - Never commit API keys, tokens, or credentials to version control
   - Use environment variables for sensitive configuration
   - Rotate credentials regularly

3. **Secure Your Environment**
   - Use strong passwords for system accounts
   - Enable firewall protection
   - Keep your operating system and drivers updated

4. **Data Protection**
   - Be cautious with sensitive training data
   - Understand data privacy implications when using cloud services
   - Regularly backup important data

5. **Network Security**
   - Use secure networks when downloading models or datasets
   - Be cautious when connecting to external services
   - Verify SSL/TLS certificates

### For Developers

1. **Code Security**
   - Follow secure coding practices
   - Validate and sanitize all user inputs
   - Use parameterized queries to prevent SQL injection
   - Avoid using `eval()` or similar dangerous functions

2. **Dependency Management**
   - Regularly audit dependencies for vulnerabilities
   - Use `npm audit` and `pip-audit` to check for known issues
   - Keep dependencies up to date
   - Review dependency licenses for compatibility

3. **Authentication & Authorization**
   - Implement proper authentication mechanisms
   - Use principle of least privilege
   - Validate user permissions before operations

4. **Data Handling**
   - Encrypt sensitive data at rest and in transit
   - Implement proper error handling (don't leak sensitive info)
   - Sanitize logs to remove sensitive information

5. **Testing**
   - Include security tests in your test suite
   - Test for common vulnerabilities (XSS, CSRF, injection attacks)
   - Use static analysis tools to detect security issues

## Known Security Considerations

### Electron Security

PEFT Studio is built with Electron. We follow Electron security best practices:

- **Context Isolation**: Enabled to prevent renderer process from accessing Node.js APIs
- **Node Integration**: Disabled in renderer processes
- **Remote Module**: Disabled to prevent remote code execution
- **Content Security Policy**: Implemented to prevent XSS attacks
- **Secure IPC**: All IPC communication is validated and sanitized

### Python Backend Security

The Python backend follows these security practices:

- **Input Validation**: All API inputs are validated and sanitized
- **SQL Injection Prevention**: Using SQLAlchemy ORM with parameterized queries
- **CORS Configuration**: Properly configured to prevent unauthorized access
- **Rate Limiting**: Implemented to prevent abuse
- **Error Handling**: Errors don't expose sensitive system information

### Model and Dataset Security

When working with models and datasets:

- **Verify Sources**: Only download models from trusted sources (HuggingFace, etc.)
- **Scan Files**: Be cautious with user-uploaded datasets
- **Sandboxing**: Training runs are isolated from system resources
- **Resource Limits**: Memory and compute limits prevent resource exhaustion

## Security Updates

Security updates will be released as soon as possible after a vulnerability is confirmed. Updates will be announced through:

- GitHub Security Advisories
- Release notes
- Project README

## Compliance

PEFT Studio aims to comply with:

- OWASP Top 10 security risks
- CWE/SANS Top 25 Most Dangerous Software Errors
- Electron Security Guidelines
- Python Security Best Practices

## Security Tools

We use the following tools to maintain security:

- **npm audit**: For Node.js dependency vulnerabilities
- **pip-audit**: For Python dependency vulnerabilities
- **ESLint**: For JavaScript/TypeScript code quality and security
- **Bandit**: For Python security linting
- **GitHub Dependabot**: For automated dependency updates
- **GitHub Code Scanning**: For automated security analysis

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Electron Security Guidelines](https://www.electronjs.org/docs/latest/tutorial/security)
- [Python Security Best Practices](https://python.readthedocs.io/en/stable/library/security_warnings.html)
- [Node.js Security Best Practices](https://nodejs.org/en/docs/guides/security/)

## Questions?

If you have questions about security that are not covered in this document, please open a GitHub Discussion or contact us at [INSERT CONTACT EMAIL].

Thank you for helping keep PEFT Studio and its users safe!
