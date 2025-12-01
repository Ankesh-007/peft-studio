# Frequently Asked Questions (FAQ)

Common questions about PEFT Studio.

## General Questions

### What is PEFT Studio?
PEFT Studio is a unified desktop application for fine-tuning large language models using Parameter-Efficient Fine-Tuning (PEFT) techniques. It integrates with multiple cloud GPU providers, model registries, experiment trackers, and deployment platforms.

### Is PEFT Studio free?
Yes, PEFT Studio is free and open-source under the MIT license. However, you'll need to pay for:
- Cloud GPU compute (if not using local GPU)
- Platform API usage (some platforms have free tiers)
- Model deployment costs

### What platforms does PEFT Studio support?
**Compute:** RunPod, Lambda Labs, Vast.ai, Local GPU
**Models:** HuggingFace, Civitai, Ollama
**Tracking:** Weights & Biases, Comet ML, Arize Phoenix
**Deployment:** Predibase, Together AI, Modal, Replicate
**Evaluation:** DeepEval, HoneyHive

### What operating systems are supported?
- Windows 10 and later
- macOS 10.15 (Catalina) and later
- Linux (Ubuntu 20.04+, Fedora 34+, Arch)

### Do I need a GPU?
Not required, but highly recommended. You can:
- Use your local GPU (NVIDIA with CUDA)
- Rent cloud GPUs through integrated providers
- Use CPU for inference (very slow for training)

## Installation and Setup

### How do I install PEFT Studio?
Download the installer for your OS from the [releases page](https://github.com/your-org/peft-studio/releases):
- Windows: Run the .exe installer
- macOS: Open the .dmg and drag to Applications
- Linux: Make the .AppImage executable and run

### Where is my data stored?
- **Windows**: `%APPDATA%\peft-studio\`
- **macOS**: `~/Library/Application Support/peft-studio/`
- **Linux**: `~/.config/peft-studio/`

### How do I uninstall PEFT Studio?
- **Windows**: Use "Add or Remove Programs"
- **macOS**: Drag from Applications to Trash
- **Linux**: Delete the AppImage file

To remove all data, also delete the data directory (see above).

### Can I use PEFT Studio offline?
Yes! PEFT Studio has offline-first architecture:
- Browse cached models
- Configure training
- View past runs
- Operations queue and sync when online

## Training Questions

### What PEFT algorithms are supported?
- **LoRA**: Low-Rank Adaptation
- **QLoRA**: Quantized LoRA (4-bit, 8-bit)
- **DoRA**: Weight-Decomposed LoRA
- **PiSSA**: Principal Singular Values Adaptation
- **rsLoRA**: Rank-Stabilized LoRA

### How long does training take?
Depends on:
- Model size (7B: 30-60 min, 13B: 1-2 hours, 70B: 4-8 hours)
- Dataset size (1000 examples: ~30 min, 10000: ~3 hours)
- GPU type (A100 is ~2× faster than RTX 4090)
- PEFT configuration (higher rank = longer training)

### How much does training cost?
Typical costs:
- **7B model on RTX 4090**: $0.50-$2.00
- **13B model on A100**: $2.00-$5.00
- **70B model on 8×A100**: $20.00-$50.00

Use local GPU for zero compute cost!

### What's the minimum dataset size?
- **Minimum**: 50-100 examples
- **Recommended**: 500-1000 examples
- **Optimal**: 5000+ examples

Quality matters more than quantity!

### Can I pause and resume training?
Yes! PEFT Studio supports:
- Automatic checkpointing
- Manual pause/resume
- Resume after crashes
- Continue from any checkpoint

### What if training fails?
PEFT Studio will:
1. Capture error logs
2. Save last checkpoint
3. Suggest solutions
4. Offer to retry or adjust config

Common fixes:
- Reduce batch size (OOM errors)
- Lower learning rate (NaN loss)
- Check dataset format (parsing errors)

## Model and Data Questions

### What models can I fine-tune?
Any model on HuggingFace, Civitai, or Ollama that supports:
- Transformers architecture
- Causal language modeling
- Compatible with PEFT

Popular: Llama 2, Mistral, Falcon, CodeLlama, Phi

### Can I use my own model?
Yes! If it's:
- In HuggingFace format
- Uploaded to HuggingFace Hub
- Or available locally

### What data format is required?
Supported formats:
- JSON Lines (.jsonl)
- JSON array
- CSV
- Instruction format (instruction/input/output)

See [training configuration guide](../user-guide/training-configuration.md) for examples.

### How do I prepare my dataset?
1. Collect examples (text, conversations, instructions)
2. Format as JSON/JSONL
3. Clean and deduplicate
4. Split into train/validation
5. Upload to PEFT Studio

### Can I use private models?
Yes! Connect your HuggingFace account and access:
- Private models
- Gated models (with approval)
- Organization models

## Deployment Questions

### Where can I deploy my adapter?
- **Predibase**: Hot-swappable adapters
- **Together AI**: Serverless endpoints
- **Modal**: Function-based deployment
- **Replicate**: Version-controlled deployment
- **Local**: Run on your machine

### How much does deployment cost?
Varies by platform:
- **Predibase**: $0.0002-$0.001 per token
- **Together AI**: $0.0002-$0.0008 per token
- **Modal**: $0.0001-$0.0005 per token
- **Local**: Free (electricity only)

### Can I deploy multiple adapters?
Yes! Predibase supports hot-swapping:
- Load multiple adapters
- Switch instantly
- Share base model
- Pay only for active usage

### How do I test my deployment?
PEFT Studio provides:
- Built-in testing interface
- Sample prompts
- Latency monitoring
- Cost tracking

## Performance Questions

### Why is the app slow to start?
Possible causes:
- Large model cache
- Many cached jobs
- Database needs optimization

Solutions:
- Clear cache
- Archive old jobs
- Run database vacuum

### Why is training slow?
Check:
- GPU utilization (should be >80%)
- Batch size (increase if possible)
- Data loading (use more workers)
- Network speed (for cloud training)

### How can I speed up inference?
- Use quantization (int4/int8)
- Reduce max_tokens
- Use faster GPU
- Enable caching
- Batch requests

### How much RAM do I need?
- **Minimum**: 8GB
- **Recommended**: 16GB
- **Optimal**: 32GB+

More RAM allows:
- Larger model cache
- More concurrent jobs
- Better performance

## Security and Privacy

### Are my API keys secure?
Yes! PEFT Studio:
- Uses OS-level keystore
- Encrypts at rest (AES-256)
- Never logs credentials
- Transmits over HTTPS only

### Is my data private?
Your data never leaves your machine except:
- When uploading to platforms (with confirmation)
- When syncing to experiment trackers (opt-in)
- When deploying models (explicit action)

### Does PEFT Studio collect telemetry?
Only if you opt-in. Telemetry includes:
- Feature usage (anonymized)
- Error reports (no PII)
- Performance metrics

You can disable anytime in Settings.

### Can I use PEFT Studio in production?
Yes! PEFT Studio is production-ready:
- Stable API
- Comprehensive logging
- Error handling
- Security best practices

## Troubleshooting

### Connection to platform failed
1. Verify API key is correct
2. Check internet connection
3. Test platform status page
4. Try different platform

### Out of memory during training
1. Reduce batch size
2. Enable quantization (QLoRA)
3. Use gradient checkpointing
4. Try smaller model

### Model not found
1. Check model ID spelling
2. Verify model is public
3. Ensure you have access
4. Try different registry

### Deployment not responding
1. Wait for cold start (30-60s)
2. Check endpoint URL
3. Verify authentication
4. Test with simple prompt

## Advanced Questions

### Can I create custom connectors?
Yes! PEFT Studio has a plugin system:
1. Implement connector interface
2. Place in plugins directory
3. Register connector
4. Test and use

See [connector development guide](../developer-guide/connector-development.md).

### Does PEFT Studio support multi-GPU?
Yes! For local training:
- Automatic multi-GPU detection
- Data parallelism
- Model parallelism (large models)

For cloud: Select multi-GPU instances.

### Can I use PEFT Studio programmatically?
Yes! PEFT Studio provides:
- REST API
- WebSocket API
- Python SDK
- JavaScript SDK

See [API documentation](../developer-guide/api-documentation.md).

### How do I contribute?
We welcome contributions!
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

See [contributing guide](../developer-guide/contributing.md).

## Billing and Costs

### How do I track costs?
PEFT Studio shows:
- Real-time cost estimates
- Actual costs after completion
- Cost per epoch
- Cost comparisons across providers

### Can I set budget limits?
Yes! Configure in Settings:
- Maximum cost per job
- Daily/monthly budgets
- Alerts at thresholds
- Auto-stop on limit

### Which provider is cheapest?
Generally:
1. **Local GPU**: Free
2. **Vast.ai**: $0.20-$1.50/hour
3. **RunPod**: $0.39-$2.89/hour
4. **Lambda Labs**: $1.10-$2.49/hour

But consider:
- Availability
- Reliability
- Performance
- Support

## Getting Help

### Where can I get help?
- **Documentation**: [docs.peft-studio.com](https://docs.peft-studio.com)
- **GitHub Issues**: [Report bugs](https://github.com/your-org/peft-studio/issues)
- **Discussions**: [Ask questions](https://github.com/your-org/peft-studio/discussions)
- **Discord**: [Join community](https://discord.gg/peft-studio)
- **Email**: support@peft-studio.com

### How do I report a bug?
1. Check if already reported
2. Gather information:
   - PEFT Studio version
   - Operating system
   - Steps to reproduce
   - Error messages
3. Create GitHub issue
4. Attach diagnostic report

### How do I request a feature?
1. Check roadmap and existing requests
2. Create GitHub discussion
3. Describe use case
4. Explain benefits
5. Community votes on priority

### Is there a community?
Yes! Join us:
- **Discord**: Daily discussions
- **GitHub**: Code and issues
- **Twitter**: Updates and tips
- **YouTube**: Tutorials

## Roadmap

### What's coming next?
Planned features:
- More platform integrations
- Advanced evaluation tools
- Team collaboration features
- Cloud sync
- Mobile companion app

See [roadmap](https://github.com/your-org/peft-studio/projects) for details.

### Can I influence the roadmap?
Absolutely! We prioritize based on:
- Community votes
- User feedback
- Use case importance
- Technical feasibility

Vote on features in GitHub Discussions!

## Still Have Questions?

Can't find your answer? 

- **Search docs**: [docs.peft-studio.com](https://docs.peft-studio.com)
- **Ask community**: [GitHub Discussions](https://github.com/your-org/peft-studio/discussions)
- **Contact support**: support@peft-studio.com

We're here to help! 🚀
