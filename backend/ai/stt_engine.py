"""
STT Engine - Speech-to-Text
Responsable: Montassar
Priorité: 🔴 CRITIQUE
Temps estimé: 15h

INPUT JSON:
{
  "request_id": "req_audio_001",
  "audio_data": "UklGRiQAAABXQVZFZm10...",  # base64
  "audio_format": "wav",
  "audio_metadata": {...},
  "language": "fr",
  "user_id": "user_001"
}

OUTPUT JSON:
{
  "request_id": "req_audio_001",
  "transcription": "Allume la lampe du salon",
  "language": "fr",
  "confidence": 0.95,
  "processing_time_ms": 1247,
  "model_used": "whisper-tiny",
  "alternatives": [...],
  "timestamp": "2026-01-20T10:30:02Z"
}

Modèle: faster-whisper (tiny, optimisé pour CPU)
"""

import warnings
warnings.filterwarnings("ignore", category=UserWarning)

import base64
import time
import tempfile
import os
from datetime import datetime, UTC
from typing import Dict, Optional, Union
from pathlib import Path

from faster_whisper import WhisperModel  # type: ignore
from backend.config import Config


class STTEngine:
    """
    Moteur Speech-to-Text avec faster-whisper.
    Convertit audio en texte via Whisper (modèle tiny optimisé CPU).
    
    Basé sur tests validés (testWisper.py) :
    - Modèle: tiny (86MB, rapide)
    - Device: CPU
    - Compute type: int8 (optimisé)
    - beam_size: 1 (performance)
    """
    
    def __init__(self, model: str = "small", device: str = "cpu", compute_type: str = "int8"):
        """
        Initialiser le moteur STT.
        Charge le modèle Whisper au démarrage (une seule fois).
        
        Args:
            model: Modèle Whisper ("tiny", "base", "small", "medium", "large")
            device: Device ("cpu", "cuda")
            compute_type: Type calcul ("int8", "float16", "float32")
        """
        print(f"[STT] Loading Whisper model '{model}'...")
        start_load = time.time()
        
        self.model_name = model
        self.device = device
        self.compute_type = compute_type
        
        # Charger modèle (comme testWisper.py)
        self.model = WhisperModel(model, device=device, compute_type=compute_type)
        
        load_time = time.time() - start_load
        print(f"[STT] Model loaded ✅ (chargé en {load_time:.2f} sec)")
    
    async def transcribe(
        self,
        audio_data: str,
        audio_format: str = "wav",
        language: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> Dict:
        """
        Transcrire audio en texte (version async pour Agent Core).
        
        Args:
            audio_data: Audio encodé en base64
            audio_format: Format audio ("wav", "mp3", "ogg")
            language: Langue de l'audio ("fr", "en", "ar")
            request_id: ID de la requête (optionnel)
            
        Returns:
            Dict avec transcription, confidence, processing_time_ms, etc.
            
        Raises:
            ValueError: Si audio_data vide ou format invalide
            RuntimeError: Si erreur transcription
        """
        if not audio_data:
            raise ValueError("audio_data cannot be empty")
        
        # Use DEFAULT_LANGUAGE if language not provided
        if language is None:
            language = Config.DEFAULT_LANGUAGE
        
        start_time = time.time()
        temp_file = None
        
        try:
            # 1. Décoder base64 → bytes
            try:
                audio_bytes = base64.b64decode(audio_data)
            except Exception as e:
                raise ValueError(f"Invalid base64 audio_data: {e}")
            
            # 2. Sauver dans fichier temporaire
            with tempfile.NamedTemporaryFile(suffix=f".{audio_format}", delete=False) as f:
                temp_file = f.name
                f.write(audio_bytes)
            
            # 3. Transcription (comme testWisper.py)
            # If FORCE_STT_LANGUAGE is set, override the language parameter
            force_lang = Config.FORCE_STT_LANGUAGE
            transcription_language = force_lang if force_lang else language
            
            # Use language parameter to FORCE Whisper (not auto-detect)
            # Set language=None only for auto-detection
            segments, info = self.model.transcribe(
                temp_file,
                beam_size=1,  # Performance optimale
                language=transcription_language if transcription_language else None,
                task="transcribe"  # Force transcription (not translation)
            )
            
            # 4. Joindre segments
            text = " ".join([segment.text for segment in segments])
            
            # 5. Calculer temps
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            # 6. Construire résultat
            result = {
                "request_id": request_id or f"stt_{int(time.time() * 1000)}",
                "transcription": text.strip(),
                "language": language,
                "confidence": 0.85,  # faster-whisper ne retourne pas confidence par défaut
                "processing_time_ms": processing_time_ms,
                "model_used": f"whisper-{self.model_name}",
                "alternatives": [],  # TODO: Si besoin, extraire alternatives
                "timestamp": datetime.now(UTC).isoformat()
            }
            
            return result
        
        except Exception as e:
            raise RuntimeError(f"STT transcription failed: {e}")
        
        finally:
            # 7. Nettoyer fichier temporaire
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                except:
                    pass  # Pas grave si échec nettoyage
    
    def transcribe_sync(
        self,
        audio_data: str,
        audio_format: str = "wav",
        language: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> Dict:
        """
        Version synchrone de transcribe() pour usage non-async.
        
        Args:
            audio_data: Audio encodé en base64
            audio_format: Format audio
            language: Langue
            request_id: ID requête
            
        Returns:
            Dict avec transcription
        """
        import asyncio
        
        # Use DEFAULT_LANGUAGE if language not provided
        if language is None:
            language = Config.DEFAULT_LANGUAGE
        
        # Créer event loop si nécessaire
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Exécuter version async
        return loop.run_until_complete(
            self.transcribe(audio_data, audio_format, language, request_id)
        )
    
    def transcribe_file(self, audio_file_path: str, language: Optional[str] = None) -> str:
        """
        Transcrire directement depuis un fichier audio (pour tests).
        
        Args:
            audio_file_path: Chemin vers fichier audio
            language: Langue
            
        Returns:
            Texte transcrit
        """
        start = time.time()
        
        # Use DEFAULT_LANGUAGE if language not provided
        if language is None:
            language = Config.DEFAULT_LANGUAGE
        
        # Use FORCE_STT_LANGUAGE if set
        force_lang = Config.FORCE_STT_LANGUAGE
        transcription_language = force_lang if force_lang else language
        
        segments, _ = self.model.transcribe(
            audio_file_path, 
            beam_size=1, 
            language=transcription_language if transcription_language else None,
            task="transcribe"
        )
        text = " ".join([s.text for s in segments])
        
        elapsed = time.time() - start
        print(f"⏱️ Temps transcription : {elapsed:.2f} sec")
        
        return text.strip()
