import os
from pathlib import Path
from runtime_paths import get_base_path, get_data_dir, get_models_dir, get_datasets_dir, get_checkpoints_dir, get_cache_dir

# Base directories - use runtime path resolution for bundled executable support
BASE_DIR = get_base_path()
DATA_DIR = get_data_dir()
MODELS_DIR = get_models_dir()
DATASETS_DIR = get_datasets_dir()
CHECKPOINTS_DIR = get_checkpoints_dir()
CACHE_DIR = get_cache_dir()

# Database - use data directory (writable location)
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
