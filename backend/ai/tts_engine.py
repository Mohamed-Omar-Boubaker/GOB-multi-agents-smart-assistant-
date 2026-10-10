"""
TTS Engine - Text-to-Speech
Responsable: Montassar
Date: 2026-02-10
Basé sur: test_piper.py (validé)

Utilise le protocole Wyoming avec serveur Piper pour synthèse vocale.
"""

import asyncio
import base64
import time
import re
from datetime import datetime, UTC
from typing import Dict, Optional
import io
import wave

from wyoming.tts import Synthesize  # type: ignore
from wyoming.audio import AudioChunk, AudioStop  # type: ignore
from wyoming.event import async_write_event, async_read_event  # type: ignore
from backend.config import Config


class TTSEngine:
    """
    Moteur Text-to-Speech via Wyoming/Piper.
    Convertit texte en audio via serveur Piper local.
    """
    
    def __init__(self, host: str = "127.0.0.1", port: int = 5002):
        """
        Initialiser le moteur TTS.
        
        Args:
            host: Adresse serveur Piper (défaut: localhost)
            port: Port serveur Piper (défaut: 5002)
        """
        self.host = host
        self.port = port
        
        # 🎵 Audio parameters from Config (modifiable via .env)
        self.sample_rate = Config.TTS_SAMPLE_RATE  # Contrôle le pitch/ton de la voix
        self.channels = Config.TTS_CHANNELS  # Mono/Stereo
        self.sample_width = Config.TTS_SAMPLE_WIDTH  # 16-bit audio
        
        print(f"[TTS] Engine initialized - Wyoming @ {host}:{port}")
        print(f"[TTS] Audio config: {self.sample_rate}Hz, {self.channels}ch, {self.sample_width*8}bit")
    
    def _clean_text_for_tts(self, text: str) -> str:
        """
        Nettoyer le texte avant synthèse vocale.
        
        Problème: LLM envoie des emojis (😊, 🎉, etc.) et le TTS les prononce
        littéralement ("emoji face souriant") au lieu de les ignorer.
        
        Solution: Supprimer tous les emojis et caractères spéciaux non-vocaux.
        
        Args:
            text: Texte original avec possibles emojis
            
        Returns:
            Texte nettoyé sans emojis ni symboles spéciaux
        """
        if not text:
            return text
        
        # Pattern pour détecter tous les emojis (tous les ranges Unicode d'emojis)
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F700-\U0001F77F"  # alchemical symbols
            "\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
            "\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
            "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
            "\U0001FA00-\U0001FA6F"  # Chess Symbols
            "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
            "\U00002702-\U000027B0"  # Dingbats
            "\U000024C2-\U0001F251"  # Enclosed characters
            "\U0001F926-\U0001F937"  # Various emojis (people)
            "\U0001F1E0-\U0001F1FF"  # Flags (iOS)
            "\u200d"  # Zero width joiner (used in emojis)
            "\ufe0f"  # Variation selector
            "\u20e3"  # Combining enclosing keycap
            "]+",
            flags=re.UNICODE
        )
        
        # Supprimer les emojis
        cleaned = emoji_pattern.sub('', text)
        
        # Supprimer les symboles spéciaux restants (garder lettres, chiffres, ponctuation de base)
        # On garde: lettres (toutes langues), chiffres, espace, ponctuation courante (.,!?;:'-")
        cleaned = re.sub(r'[^\w\s.,!?;:\'\"-]', '', cleaned, flags=re.UNICODE)
        
        # Nettoyer espaces multiples
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        # Log si nettoyage a modifié le texte
        if cleaned != text:
            print(f"[TTS] Text cleaned: '{text[:50]}...' → '{cleaned[:50]}...'")
        
        return cleaned
    
    async def synthesize(
        self, 
        text: str, 
        language: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> Dict:
        """
        Synthétiser texte en audio (version async pour Agent Core).
        Implémentation basée exactement sur test_piper.py.
        
        Args:
            text: Texte à synthétiser
            language: Langue du texte (fr, en, ar)
            request_id: ID de la requête (optionnel)
            
        Returns:
            Dict avec audio_data (base64), audio_format, audio_metadata
            
        Raises:
            ValueError: Si texte vide
            RuntimeError: Si erreur de connexion ou synthèse
        """
        if not text or not text.strip():
            raise ValueError("text cannot be empty")
        
        # 🧹 Clean text: remove emojis and special characters
        text = self._clean_text_for_tts(text)
        
        # Re-check if text is still valid after cleaning
        if not text or not text.strip():
            raise ValueError("text is empty after cleaning (only emojis/symbols)")
        
        # Use DEFAULT_LANGUAGE if language not provided
        if language is None:
            language = Config.DEFAULT_LANGUAGE
        
        start_time = time.time()
        
        try:
            # 1. Connexion au serveur Piper (comme test_piper.py)
            reader, writer = await asyncio.open_connection(self.host, self.port)
            
            # 2. Envoyer requête de synthèse (protocole Wyoming)
            synthesize = Synthesize(text=text)
            await async_write_event(synthesize.event(), writer)
            await writer.drain()
            
            # 3. Recevoir chunks audio
            audio_chunks = []
            
            while True:
                event = await async_read_event(reader)
                
                if event is None:
                    break
                
                # Chunk audio reçu
                if AudioChunk.is_type(event.type):
                    chunk = AudioChunk.from_event(event)
                    audio_chunks.append(chunk.audio)
                
                # Fin de la synthèse
                elif AudioStop.is_type(event.type):
                    break
            
            # 4. Fermer connexion
            writer.close()
            await writer.wait_closed()
            
            # 5. Joindre tous les chunks
            audio_bytes = b"".join(audio_chunks)
            
            if not audio_bytes:
                raise RuntimeError("No audio data received from TTS server")
            
            # 6. Créer fichier WAV en mémoire (comme test_piper.py)
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, "wb") as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(self.sample_width)
                wf.setframerate(self.sample_rate)
                wf.writeframes(audio_bytes)
            
            # 7. Récupérer WAV complet
            wav_data = wav_buffer.getvalue()
            
            # 8. Encoder en base64
            audio_base64 = base64.b64encode(wav_data).decode('utf-8')
            
            # 9. Calculer temps de traitement
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            # 10. Construire résultat
            result = {
                "request_id": request_id or f"tts_{int(time.time() * 1000)}",
                "audio_data": audio_base64,
                "audio_format": "wav",
                "audio_metadata": {
                    "sample_rate": self.sample_rate,
                    "channels": self.channels,
                    "sample_width": self.sample_width,
                    "duration_ms": int((len(audio_bytes) / (self.sample_rate * self.channels * self.sample_width)) * 1000)
                },
                "processing_time_ms": processing_time_ms,
                "text_length": len(text),
                "timestamp": datetime.now(UTC).isoformat()
            }
            
            return result
            
        except ConnectionRefusedError:
            raise RuntimeError(f"Cannot connect to TTS server at {self.host}:{self.port}. Is Piper running?")
        except Exception as e:
            raise RuntimeError(f"TTS synthesis failed: {e}")
    
    def synthesize_sync(
        self, 
        text: str, 
        language: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> Dict:
        """
        Version synchrone de synthesize() pour tests/scripts simples.
        
        Args:
            text: Texte à synthétiser
            language: Langue du texte
            request_id: ID de la requête
            
        Returns:
            Dict avec audio_data (base64), audio_format, audio_metadata
        """
        return asyncio.run(self.synthesize(text, language, request_id))
    
    async def synthesize_to_file(
        self, 
        text: str, 
        output_file: str, 
        language: Optional[str] = None
    ) -> None:
        """
        Synthétiser texte et sauver directement dans fichier WAV.
        Utile pour tests et debugging.
        
        Args:
            text: Texte à synthétiser
            output_file: Chemin fichier de sortie (.wav)
            language: Langue du texte
            
        Raises:
            ValueError: Si texte vide
            RuntimeError: Si erreur synthèse
        """
        result = await self.synthesize(text, language)
        
        # Décoder base64 et écrire fichier
        audio_data = base64.b64decode(result["audio_data"])
        with open(output_file, "wb") as f:
            f.write(audio_data)
        
        print(f"✅ Audio saved: {output_file} ({len(audio_data)} bytes)")
    
    async def health_check(self) -> bool:
        """
        Vérifier si le serveur Piper est accessible.
        
        Returns:
            True si serveur accessible, False sinon
        """
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port),
                timeout=2.0
            )
            writer.close()
            await writer.wait_closed()
            return True
        except Exception:
            return False
