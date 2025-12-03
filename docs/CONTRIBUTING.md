# Contributing to PEFT Studio Documentation

Thank you for your interest in improving PEFT Studio documentation!

## How to Contribute

### Reporting Issues

Found a problem in the docs?
1. Check if already reported in [GitHub Issues](https://github.com/your-org/peft-studio/issues)
2. Create a new issue with:
   - Page/section with the problem
   - What's wrong or unclear
   - Suggested improvement
   - Your experience level (helps us gauge clarity)

### Suggesting Improvements

Have an idea for better docs?
1. Open a [GitHub Discussion](https://github.com/your-org/peft-studio/discussions)
2. Describe your suggestion
3. Explain why it would help users
4. Community can discuss and vote

### Submitting Changes

Want to fix or improve docs yourself?

#### Small Changes (typos, clarifications)
1. Click "Edit this page" on any doc page
2. Make your changes in GitHub's editor
3. Submit a pull request
4. We'll review and merge quickly!

#### Large Changes (new guides, restructuring)
1. Fork the repository
2. Create a branch: `git checkout -b docs/your-improvement`
3. Make your changes
4. Test locally (see below)
5. Submit a pull request
6. Discuss with maintainers

## Documentation Structure

```
docs/
├── README.md                 # Documentation home
├── user-guide/              # End-user guides
│   ├── quick-start.md
│   ├── platform-connections.md
│   ├── training-configuration.md
│   └── ...
├── developer-guide/         # Developer documentation
│   ├── connector-development.md
│   ├── api-documentation.md
│   └── ...
├── reference/               # Reference materials
│   ├── troubleshooting.md
│   ├── faq.md
│   └── ...
└── video-tutorials/         # Video tutorial index
    └── index.md
```

## Writing Guidelines

### Style Guide

**Tone:**
- Friendly and approachable
- Clear and concise
- Assume beginner knowledge
- Explain technical terms

**Formatting:**
- Use headings hierarchically (H1 → H2 → H3)
- Keep paragraphs short (2-4 sentences)
- Use bullet points for lists
- Include code examples
- Add screenshots when helpful

**Code Examples:**
- Always test code before including
- Include language identifier in code blocks
- Add comments for clarity
- Show both input and output

**Links:**
- Use relative links for internal docs
- Use descriptive link text (not "click here")
- Check links aren't broken

### Content Guidelines

**User Guides:**
- Start with "What you'll learn"
- Include step-by-step instructions
- Add screenshots for UI steps
- Provide troubleshooting tips
- Link to related guides

**Developer Guides:**
- Include complete code examples
- Explain the "why" not just "how"
- Cover edge cases
- Link to API reference
- Provide testing examples

**Reference:**
- Be comprehensive
- Use consistent formatting
- Include all options/parameters
- Provide examples
- Keep up to date

### Examples

**Good:**
```markdown
## Connecting to RunPod

To connect PEFT Studio to RunPod:

1. Get your API key from [RunPod Settings](https://runpod.io/console/user/settings)
2. In PEFT Studio, click **Platforms** → **RunPod** → **Connect**
3. Paste your API key
4. Click **Verify Connection**

You should see a green "Connected" status.

**Troubleshooting:** If connection fails, verify your API key has full access permissions.
```

**Not as good:**
```markdown
## RunPod

Connect to RunPod by entering your API key.
```

## Testing Documentation

### Local Preview

1. Install dependencies:
   ```bash
   npm install -g docsify-cli
   ```

2. Serve docs locally:
   ```bash
   docsify serve docs
   ```

3. Open http://localhost:3000

### Checking Links

```bash
# Install link checker
npm install -g markdown-link-check

# Check all docs
find docs -name "*.md" -exec markdown-link-check {} \;
```

### Spell Check

```bash
# Install spell checker
npm install -g markdown-spellcheck

# Check spelling
mdspell "docs/**/*.md" --en-us --ignore-numbers --ignore-acronyms
```

## Pull Request Process

1. **Create PR** with clear title and description
2. **Link related issue** if applicable
3. **Request review** from maintainers
4. **Address feedback** promptly
5. **Squash commits** before merge

### PR Checklist

- [ ] Changes are accurate and tested
- [ ] Writing follows style guide
- [ ] Links work correctly
- [ ] Code examples are tested
- [ ] Screenshots are up to date
- [ ] Spelling and grammar checked
- [ ] Related docs updated

## Video Tutorials

Want to create a video tutorial?

### Requirements

- **Length**: 5-20 minutes
- **Quality**: 1080p minimum
- **Audio**: Clear narration
- **Content**: Follow existing tutorial structure
- **Format**: MP4 (H.264)

### Process

1. Propose tutorial topic in Discussions
2. Get approval from maintainers
3. Create and upload video
4. Submit PR with:
   - Video file or YouTube link
   - Transcript
   - Thumbnail
   - Description

### Guidelines

- Show real workflows
- Explain each step clearly
- Include troubleshooting
- Keep pace moderate
- Add captions/subtitles

## Translation

Want to translate docs to another language?

1. Create language directory: `docs/es/` (for Spanish)
2. Translate markdown files
3. Maintain same structure
4. Update main README with language links
5. Submit PR

**Priority languages:**
- Spanish (es)
- Chinese (zh)
- French (fr)
- German (de)
- Japanese (ja)

## Recognition

Contributors are recognized:
- In CONTRIBUTORS.md
- In release notes
- On documentation site
- In application about page

Thank you for helping make PEFT Studio better! 🎉

## Questions?

- **Documentation questions**: [GitHub Discussions](https://github.com/your-org/peft-studio/discussions)
- **General questions**: support@peft-studio.com
- **Chat with us**: [Discord](https://discord.gg/peft-studio)
