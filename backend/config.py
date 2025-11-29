import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = DATA_DIR / "models"
DATASETS_DIR = DATA_DIR / "datasets"
CHECKPOINTS_DIR = DATA_DIR / "checkpoints"
CACHE_DIR = DATA_DIR / "cache"

# Create directories if they don't exist
for directory in [DATA_DIR, MODELS_DIR, DATASETS_DIR, CHECKPOINTS_DIR, CACHE_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Database
DATABASE_URL = f"sqlite:///{DATA_DIR / 'peft_studio.db'}"

# API Settings
API_HOST = "127.0.0.1"
API_PORT = 8000

# Training defaults
DEFAULT_LEARNING_RATE = 2e-4
DEFAULT_BATCH_SIZE = 4
DEFAULT_EPOCHS = 3
DEFAULT_MAX_SEQ_LENGTH = 512

# PEFT defaults
DEFAULT_LORA_R = 8
DEFAULT_LORA_ALPHA = 16
DEFAULT_LORA_DROPOUT = 0.1
DEFAULT_LORA_TARGET_MODULES = ["q_proj", "v_proj"]
