"""
Configuration Module LLM
Responsable: Équipe Backend
"""

import os
from dotenv import load_dotenv

load_dotenv()

class LLMConfig:
    """Configuration du module LLM."""
    
    # API Configuration
    LLM_API_KEY = os.getenv("LLM_API_KEY", "")
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")  # "openai", "huggingface", "local"
    LLM_MODEL = os.getenv("LLM_MODEL", "gpt-3.5-turbo")
    
    # Server Configuration
    HOST = os.getenv("LLM_HOST", "0.0.0.0")
    PORT = int(os.getenv("LLM_PORT", 5000))
    DEBUG = os.getenv("LLM_DEBUG", "False").lower() == "true"
    
    # Performance
    MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", 500))
    TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", 0.7))
    TIMEOUT = int(os.getenv("LLM_TIMEOUT", 30))
    
    # Logging
    LOG_LEVEL = os.getenv("LLM_LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LLM_LOG_FILE", "logs/llm.log")
