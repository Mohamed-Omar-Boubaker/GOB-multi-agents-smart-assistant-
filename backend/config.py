"""
Configuration centralisée du système
Responsable: Montassar

Rôle:
- Charger variables d'environnement
- Centraliser paramètres système
- Configurer les modules (LLM, n8n, MQTT, etc.)
"""

import os
from dotenv import load_dotenv # type: ignore
from pathlib import Path

# Charger .env depuis la racine du backend
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)


class Config:
    """Configuration centralisée du backend Python."""
    
    # ==================== SERVEUR ====================
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8000))
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")  # development|production
    
    # ==================== MODULE LLM ====================
    LLM_API_URL = os.getenv("LLM_API_URL", "http://localhost:5000")
    LLM_API_KEY = os.getenv("LLM_API_KEY", "")
    LLM_MODEL = os.getenv("LLM_MODEL", "gpt-3.5-turbo")
    LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", 30))
    LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", 500))
    LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", 0.7))
    
    # ==================== LANGUE PAR DÉFAUT ====================
    DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "fr")  # en|fr|ar
    FORCE_LLM_RESPONSE_LANGUAGE = os.getenv("FORCE_LLM_RESPONSE_LANGUAGE", "")  # Force LLM response language
    FORCE_STT_LANGUAGE = os.getenv("FORCE_STT_LANGUAGE", "")  # Force Whisper transcription language
    MAX_RESPONSE_SENTENCES = int(os.getenv("MAX_RESPONSE_SENTENCES", 3))  # Max sentences in LLM responses
    
    # ==================== MODULE STT (Speech-to-Text) ====================
    STT_ENGINE = os.getenv("STT_ENGINE", "whisper")  # whisper|google|vosk
    WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")  # tiny|base|small|medium
    WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "cpu")  # cpu|cuda
    STT_LANGUAGE = os.getenv("STT_LANGUAGE", DEFAULT_LANGUAGE)
    
    # ==================== MODULE TTS (Text-to-Speech) ====================
    TTS_ENGINE = os.getenv("TTS_ENGINE", "gtts")  # gtts|pyttsx3|piper
    TTS_LANGUAGE = os.getenv("TTS_LANGUAGE", DEFAULT_LANGUAGE)
    TTS_VOICE = os.getenv("TTS_VOICE", "female")
    TTS_SPEED = float(os.getenv("TTS_SPEED", 1.0))
    PIPER_MODEL_PATH = os.getenv("PIPER_MODEL_PATH", "models/piper/fr_FR-upmc-medium.onnx")
    
    # 🎵 TTS Audio Quality Settings (from test_piper.py)
    # Sample rate controls pitch/tone: Higher = sharper voice, Lower = deeper voice
    # Recommended values: 20000 (deep), 21470 (natural), 25750 (sharp)
    TTS_SAMPLE_RATE = int(os.getenv("TTS_SAMPLE_RATE", 21470))  # Hz - Natural human-like voice
    TTS_CHANNELS = int(os.getenv("TTS_CHANNELS", 1))  # 1=mono, 2=stereo
    TTS_SAMPLE_WIDTH = int(os.getenv("TTS_SAMPLE_WIDTH", 2))  # bytes per sample (2=16bit)
    
    # ==================== MODULE N8N ====================
    N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "http://localhost:5678/webhook/action")
    N8N_API_URL = os.getenv("N8N_API_URL", "http://localhost:5678")
    N8N_API_KEY = os.getenv("N8N_API_KEY", "")
    N8N_TIMEOUT = int(os.getenv("N8N_TIMEOUT", 60))
    
    # ==================== MODULE MQTT (Device Communication) ====================
    MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
    MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
    MQTT_USERNAME = os.getenv("MQTT_USERNAME", "")
    MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "")
    # Topics génériques device/* (flexibles pour tout type de device)
    MQTT_TOPIC_AUDIO_OUT = os.getenv("MQTT_TOPIC_AUDIO_OUT", "device/audio")
    MQTT_TOPIC_COMMAND_OUT = os.getenv("MQTT_TOPIC_COMMAND_OUT", "device/command")
    MQTT_TOPIC_STATUS_IN = os.getenv("MQTT_TOPIC_STATUS_IN", "device/status")
    MQTT_TOPIC_ROBOT_STATE_OUT = os.getenv("MQTT_TOPIC_ROBOT_STATE_OUT", "gob/robot/state")
    MQTT_TOPIC_ROBOT_STATE_ACK_IN = os.getenv("MQTT_TOPIC_ROBOT_STATE_ACK_IN", "gob/robot/state/ack")
    MQTT_QOS = int(os.getenv("MQTT_QOS", 1))
    MQTT_KEEPALIVE = int(os.getenv("MQTT_KEEPALIVE", 60))
    
    # ==================== SÉCURITÉ ====================
    SECRET_KEY = os.getenv("SECRET_KEY", "changeme-secret-key-production-MUST-BE-SECURE")
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRATION = int(os.getenv("JWT_EXPIRATION", 3600))  # secondes
    HMAC_ALGORITHM = os.getenv("HMAC_ALGORITHM", "sha256")
    
    # ==================== BASE DE DONNÉES ====================
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///agent.db")
    DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", 10))
    DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", 20))
    
    # ==================== CLASSIFIER ====================
    CLASSIFIER_METHOD = os.getenv("CLASSIFIER_METHOD", "rules")  # rules|ml|llm
    CLASSIFIER_THRESHOLD = float(os.getenv("CLASSIFIER_THRESHOLD", 0.60))  # 🔥 Lowered to 0.60 for normal conversations
    CLASSIFIER_USE_LLM_FALLBACK = os.getenv("CLASSIFIER_USE_LLM_FALLBACK", "True").lower() == "true"
    
    # 🔥 Confidence zones for Safe AI
    CLARIFICATION_CONFIDENCE_MIN = float(os.getenv("CLARIFICATION_CONFIDENCE_MIN", 0.40))  # Below this: reject
    CLARIFICATION_CONFIDENCE_MAX = float(os.getenv("CLARIFICATION_CONFIDENCE_MAX", 0.60))  # Between min-max: ask clarification
    # Above CLASSIFIER_THRESHOLD (0.60): proceed with high confidence
    
    # ==================== LIMITES ET SÉCURITÉ ====================
    MAX_AUDIO_SIZE_MB = int(os.getenv("MAX_AUDIO_SIZE_MB", 10))
    MAX_TEXT_LENGTH = int(os.getenv("MAX_TEXT_LENGTH", 1000))
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", 3))
    REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", 30))  # secondes
    RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", 60))
    
    # ==================== JOURNALISATION ====================
    LOG_DIR = os.getenv("LOG_DIR", "logs")
    LOG_FILE = os.getenv("LOG_FILE", "logs/agent.log")
    LOG_MAX_BYTES = int(os.getenv("LOG_MAX_BYTES", 10485760))  # 10MB
    LOG_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", 5))
    LOG_FORMAT = os.getenv("LOG_FORMAT", "json")  # json|text
    
    # ==================== CONFIRMATION ====================
    CONFIRMATION_TIMEOUT = int(os.getenv("CONFIRMATION_TIMEOUT", 30))  # secondes
    CONFIRMATION_AUTO_CANCEL = os.getenv("CONFIRMATION_AUTO_CANCEL", "True").lower() == "true"
    
    # ==================== CORS (pour développement) ====================
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
    CORS_ALLOW_CREDENTIALS = os.getenv("CORS_ALLOW_CREDENTIALS", "True").lower() == "true"
    
    # ==================== FEATURES FLAGS ====================
    ENABLE_AUDIO_PROCESSING = os.getenv("ENABLE_AUDIO_PROCESSING", "True").lower() == "true"
    ENABLE_N8N_INTEGRATION = os.getenv("ENABLE_N8N_INTEGRATION", "False").lower() == "true"
    ENABLE_MQTT_INTEGRATION = os.getenv("ENABLE_MQTT_INTEGRATION", "False").lower() == "true"
    ENABLE_CONVERSATION_HISTORY = os.getenv("ENABLE_CONVERSATION_HISTORY", "True").lower() == "true"
    
    # 🔥 FIX #4: Demo Mode for reliable soutenance - Never depends on external services
    DEMO_MODE = os.getenv("DEMO_MODE", "True").lower() == "true"  # Simulates action execution for demo stability
    
    # Auto-publish audio to MQTT after TTS (pour device ESP32/Fake)
    AUTO_PUBLISH_AUDIO_TO_MQTT = os.getenv("AUTO_PUBLISH_AUDIO_TO_MQTT", "True").lower() == "true"

    N8N_WEBHOOK_REMINDER_URL: str = os.getenv(
        "N8N_WEBHOOK_REMINDER_URL",
        "http://localhost:5678/webhook/reminder",
    )
    


def validate_config():
    """Valide la configuration critique au démarrage."""
    errors = []
    
    # Vérifications critiques
    if not Config.SECRET_KEY or Config.SECRET_KEY == "changeme-secret-key-production-MUST-BE-SECURE":
        if Config.ENVIRONMENT == "production":
            errors.append("SECRET_KEY must be set in production environment")
    
    if not Config.LLM_API_URL:
        errors.append("LLM_API_URL is required")
    
    # Vérifications optionnelles selon les features activées
    if Config.ENABLE_N8N_INTEGRATION and not Config.N8N_WEBHOOK_URL:
        errors.append("N8N_WEBHOOK_URL is required when N8N integration is enabled")
    
    if Config.ENABLE_MQTT_INTEGRATION and not Config.MQTT_BROKER:
        errors.append("MQTT_BROKER is required when MQTT integration is enabled")
    
    # Vérification des chemins
    log_dir = Path(Config.LOG_DIR)
    if not log_dir.exists():
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            errors.append(f"Cannot create log directory: {e}")
    
    if errors:
        raise ValueError(f"Configuration errors:\n" + "\n".join(f"  - {error}" for error in errors))
    
    return True


# Validation automatique au chargement
try:
    validate_config()
except ValueError as e:
    print(f"⚠️  Configuration validation issues:\n{e}")
    if Config.ENVIRONMENT == "production":
        raise
    else:
        print("⚠️  Continuing in development mode with default values")
