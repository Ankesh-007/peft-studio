# PEFT Studio Documentation

Welcome to PEFT Studio - a unified desktop platform for the complete LLM fine-tuning workflow.

## Quick Navigation

| I want to... | Go to... |
|--------------|----------|
| Get started quickly | [Quick Start Guide](user-guide/quick-start.md) |
| Configure my first training run | [Training Configuration](user-guide/training-configuration.md) |
| Connect to cloud platforms | [Platform Connections](user-guide/platform-connections.md) |
| Browse available models | [Model Browser](user-guide/model-browser.md) |
| Deploy my fine-tuned model | [Deployment Management](user-guide/deployment.md) |
| Develop a custom connector | [Connector Development](developer-guide/connector-development.md) |
| Understand the API | [API Documentation](developer-guide/api-documentation.md) |
| Build from source | [Build and Installers](developer-guide/build-and-installers.md) |
| Troubleshoot issues | [Troubleshooting Guide](reference/troubleshooting.md) |
| Contribute to the project | [Contributing Guidelines](CONTRIBUTING.md) |

---

## Documentation Index

### 📚 User Guides

**Getting Started**
- [Quick Start Guide](user-guide/quick-start.md) - Get up and running in minutes
- [Platform Connections](user-guide/platform-connections.md) - Connect to cloud platforms and compute providers
- [Compute Provider Selection](user-guide/compute-providers.md) - Choose the right compute for your workload

**Model Management**
- [Model Browser](user-guide/model-browser.md) - Browse and select models from multiple sources
- [Training Configuration](user-guide/training-configuration.md) - Configure PEFT training parameters
- [Configuration Management](user-guide/configuration-management.md) - Import, export, and manage training configurations

**Training & Deployment**
- [Deployment Management](user-guide/deployment.md) - Deploy models to production endpoints
- [Inference Playground](user-guide/inference-playground.md) - Test and validate your fine-tuned models
- [Gradio Demo Generator](user-guide/gradio-demo.md) - Create interactive demos for your models

**Monitoring & Diagnostics**
- [Logging and Diagnostics](user-guide/logging-diagnostics.md) - Monitor training runs and diagnose issues

---

### 🔧 Developer Guides

**Core Development**
- [API Documentation](developer-guide/api-documentation.md) - Complete API reference
- [Connector Development Guide](developer-guide/connector-development.md) - Build custom platform connectors
- [Contributing Guidelines](CONTRIBUTING.md) - How to contribute to PEFT Studio

**Build & Deployment**
- [Build and Installers](developer-guide/build-and-installers.md) - Build desktop installers for all platforms
- [CI/CD Setup](developer-guide/ci-cd-setup.md) - Continuous integration and deployment configuration
- [Auto-Update System](developer-guide/auto-update-system.md) - Automatic update mechanism

**Backend Services**
- [Training Orchestrator](developer-guide/training-orchestrator.md) - Multi-provider training orchestration
- [Cost Calculator](developer-guide/cost-calculator.md) - Training cost estimation service
- [Export System](developer-guide/export-system.md) - Model export to various formats
- [Credential Management](developer-guide/credential-management.md) - Secure credential storage
- [Multi-Run Management](developer-guide/multi-run-management.md) - Parallel training run management
- [Paused Run Management](developer-guide/paused-run-management.md) - Resume interrupted training runs
- [Notification System](developer-guide/notification-system.md) - User notification service
- [Gradio Generator](developer-guide/gradio-generator.md) - Gradio demo generation service

**Platform Integration**
- [Cloud Platforms](developer-guide/cloud-platforms.md) - Cloud platform integration architecture
- [Platform Connections](developer-guide/platform-connections.md) - Platform connection management
- [WandB Integration](developer-guide/wandb-integration.md) - Weights & Biases experiment tracking

**System Architecture**
- [Performance Optimization](developer-guide/performance-optimization.md) - Performance tuning and optimization
- [Security](developer-guide/security.md) - Security best practices and implementation
- [Telemetry](developer-guide/telemetry.md) - Usage analytics and telemetry system
- [Testing](developer-guide/testing.md) - Testing strategy and guidelines

---

### 📖 Reference

- [Error Handling](reference/error-handling.md) - Error codes and handling strategies
- [FAQ](reference/faq.md) - Frequently asked questions
- [Troubleshooting Guide](reference/troubleshooting.md) - Common issues and solutions

---

### 🎥 Video Tutorials

- [Video Tutorial Index](video-tutorials/index.md) - Video walkthroughs and demonstrations

---

## Documentation Structure

```
docs/
├── README.md                          # This file - documentation index
├── CONTRIBUTING.md                    # Contribution guidelines
├── user-guide/                        # End-user documentation
│   ├── quick-start.md
│   ├── platform-connections.md
│   ├── compute-providers.md
│   ├── model-browser.md
│   ├── training-configuration.md
│   ├── configuration-management.md
│   ├── deployment.md
│   ├── inference-playground.md
│   ├── gradio-demo.md
│   └── logging-diagnostics.md
├── developer-guide/                   # Developer documentation
│   ├── api-documentation.md
│   ├── connector-development.md
│   ├── auto-update-system.md
│   ├── build-and-installers.md
│   ├── ci-cd-setup.md
│   ├── cloud-platforms.md
│   ├── cost-calculator.md
│   ├── credential-management.md
│   ├── export-system.md
│   ├── gradio-generator.md
│   ├── multi-run-management.md
│   ├── notification-system.md
│   ├── paused-run-management.md
│   ├── performance-optimization.md
│   ├── platform-connections.md
│   ├── security.md
│   ├── telemetry.md
│   ├── testing.md
│   ├── training-orchestrator.md
│   └── wandb-integration.md
├── reference/                         # Reference materials
│   ├── error-handling.md
│   ├── faq.md
│   └── troubleshooting.md
└── video-tutorials/                   # Video content
    └── index.md
```

---

## Contributing to Documentation

We welcome contributions to improve our documentation! Here's how you can help:

### Documentation Guidelines

1. **Clarity First**: Write for users who may be unfamiliar with the topic
2. **Use Examples**: Include code examples and screenshots where helpful
3. **Keep It Current**: Update docs when features change
4. **Link Appropriately**: Cross-reference related documentation
5. **Follow Structure**: Place docs in the appropriate directory:
   - `user-guide/` - End-user features and workflows
   - `developer-guide/` - Technical implementation details
   - `reference/` - Reference materials and troubleshooting

### How to Contribute

1. **Find or Create an Issue**: Check existing issues or create a new one describing the documentation improvement
2. **Fork and Branch**: Create a feature branch for your changes
3. **Write/Update Docs**: Follow our style guide and formatting conventions
4. **Test Links**: Ensure all internal links work correctly
5. **Submit PR**: Create a pull request with a clear description of your changes

### Documentation Style Guide

**Formatting**
- Use Markdown for all documentation
- Use `#` for main title, `##` for sections, `###` for subsections
- Use code blocks with language specification: ` ```python ` or ` ```typescript `
- Use **bold** for UI elements and important terms
- Use `inline code` for commands, file names, and code references

**Structure**
- Start with a brief overview of what the document covers
- Use clear section headings
- Include a table of contents for longer documents
- End with related links or next steps

**Content**
- Write in present tense
- Use active voice
- Keep sentences concise
- Define technical terms on first use
- Include practical examples
- Add troubleshooting tips where relevant

### Reporting Documentation Issues

Found a typo, broken link, or unclear explanation? Please:
1. Open an issue on GitHub with the label `documentation`
2. Include the file path and section
3. Describe the problem or suggest an improvement

---

## Support

- **GitHub Issues**: [Report bugs or request features](https://github.com/your-org/peft-studio/issues)
- **Discussions**: [Community forum](https://github.com/your-org/peft-studio/discussions)
- **Documentation Issues**: Use the `documentation` label when creating issues

---

## License

PEFT Studio is released under the MIT License. See the [LICENSE](../LICENSE) file for details.
