# Quick Start Guide

Get up and running with PEFT Studio in 5 minutes.

## Prerequisites

- Windows 10+, macOS 10.15+, or Linux (Ubuntu 20.04+)
- 8GB RAM minimum (16GB recommended)
- 10GB free disk space
- Internet connection for initial setup

## Installation

### Windows
1. Download `PEFT-Studio-Setup.exe` from [releases](https://github.com/your-org/peft-studio/releases)
2. Run the installer
3. Follow the installation wizard
4. Launch PEFT Studio from the Start Menu

### macOS
1. Download `PEFT-Studio.dmg` from [releases](https://github.com/your-org/peft-studio/releases)
2. Open the DMG file
3. Drag PEFT Studio to Applications
4. Launch from Applications folder

### Linux
1. Download `PEFT-Studio.AppImage` from [releases](https://github.com/your-org/peft-studio/releases)
2. Make it executable: `chmod +x PEFT-Studio.AppImage`
3. Run: `./PEFT-Studio.AppImage`

## First Launch

On first launch, PEFT Studio will:
1. Initialize the local database
2. Create configuration directories
3. Show the welcome screen

## Connect Your First Platform

1. Click **Platforms** in the sidebar
2. Select a platform (e.g., HuggingFace)
3. Click **Connect**
4. Enter your API credentials
5. Click **Verify Connection**

## Your First Training Run

1. Navigate to **Training** → **New Training Run**
2. **Select a Model**: Browse and select a base model (e.g., `meta-llama/Llama-2-7b-hf`)
3. **Configure PEFT**: Choose LoRA with default settings
4. **Select Compute**: Choose local GPU or a cloud provider
5. **Upload Dataset**: Select your training data
6. **Review & Launch**: Verify settings and start training

## Monitor Training

- View real-time metrics in the dashboard
- Stream logs as they're generated
- Track GPU usage and costs
- Pause or stop training anytime

## Next Steps

- [Connect more platforms](platform-connections.md)
- [Explore the model browser](model-browser.md)
- [Learn about PEFT algorithms](training-configuration.md)
- [Deploy your first adapter](deployment-management.md)

## Getting Help

- Press `Ctrl/Cmd + /` for help
- Check the [Troubleshooting Guide](../reference/troubleshooting.md)
- Visit our [FAQ](../reference/faq.md)
