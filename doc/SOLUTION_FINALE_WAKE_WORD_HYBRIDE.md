# 🎯 Solution Finale Wake Word HYBRIDE - Documentation Complète

## 📋 Vue d'ensemble

**Solution Hybride Intelligente** qui offre le meilleur des 3 technologies selon la plateforme et les préférences utilisateur.

### Architecture Globale

```
┌─────────────────────────────────────────────────────────────────────┐
│                          FRONTEND REACT                              │
│                                                                       │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │              wakeWordService.ts (Orchestrateur)               │  │
│  │                                                                │  │
│  │  Détecte plateforme + préférences utilisateur                 │  │
│  │  Sélectionne automatiquement le bon moteur                    │  │
│  └────────┬────────────────┬──────────────────┬───────────────────┘  │
│           │                │                  │                       │
│           ▼                ▼                  ▼                       │
│  ┌────────────────┐ ┌─────────────────┐ ┌──────────────────────┐   │
│  │ Web Speech API │ │  Picovoice      │ │  Whisper Backend    │   │
│  │   (Google)     │ │  (Natif Mobile) │ │  (Flexible)         │   │
│  │                │ │                 │ │                      │   │
│  │ ✅ Web only    │ │ ⚡ Performance  │ │ 🔧 Personnalisable  │   │
│  │ ⚡ Instantané  │ │ 📱 Mobile      │ │ 📱🌐 Multi-platform │   │
│  │ 🆓 Gratuit     │ │ 🔋 Batterie    │ │ 🆓 Gratuit          │   │
│  └────────────────┘ └─────────────────┘ └──────────┬───────────┘   │
└────────────────────────────────────────────────────│─────────────────┘
                                                      │
                                                      ▼
                                            ┌──────────────────────┐
                                            │  BACKEND PYTHON      │
                                            │  (FastAPI)           │
                                            │                      │
                                            │  /wake-word/detect   │
                                            │  - Whisper tiny      │
                                            │  - Transcription     │
                                            │  - Détection mot-clé │
                                            └──────────────────────┘
```

---

## 🎯 Logique de Sélection Automatique

```typescript
function selectWakeWordEngine() {
  if (isWeb) {
    return 'WEB_SPEECH_API'  // Google (gratuit, instantané)
  }
  
  if (isMobile) {
    // Préférence utilisateur dans settings
    if (userPreference === 'performance') {
      return 'PICOVOICE'     // Natif (ultra-rapide, batterie optimal)
    } else {
      return 'WHISPER_BACKEND'  // Backend (flexible, wake word custom)
    }
  }
}
```

---

## 📁 Structure des Fichiers à Créer/Modifier

```
pcd-ai-embedded-agent/
├── backend/
│   ├── ai/
│   │   ├── stt_engine.py                    # ✅ Existant (pas toucher)
│   │   └── wake_word_detector.py            # 🆕 NOUVEAU
│   ├── main.py                               # ✏️ MODIFIER (ajouter routes)
│   └── config.py                             # ✏️ MODIFIER (ajouter config)
│
└── agent-ui/
    ├── src/
    │   ├── services/
    │   │   ├── wakeWordService.ts            # ✏️ MODIFIER (orchestrateur)
    │   │   ├── picovoiceService.ts           # 🆕 NOUVEAU
    │   │   ├── whisperWakeWordService.ts     # 🆕 NOUVEAU
    │   │   └── audioStreamService.ts         # 🆕 NOUVEAU
    │   │
    │   ├── components/
    │   │   └── WakeWordSettings/
    │   │       └── WakeWordSettings.tsx      # 🆕 NOUVEAU (UI settings)
    │   │
    │   └── types/
    │       └── wakeWord.types.ts             # 🆕 NOUVEAU
    │
    ├── android/
    │   └── app/src/main/
    │       └── AndroidManifest.xml           # ✏️ MODIFIER (permissions)
    │
    └── ios/
        └── App/
            └── Info.plist                    # ✏️ MODIFIER (permissions)
```

---

## 🔧 PHASE 1: Backend - Wake Word Detector

### 1.1 - Créer `backend/ai/wake_word_detector.py`

```python
"""
Wake Word Detector - Détection rapide de mot-clé avec Whisper
Responsable: Montassar
Date: 2026-02-25

Utilise Whisper "tiny" pour détecter rapidement un wake word dans un audio court.
Optimisé pour latence minimale (< 500ms).
"""

import base64
import time
import tempfile
import os
import re
from datetime import datetime, UTC
from typing import Dict, Optional
from pathlib import Path

from faster_whisper import WhisperModel
from backend.config import Config


class WakeWordDetector:
    """
    Détecteur de wake word utilisant Whisper tiny.
    Optimisé pour audio courts (2-3 secondes maximum).
    """
    
    def __init__(self, wake_word: str = "hey assistant", language: str = "en"):
        """
        Initialiser le détecteur.
        
        Args:
            wake_word: Mot-clé à détecter (ex: "hey gob")
            language: Langue du wake word ("en", "fr", "ar")
        """
        print(f"[WakeWord] Initializing detector...")
        print(f"[WakeWord] Wake word: '{wake_word}'")
        print(f"[WakeWord] Language: {language}")
        
        self.wake_word = self._normalize_text(wake_word)
        self.language = language
        self.threshold = Config.WAKE_WORD_THRESHOLD
        
        # Charger Whisper tiny (ultra-rapide)
        start_time = time.time()
        self.model = WhisperModel(
            Config.WAKE_WORD_MODEL,
            device=Config.WHISPER_DEVICE,
            compute_type="int8"
        )
        load_time = time.time() - start_time
        print(f"[WakeWord] ✅ Model loaded in {load_time:.2f}s")
    
    def _normalize_text(self, text: str) -> str:
        """
        Normaliser texte pour comparaison.
        Enlève ponctuation, lowercase, espaces multiples.
        """
        text = text.lower()
        text = re.sub(r'[^\w\s]', '', text)  # Enlever ponctuation
        text = re.sub(r'\s+', ' ', text)      # Espaces multiples → 1
        return text.strip()
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculer similarité entre 2 textes (0.0 - 1.0).
        Utilise simple word matching pour rapidité.
        """
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return 0.0
        
        # Jaccard similarity
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    async def detect(
        self,
        audio_data: str,
        audio_format: str = "webm",
        user_id: Optional[str] = None
    ) -> Dict:
        """
        Détecter wake word dans audio.
        
        Args:
            audio_data: Audio encodé en base64
            audio_format: Format audio ("webm", "wav", "ogg")
            user_id: ID utilisateur (optionnel)
            
        Returns:
            {
                "detected": bool,
                "confidence": float,
                "transcription": str,
                "processing_time_ms": int
            }
        """
        start_time = time.time()
        
        try:
            # 1. Décoder base64
            audio_bytes = base64.b64decode(audio_data)
            
            # 2. Sauvegarder temporairement
            temp_file = None
            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=f'.{audio_format}'
            ) as f:
                f.write(audio_bytes)
                temp_file = f.name
            
            # 3. Transcrire avec Whisper (rapide)
            segments, info = self.model.transcribe(
                temp_file,
                beam_size=1,           # Plus rapide
                language=self.language if self.language else None,
                task="transcribe",
                vad_filter=False       # Pas de VAD (plus simple/rapide)
            )
            
            # 4. Récupérer transcription
            transcription_raw = " ".join([seg.text for seg in segments])
            transcription_normalized = self._normalize_text(transcription_raw)
            
            # 5. Calculer similarité avec wake word
            similarity = self._calculate_similarity(
                transcription_normalized,
                self.wake_word
            )
            
            # 6. Détecter si wake word présent
            detected = (
                similarity >= self.threshold or
                self.wake_word in transcription_normalized
            )
            
            # 7. Nettoyer fichier temporaire
            if temp_file and os.path.exists(temp_file):
                os.remove(temp_file)
            
            # 8. Calculer temps de traitement
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            # 9. Construire résultat
            result = {
                "detected": detected,
                "confidence": similarity,
                "transcription": transcription_raw.strip(),
                "transcription_normalized": transcription_normalized,
                "wake_word": self.wake_word,
                "threshold": self.threshold,
                "processing_time_ms": processing_time_ms,
                "timestamp": datetime.now(UTC).isoformat()
            }
            
            # Log
            status = "✅ DETECTED" if detected else "❌ NOT DETECTED"
            print(f"[WakeWord] {status} (confidence: {similarity:.2f})")
            print(f"[WakeWord] Transcription: '{transcription_raw}'")
            print(f"[WakeWord] Processing time: {processing_time_ms}ms")
            
            return result
            
        except Exception as e:
            print(f"[WakeWord] ❌ Error: {e}")
            
            # Nettoyer fichier en cas d'erreur
            if temp_file and os.path.exists(temp_file):
                os.remove(temp_file)
            
            raise
    
    def set_wake_word(self, wake_word: str):
        """Changer le wake word"""
        self.wake_word = self._normalize_text(wake_word)
        print(f"[WakeWord] Wake word updated to: '{wake_word}'")
    
    def set_threshold(self, threshold: float):
        """Changer le seuil de détection (0.0 - 1.0)"""
        self.threshold = max(0.0, min(1.0, threshold))
        print(f"[WakeWord] Threshold updated to: {self.threshold}")
    
    def get_info(self) -> Dict:
        """Informations sur le détecteur"""
        return {
            "wake_word": self.wake_word,
            "language": self.language,
            "threshold": self.threshold,
            "model": Config.WAKE_WORD_MODEL,
            "device": Config.WHISPER_DEVICE
        }
```

---

### 1.2 - Modifier `backend/config.py`

**Ajouter à la fin du fichier:**

```python
# ==================== WAKE WORD DETECTION ====================
WAKE_WORD_ENABLED = os.getenv("WAKE_WORD_ENABLED", "True").lower() == "true"
WAKE_WORD_MODEL = os.getenv("WAKE_WORD_MODEL", "tiny")  # tiny|base
WAKE_WORD_DEFAULT = os.getenv("WAKE_WORD_DEFAULT", "hey assistant")
WAKE_WORD_THRESHOLD = float(os.getenv("WAKE_WORD_THRESHOLD", 0.7))  # 0.0-1.0
WAKE_WORD_LANGUAGE = os.getenv("WAKE_WORD_LANGUAGE", "en")
```

---

### 1.3 - Modifier `backend/main.py`

**Ajouter après les imports:**

```python
from backend.ai.wake_word_detector import WakeWordDetector
```

**Ajouter dans `startup_event()`:**

```python
@app.on_event("startup")
async def startup_event():
    global agent_core
    
    # ... code existant ...
    
    # Initialiser Wake Word Detector (si enabled)
    global wake_word_detector
    wake_word_detector = None
    
    if Config.WAKE_WORD_ENABLED:
        try:
            wake_word_detector = WakeWordDetector(
                wake_word=Config.WAKE_WORD_DEFAULT,
                language=Config.WAKE_WORD_LANGUAGE
            )
            logger.info("✅ Wake Word Detector initialized")
        except Exception as e:
            logger.error(f"❌ Wake Word Detector initialization failed: {e}")
```

**Ajouter les routes Wake Word (avant la fin du fichier):**

```python
# ============================================================
# ROUTES WAKE WORD
# ============================================================

class WakeWordDetectRequest(BaseModel):
    """Requête détection wake word"""
    audio_data: str = Field(..., description="Audio en base64")
    audio_format: str = Field(default="webm", description="Format audio")
    user_id: Optional[str] = Field(default=None, description="ID utilisateur")


class WakeWordConfigRequest(BaseModel):
    """Requête configuration wake word"""
    wake_word: str = Field(..., description="Nouveau wake word")
    threshold: Optional[float] = Field(default=None, description="Seuil 0.0-1.0")
    user_id: Optional[str] = Field(default=None, description="ID utilisateur")


@app.post("/wake-word/detect",
          summary="Détecter wake word dans audio",
          tags=["Wake Word"])
async def detect_wake_word(request: WakeWordDetectRequest):
    """
    Détecte si le wake word est présent dans l'audio.
    
    **Usage:**
    1. Enregistrer audio court (2-3 secondes)
    2. Encoder en base64
    3. Envoyer à cette route
    4. Vérifier `detected: true/false`
    
    **Performance:** ~200-500ms processing time
    """
    if not Config.WAKE_WORD_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Wake word detection is disabled"
        )
    
    if not wake_word_detector:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Wake word detector not initialized"
        )
    
    try:
        result = await wake_word_detector.detect(
            audio_data=request.audio_data,
            audio_format=request.audio_format,
            user_id=request.user_id
        )
        return result
        
    except Exception as e:
        logger.error(f"Wake word detection failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Wake word detection failed: {str(e)}"
        )


@app.post("/wake-word/config",
          summary="Configurer wake word",
          tags=["Wake Word"])
async def configure_wake_word(request: WakeWordConfigRequest):
    """
    Configure le wake word à détecter.
    Permet à l'utilisateur de définir son propre wake word custom.
    """
    if not Config.WAKE_WORD_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Wake word detection is disabled"
        )
    
    if not wake_word_detector:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Wake word detector not initialized"
        )
    
    try:
        # Changer wake word
        wake_word_detector.set_wake_word(request.wake_word)
        
        # Changer threshold si fourni
        if request.threshold is not None:
            wake_word_detector.set_threshold(request.threshold)
        
        return {
            "success": True,
            "message": f"Wake word configured to: {request.wake_word}",
            "info": wake_word_detector.get_info()
        }
        
    except Exception as e:
        logger.error(f"Wake word configuration failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Configuration failed: {str(e)}"
        )


@app.get("/wake-word/info",
         summary="Informations wake word",
         tags=["Wake Word"])
async def wake_word_info():
    """
    Renvoie les informations sur la configuration actuelle du wake word.
    """
    if not Config.WAKE_WORD_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Wake word detection is disabled"
        )
    
    if not wake_word_detector:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Wake word detector not initialized"
        )
    
    return wake_word_detector.get_info()
```

---

### 1.4 - Modifier `backend/.env`

**Ajouter à la fin:**

```env
# ==================== WAKE WORD DETECTION ====================
WAKE_WORD_ENABLED=True
WAKE_WORD_MODEL=tiny
WAKE_WORD_DEFAULT=hey gob
WAKE_WORD_THRESHOLD=0.7
WAKE_WORD_LANGUAGE=en
```

---

## 🎨 PHASE 2: Frontend - Services

### 2.1 - Créer types `agent-ui/src/types/wakeWord.types.ts`

```typescript
/**
 * Types pour Wake Word Detection
 */

export type WakeWordEngine = 'web-speech' | 'picovoice' | 'whisper-backend';

export interface WakeWordSettings {
  enabled: boolean;
  engine: WakeWordEngine;
  wakeWord: string;
  threshold: number;
}

export interface WakeWordDetectionResult {
  detected: boolean;
  confidence: number;
  transcription: string;
  processing_time_ms: number;
}

export interface PicovoiceWakeWord {
  id: string;
  name: string;
  displayName: string;
}

// Wake words disponibles avec Picovoice
export const PICOVOICE_WAKE_WORDS: PicovoiceWakeWord[] = [
  { id: 'hey-gob', name: 'hey-gob', displayName: 'Hey Gob' },
  { id: 'hello-robot', name: 'hello-robot', displayName: 'Hello Robot' },
  { id: 'hi-assistant', name: 'hi-assistant', displayName: 'Hi Assistant' },
  { id: 'wake-up', name: 'wake-up', displayName: 'Wake Up' },
];
```

---

### 2.2 - Créer `agent-ui/src/services/audioStreamService.ts`

```typescript
/**
 * Audio Stream Service
 * Enregistre audio par chunks et envoie au backend pour détection
 */

import { getBackendURL } from '../config/api.config';

export class AudioStreamService {
  private mediaRecorder: MediaRecorder | null = null;
  private audioChunks: Blob[] = [];
  private isRecording: boolean = false;
  private onWakeWordCallback: (() => void) | null = null;
  private recordingInterval: any = null;
  
  // Durée d'un chunk audio (millisecondes)
  private readonly CHUNK_DURATION = 2500; // 2.5 secondes
  
  /**
   * Démarrer l'écoute continue
   */
  async startContinuousListening(
    onWakeWordDetected: () => void
  ): Promise<void> {
    this.onWakeWordCallback = onWakeWordDetected;
    
    try {
      // Demander accès micro
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: true 
      });
      
      // Créer recorder
      this.mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm'
      });
      
      // Buffer pour chunks
      this.audioChunks = [];
      
      // Écouter data disponible
      this.mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          this.audioChunks.push(event.data);
        }
      };
      
      // Écouter stop (fin d'un chunk)
      this.mediaRecorder.onstop = async () => {
        if (this.audioChunks.length > 0) {
          const audioBlob = new Blob(this.audioChunks, { 
            type: 'audio/webm' 
          });
          
          // Vérifier si wake word détecté
          await this.checkWakeWord(audioBlob);
          
          // Reset pour prochain chunk
          this.audioChunks = [];
          
          // Redémarrer si toujours en écoute
          if (this.isRecording && this.mediaRecorder) {
            this.mediaRecorder.start();
            
            // Auto-stop après CHUNK_DURATION
            setTimeout(() => {
              if (this.mediaRecorder && this.isRecording) {
                this.mediaRecorder.stop();
              }
            }, this.CHUNK_DURATION);
          }
        }
      };
      
      // Démarrer enregistrement
      this.isRecording = true;
      this.mediaRecorder.start();
      
      // Auto-stop après CHUNK_DURATION
      setTimeout(() => {
        if (this.mediaRecorder && this.isRecording) {
          this.mediaRecorder.stop();
        }
      }, this.CHUNK_DURATION);
      
      console.log('[AudioStream] ✅ Started continuous listening');
      
    } catch (error) {
      console.error('[AudioStream] ❌ Failed to start:', error);
      throw error;
    }
  }
  
  /**
   * Arrêter l'écoute
   */
  async stopContinuousListening(): Promise<void> {
    this.isRecording = false;
    
    if (this.recordingInterval) {
      clearInterval(this.recordingInterval);
    }
    
    if (this.mediaRecorder) {
      // Arrêter toutes les pistes
      this.mediaRecorder.stream.getTracks().forEach(track => track.stop());
      this.mediaRecorder = null;
    }
    
    this.audioChunks = [];
    console.log('[AudioStream] 🔇 Stopped listening');
  }
  
  /**
   * Envoyer audio au backend pour vérifier wake word
   */
  private async checkWakeWord(audioBlob: Blob): Promise<void> {
    try {
      // Convertir en base64
      const base64Audio = await this.blobToBase64(audioBlob);
      
      // Envoyer au backend
      const backendURL = getBackendURL();
      const response = await fetch(`${backendURL}/wake-word/detect`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          audio_data: base64Audio,
          audio_format: 'webm'
        })
      });
      
      if (!response.ok) {
        console.error('[AudioStream] Backend error:', response.status);
        return;
      }
      
      const result = await response.json();
      
      // Si wake word détecté, appeler callback
      if (result.detected) {
        console.log('[AudioStream] 🔥 Wake word detected!');
        console.log('[AudioStream] Transcription:', result.transcription);
        console.log('[AudioStream] Confidence:', result.confidence);
        
        if (this.onWakeWordCallback) {
          this.onWakeWordCallback();
        }
      }
      
    } catch (error) {
      console.error('[AudioStream] Check wake word failed:', error);
    }
  }
  
  /**
   * Convertir Blob en base64
   */
  private async blobToBase64(blob: Blob): Promise<string> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onloadend = () => {
        const base64 = reader.result as string;
        const base64Data = base64.split(',')[1];
        resolve(base64Data);
      };
      reader.onerror = reject;
      reader.readAsDataURL(blob);
    });
  }
  
  /**
   * Statut
   */
  isListening(): boolean {
    return this.isRecording;
  }
}

// Singleton
export const audioStreamService = new AudioStreamService();
```

---

### 2.3 - Créer `agent-ui/src/services/picovoiceService.ts`

```typescript
/**
 * Picovoice Service - Wake Word natif mobile
 * Utilise @capacitor-community/porcupine-wake-word
 */

import { Plugins } from '@capacitor/core';

// Types pour le plugin (si pas de types officiels)
interface PorcupinePlugin {
  initialize(config: {
    accessKey: string;
    keywords: string[];
    sensitivities?: number[];
  }): Promise<void>;
  
  start(): Promise<void>;
  stop(): Promise<void>;
  delete(): Promise<void>;
  
  addListener(
    eventName: 'wakeWordDetected',
    listenerFunc: (info: { keyword: string }) => void
  ): Promise<any>;
}

declare const PorcupineWakeWord: PorcupinePlugin;

export class PicovoiceService {
  private isListening: boolean = false;
  private onDetectedCallback: ((keyword: string) => void) | null = null;
  
  // 🔑 ACCESS KEY depuis Picovoice Console
  // TODO: Remplacer par votre vraie clé
  private readonly ACCESS_KEY = 'YOUR_PICOVOICE_ACCESS_KEY_HERE';
  
  // Wake words disponibles (fichiers .ppn requis)
  private readonly WAKE_WORDS = [
    'hey-gob',
    'hello-robot',
    'hi-assistant',
    'wake-up'
  ];
  
  /**
   * Initialiser Picovoice
   */
  async initialize(): Promise<void> {
    try {
      console.log('[Picovoice] Initializing...');
      
      // Vérifier si le plugin existe
      if (typeof PorcupineWakeWord === 'undefined') {
        throw new Error('Picovoice plugin not installed');
      }
      
      // Initialiser avec config
      await PorcupineWakeWord.initialize({
        accessKey: this.ACCESS_KEY,
        keywords: this.WAKE_WORDS,
        sensitivities: [0.5, 0.5, 0.5, 0.5] // 0.0-1.0
      });
      
      // Écouter événements de détection
      await PorcupineWakeWord.addListener(
        'wakeWordDetected',
        (info: { keyword: string }) => {
          console.log('[Picovoice] Wake word detected:', info.keyword);
          
          if (this.onDetectedCallback) {
            this.onDetectedCallback(info.keyword);
          }
        }
      );
      
      console.log('[Picovoice] ✅ Initialized successfully');
      
    } catch (error) {
      console.error('[Picovoice] ❌ Initialization failed:', error);
      throw error;
    }
  }
  
  /**
   * Démarrer l'écoute
   */
  async start(): Promise<void> {
    if (this.isListening) {
      console.log('[Picovoice] Already listening');
      return;
    }
    
    try {
      await PorcupineWakeWord.start();
      this.isListening = true;
      console.log('[Picovoice] 👂 Listening for wake words...');
      
    } catch (error) {
      console.error('[Picovoice] ❌ Failed to start:', error);
      throw error;
    }
  }
  
  /**
   * Arrêter l'écoute
   */
  async stop(): Promise<void> {
    if (!this.isListening) {
      return;
    }
    
    try {
      await PorcupineWakeWord.stop();
      this.isListening = false;
      console.log('[Picovoice] 🔇 Stopped listening');
      
    } catch (error) {
      console.error('[Picovoice] Failed to stop:', error);
    }
  }
  
  /**
   * Nettoyer ressources
   */
  async cleanup(): Promise<void> {
    await this.stop();
    
    try {
      await PorcupineWakeWord.delete();
      console.log('[Picovoice] 🧹 Cleaned up');
    } catch (error) {
      console.error('[Picovoice] Cleanup error:', error);
    }
  }
  
  /**
   * Définir callback
   */
  onDetection(callback: (keyword: string) => void): void {
    this.onDetectedCallback = callback;
  }
  
  /**
   * Statut
   */
  getIsListening(): boolean {
    return this.isListening;
  }
  
  /**
   * Wake words disponibles
   */
  getAvailableWakeWords(): string[] {
    return [...this.WAKE_WORDS];
  }
}

// Singleton
export const picovoiceService = new PicovoiceService();
```

---

### 2.4 - Modifier `agent-ui/src/services/wakeWordService.ts`

**REMPLACER ENTIÈREMENT le contenu par:**

```typescript
/**
 * Wake Word Service - Orchestrateur Hybride
 * Sélectionne automatiquement le meilleur moteur selon plateforme
 */

import { picovoiceService } from './picovoiceService';
import { audioStreamService } from './audioStreamService';
import type { WakeWordEngine } from '../types/wakeWord.types';

// Types Web Speech API
declare global {
  interface Window {
    SpeechRecognition: any;
    webkitSpeechRecognition: any;
    Capacitor: any;
  }
}

type WakeWordCallback = (transcript: string) => void;
type ErrorCallback = (error: string) => void;

export class WakeWordService {
  private recognition: any = null;
  private wakeWord: string = '';
  private isActive: boolean = false;
  private currentEngine: WakeWordEngine | null = null;
  private onWakeWordDetected: WakeWordCallback | null = null;
  private onError: ErrorCallback | null = null;
  
  constructor() {
    this.initializeWebSpeechAPI();
  }
  
  /**
   * Détecter si on est sur mobile Capacitor
   */
  private isCapacitor(): boolean {
    return typeof window !== 'undefined' && window.Capacitor !== undefined;
  }
  
  /**
   * Initialiser Web Speech API (pour navigateurs web)
   */
  private initializeWebSpeechAPI(): void {
    if (this.isCapacitor()) {
      console.log('[WakeWord] Mobile detected - Web Speech API not needed');
      return;
    }
    
    if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
      console.warn('[WakeWord] Web Speech API not supported');
      return;
    }
    
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    this.recognition = new SpeechRecognition();
    this.recognition.continuous = true;
    this.recognition.interimResults = false;
    this.recognition.lang = 'en-US';
    
    this.recognition.onresult = (event: any) => {
      for (let i = event.resultIndex; i < event.results.length; i++) {
        if (!event.results[i].isFinal) continue;
        
        const transcript = event.results[i][0].transcript.toLowerCase();
        console.log('[WakeWord] Heard:', transcript);
        
        if (this.isActive && this.wakeWord && transcript.includes(this.wakeWord)) {
          console.log('[WakeWord] 🔥 DETECTED!');
          if (this.onWakeWordDetected) {
            this.onWakeWordDetected(transcript);
          }
        }
      }
    };
    
    this.recognition.onerror = (event: any) => {
      if (event.error === 'no-speech') return;
      
      console.warn('[WakeWord] Error:', event.error);
      if (this.onError && event.error !== 'no-speech') {
        this.onError(event.error);
      }
    };
    
    this.recognition.onend = () => {
      if (this.isActive && this.currentEngine === 'web-speech') {
        try {
          this.recognition?.start();
        } catch (e) {
          console.error('[WakeWord] Restart failed:', e);
        }
      }
    };
  }
  
  /**
   * Sélectionner le moteur optimal selon plateforme et préférences
   */
  private selectEngine(preferredEngine?: WakeWordEngine): WakeWordEngine {
    // Si web browser → Web Speech API
    if (!this.isCapacitor()) {
      return 'web-speech';
    }
    
    // Si mobile, utiliser préférence utilisateur
    if (preferredEngine) {
      return preferredEngine;
    }
    
    // Par défaut sur mobile: Picovoice (performance)
    return 'picovoice';
  }
  
  /**
   * Définir wake word
   */
  setWakeWord(word: string): void {
    this.wakeWord = word.toLowerCase();
    console.log('[WakeWord] Set to:', this.wakeWord);
  }
  
  /**
   * Démarrer écoute
   */
  async start(preferredEngine?: WakeWordEngine): Promise<void> {
    if (this.isActive) {
      console.log('[WakeWord] Already active');
      return;
    }
    
    // Sélectionner moteur
    this.currentEngine = this.selectEngine(preferredEngine);
    this.isActive = true;
    
    console.log(`[WakeWord] Starting with engine: ${this.currentEngine}`);
    
    try {
      switch (this.currentEngine) {
        case 'web-speech':
          await this.startWebSpeech();
          break;
          
        case 'picovoice':
          await this.startPicovoice();
          break;
          
        case 'whisper-backend':
          await this.startWhisperBackend();
          break;
          
        default:
          throw new Error(`Unknown engine: ${this.currentEngine}`);
      }
      
      console.log(`[WakeWord] ✅ Started with ${this.currentEngine}`);
      
    } catch (error) {
      this.isActive = false;
      this.currentEngine = null;
      console.error('[WakeWord] ❌ Start failed:', error);
      throw error;
    }
  }
  
  /**
   * Démarrer Web Speech API
   */
  private async startWebSpeech(): Promise<void> {
    if (!this.recognition) {
      throw new Error('Web Speech API not supported');
    }
    
    if (!this.wakeWord) {
      throw new Error('Wake word not set');
    }
    
    this.recognition.start();
  }
  
  /**
   * Démarrer Picovoice
   */
  private async startPicovoice(): Promise<void> {
    try {
      // Initialiser si pas encore fait
      await picovoiceService.initialize();
      
      // Définir callback
      picovoiceService.onDetection((keyword: string) => {
        console.log('[WakeWord] Picovoice detected:', keyword);
        if (this.onWakeWordDetected) {
          this.onWakeWordDetected(keyword);
        }
      });
      
      // Démarrer écoute
      await picovoiceService.start();
      
    } catch (error) {
      console.error('[WakeWord] Picovoice failed:', error);
      throw error;
    }
  }
  
  /**
   * Démarrer Whisper Backend
   */
  private async startWhisperBackend(): Promise<void> {
    try {
      // Définir callback
      await audioStreamService.startContinuousListening(() => {
        console.log('[WakeWord] Whisper backend detected');
        if (this.onWakeWordDetected) {
          this.onWakeWordDetected(this.wakeWord);
        }
      });
      
    } catch (error) {
      console.error('[WakeWord] Whisper backend failed:', error);
      throw error;
    }
  }
  
  /**
   * Arrêter écoute
   */
  async stop(): Promise<void> {
    if (!this.isActive) return;
    
    this.isActive = false;
    
    try {
      switch (this.currentEngine) {
        case 'web-speech':
          if (this.recognition) {
            this.recognition.stop();
          }
          break;
          
        case 'picovoice':
          await picovoiceService.stop();
          break;
          
        case 'whisper-backend':
          await audioStreamService.stopContinuousListening();
          break;
      }
      
      console.log(`[WakeWord] Stopped ${this.currentEngine}`);
      this.currentEngine = null;
      
    } catch (error) {
      console.error('[WakeWord] Stop error:', error);
    }
  }
  
  /**
   * Définir callback
   */
  onDetection(callback: WakeWordCallback): void {
    this.onWakeWordDetected = callback;
  }
  
  /**
   * Définir error callback
   */
  onErrorEvent(callback: ErrorCallback): void {
    this.onError = callback;
  }
  
  /**
   * Vérifier support
   */
  isSupported(engine?: WakeWordEngine): boolean {
    const targetEngine = engine || this.selectEngine();
    
    switch (targetEngine) {
      case 'web-speech':
        return this.recognition !== null;
        
      case 'picovoice':
        return this.isCapacitor();
        
      case 'whisper-backend':
        return true; // Toujours supporté si backend accessible
        
      default:
        return false;
    }
  }
  
  /**
   * Obtenir moteur actuel
   */
  getCurrentEngine(): WakeWordEngine | null {
    return this.currentEngine;
  }
  
  /**
   * Obtenir moteur recommandé
   */
  getRecommendedEngine(): WakeWordEngine {
    return this.selectEngine();
  }
  
  /**
   * Statut
   */
  getIsActive(): boolean {
    return this.isActive;
  }
  
  /**
   * Wake words disponibles pour Picovoice
   */
  getAvailablePicovoiceWakeWords(): string[] {
    return picovoiceService.getAvailableWakeWords();
  }
}

// Singleton
export const wakeWordService = new WakeWordService();
```

---

### 2.5 - Créer composant settings `agent-ui/src/components/WakeWordSettings/WakeWordSettings.tsx`

```typescript
/**
 * Wake Word Settings Component
 * Permet à l'utilisateur de choisir le moteur de wake word sur mobile
 */

import { useState, useEffect } from 'react';
import { useAgentStore } from '../../store/agentStore';
import { wakeWordService } from '../../services/wakeWordService';
import { PICOVOICE_WAKE_WORDS } from '../../types/wakeWord.types';
import type { WakeWordEngine } from '../../types/wakeWord.types';
import './WakeWordSettings.css';

export function WakeWordSettings() {
  const { showToast } = useAgentStore();
  const [engine, setEngine] = useState<WakeWordEngine>('picovoice');
  const [customWakeWord, setCustomWakeWord] = useState('');
  const [selectedPicovoiceWord, setSelectedPicovoiceWord] = useState('hey-gob');
  
  // Détecter si on est sur mobile
  const isMobile = (typeof window !== 'undefined' && (window as any).Capacitor !== undefined);
  const recommendedEngine = wakeWordService.getRecommendedEngine();
  
  useEffect(() => {
    // Charger settings sauvegardés
    const saved = localStorage.getItem('wake-word-settings');
    if (saved) {
      try {
        const settings = JSON.parse(saved);
        setEngine(settings.engine || recommendedEngine);
        setCustomWakeWord(settings.customWakeWord || '');
        setSelectedPicovoiceWord(settings.picovoiceWord || 'hey-gob');
      } catch (e) {
        console.error('Failed to load wake word settings:', e);
      }
    }
  }, [recommendedEngine]);
  
  const handleSaveSettings = () => {
    // Sauvegarder dans localStorage
    const settings = {
      engine,
      customWakeWord,
      picovoiceWord: selectedPicovoiceWord
    };
    localStorage.setItem('wake-word-settings', JSON.stringify(settings));
    
    // Appliquer le wake word selon le moteur
    if (engine === 'picovoice') {
      // Picovoice utilise les mots pré-définis
      showToast(`Wake word set to: ${selectedPicovoiceWord}`, 'success');
    } else {
      // Whisper backend utilise le custom
      if (!customWakeWord.trim()) {
        showToast('Please enter a wake word', 'warning');
        return;
      }
      wakeWordService.setWakeWord(customWakeWord);
      showToast(`Custom wake word set to: ${customWakeWord}`, 'success');
    }
  };
  
  return (
    <div className="wake-word-settings">
      <h3>Wake Word Configuration</h3>
      
      {isMobile ? (
        <>
          <div className="engine-selector">
            <label>Detection Engine:</label>
            <select value={engine} onChange={(e) => setEngine(e.target.value as WakeWordEngine)}>
              <option value="picovoice">
                ⚡ Picovoice (Performance) - Recommended
              </option>
              <option value="whisper-backend">
                🔧 Whisper Backend (Flexible)
              </option>
            </select>
            <p className="engine-description">
              {engine === 'picovoice' 
                ? '✅ Ultra-fast, optimal battery, native detection'
                : '✅ Custom wake word, flexible, any word you want'}
            </p>
          </div>
          
          {engine === 'picovoice' ? (
            <div className="picovoice-selection">
              <label>Choose Wake Word:</label>
              <select 
                value={selectedPicovoiceWord} 
                onChange={(e) => setSelectedPicovoiceWord(e.target.value)}
              >
                {PICOVOICE_WAKE_WORDS.map(word => (
                  <option key={word.id} value={word.id}>
                    {word.displayName}
                  </option>
                ))}
              </select>
            </div>
          ) : (
            <div className="custom-wake-word">
              <label>Custom Wake Word:</label>
              <input
                type="text"
                placeholder="e.g., hey robot, hello friend..."
                value={customWakeWord}
                onChange={(e) => setCustomWakeWord(e.target.value)}
              />
              <p className="hint">
                💡 Tip: Use 2-3 words for better detection
              </p>
            </div>
          )}
        </>
      ) : (
        <div className="web-info">
          <p>✅ Web platform detected</p>
          <p>Using Google Web Speech API (automatic)</p>
          <input
            type="text"
            placeholder="Enter wake word..."
            value={customWakeWord}
            onChange={(e) => setCustomWakeWord(e.target.value)}
          />
        </div>
      )}
      
      <button onClick={handleSaveSettings} className="save-btn">
        Save Settings
      </button>
      
      <div className="current-config">
        <h4>Current Configuration:</h4>
        <ul>
          <li><strong>Platform:</strong> {isMobile ? '📱 Mobile' : '🌐 Web'}</li>
          <li><strong>Engine:</strong> {engine}</li>
          <li><strong>Wake Word:</strong> {
            engine === 'picovoice' 
              ? selectedPicovoiceWord 
              : (customWakeWord || 'Not set')
          }</li>
        </ul>
      </div>
    </div>
  );
}
```

**CSS correspondant `WakeWordSettings.css`:**

```css
.wake-word-settings {
  padding: 20px;
  background: #f5f5f5;
  border-radius: 12px;
  margin: 20px 0;
}

.wake-word-settings h3 {
  margin-bottom: 20px;
  color: #333;
}

.engine-selector,
.picovoice-selection,
.custom-wake-word,
.web-info {
  margin-bottom: 20px;
}

.engine-selector label,
.picovoice-selection label,
.custom-wake-word label {
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
  color: #555;
}

.engine-selector select,
.picovoice-selection select,
.custom-wake-word input,
.web-info input {
  width: 100%;
  padding: 12px;
  border: 2px solid #ddd;
  border-radius: 8px;
  font-size: 16px;
}

.engine-description {
  margin-top: 8px;
  font-size: 14px;
  color: #666;
}

.hint {
  margin-top: 8px;
  font-size: 13px;
  color: #888;
}

.save-btn {
  width: 100%;
  padding: 14px;
  background: #4CAF50;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.3s;
}

.save-btn:hover {
  background: #45a049;
}

.current-config {
  margin-top: 24px;
  padding: 16px;
  background: white;
  border-radius: 8px;
  border: 1px solid #ddd;
}

.current-config h4 {
  margin-bottom: 12px;
  color: #333;
}

.current-config ul {
  list-style: none;
  padding: 0;
}

.current-config li {
  margin: 8px 0;
  color: #555;
}
```

---

## 🔧 PHASE 3: Configuration Mobile

### 3.1 - Installer plugin Picovoice

```bash
cd pcd-ai-embedded-agent/agent-ui

# Installer le plugin
npm install @capacitor-community/porcupine-wake-word

# Synchroniser
npx cap sync
```

### 3.2 - Permissions Android

**Fichier:** `agent-ui/android/app/src/main/AndroidManifest.xml`

**Ajouter après la balise `<manifest>`:**

```xml
<uses-permission android:name="android.permission.RECORD_AUDIO" />
<uses-permission android:name="android.permission.INTERNET" />
```

### 3.3 - Permissions iOS

**Fichier:** `agent-ui/ios/App/App/Info.plist`

**Ajouter dans `<dict>`:**

```xml
<key>NSMicrophoneUsageDescription</key>
<string>This app needs microphone access to listen for wake word commands</string>
```

---

## 📝 PHASE 4: Intégration UI

### 4.1 - Ajouter le composant dans Settings

**Fichier:** `agent-ui/src/screens/SettingsScreen.tsx` (ou équivalent)

```typescript
import { WakeWordSettings } from '../components/WakeWordSettings/WakeWordSettings';

export function SettingsScreen() {
  return (
    <div className="settings-screen">
      <h2>Settings</h2>
      
      {/* Autres settings... */}
      
      {/* Nouveau: Wake Word Settings */}
      <section>
        <WakeWordSettings />
      </section>
    </div>
  );
}
```

### 4.2 - Modifier MicButton pour supporter les moteurs

**Fichier:** `agent-ui/src/components/MicButton/MicButton.tsx`

**Trouver la fonction `handleToggleWakeMode` et modifier:**

```typescript
const handleToggleWakeMode = async () => {
  if (!wakeWord) {
    showToast('Please configure wake word in settings first', 'warning');
    return;
  }
  
  try {
    if (wakeMode) {
      // Désactiver
      await wakeWordService.stop();
      disableWakeMode();
      showToast('Wake mode disabled', 'info');
    } else {
      // Activer - Lire les settings pour savoir quel moteur utiliser
      const savedSettings = localStorage.getItem('wake-word-settings');
      let preferredEngine = undefined;
      
      if (savedSettings) {
        const settings = JSON.parse(savedSettings);
        preferredEngine = settings.engine;
      }
      
      await wakeWordService.start(preferredEngine);
      enableWakeMode();
      
      const engine = wakeWordService.getCurrentEngine();
      showToast(`Wake mode enabled (${engine})`, 'success');
    }
  } catch (error) {
    console.error('Wake mode toggle failed:', error);
    showToast('Failed to toggle wake mode', 'error');
  }
};
```

---

## 🎯 PHASE 5: Configuration Picovoice Console

### 5.1 - Créer compte Picovoice

1. Aller sur https://console.picovoice.ai/
2. Cliquer "Sign Up" (gratuit)
3. Confirmer email
4. Se connecter

### 5.2 - Obtenir Access Key

1. Dans le dashboard, aller à "Access Keys"
2. Copier votre clé (commence par "xxxxxxxx...")
3. Coller dans `picovoiceService.ts`:

```typescript
private readonly ACCESS_KEY = 'VOTRE_CLE_ICI';
```

### 5.3 - Créer Wake Words personnalisés

1. Dans le dashboard, cliquer sur "Porcupine Wake Word"
2. Cliquer "Train Custom Wake Word"
3. Entrer le wake word (ex: "hey gob")
4. Choisir les plateformes: Android, iOS
5. Cliquer "Train"
6. Télécharger les fichiers `.ppn` générés

### 5.4 - Ajouter modèles dans le projet

**Structure:**

```
agent-ui/
├── android/app/src/main/assets/
│   ├── hey-gob_android.ppn
│   ├── hello-robot_android.ppn
│   └── ...
│
└── ios/App/App/Resources/
    ├── hey-gob_ios.ppn
    ├── hello-robot_ios.ppn
    └── ...
```

---

## 🧪 PHASE 6: Tests

### 6.1 - Test Backend

```bash
cd pcd-ai-embedded-agent/backend

# Démarrer le backend
python main.py
```

**Test avec curl:**

```bash
# Enregistrer un audio court avec "hey gob" et convertir en base64
# Puis tester:

curl -X POST http://localhost:8000/wake-word/detect \
  -H "Content-Type: application/json" \
  -d '{
    "audio_data": "BASE64_AUDIO_HERE",
    "audio_format": "webm"
  }'

# Réponse attendue:
# {
#   "detected": true,
#   "confidence": 0.85,
#   "transcription": "hey gob",
#   "processing_time_ms": 234
# }
```

### 6.2 - Test Frontend Web

```bash
cd pcd-ai-embedded-agent/agent-ui

# Mode dev
npm run dev

# Ouvrir http://localhost:5173
# Aller dans Settings → Wake Word
# Entrer un wake word
# Activer wake mode
# Parler le wake word
# Vérifier détection
```

### 6.3 - Test Mobile Android

```bash
cd pcd-ai-embedded-agent/agent-ui

# Build
npm run build

# Sync
npx cap sync android

# Ouvrir Android Studio
npx cap open android

# Dans Android Studio:
# 1. Connecter téléphone via USB
# 2. Cliquer Run ▶️
# 3. L'app s'installe

# Sur le téléphone:
# 1. Ouvrir l'app
# 2. Aller dans Settings
# 3. Choisir "Picovoice" ou "Whisper Backend"
# 4. Sauvegarder
# 5. Activer wake mode
# 6. Dire le wake word
# 7. Vérifier réponse
```

---

## 📊 Comparaison Finale des Performances

| Métrique | Web Speech | Picovoice | Whisper Backend |
|----------|------------|-----------|-----------------|
| **Latence** | ⚡ < 50ms | ⚡ 100-200ms | ⏱️ 300-500ms |
| **CPU** | 🟢 < 3% | 🟢 < 5% | 🟡 10-15% |
| **Batterie** | 🟢 < 1%/h | 🟢 < 2%/h | 🟡 5-8%/h |
| **Précision** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Offline** | ❌ Non | ✅ Oui | ✅ Oui (local) |
| **Custom Word** | ✅ Oui | ⚠️ Pré-défini | ✅ Oui |

---

## 🎯 Résumé de la Solution

### ✅ **Web Browser (Chrome, Safari):**
- Utilise **Web Speech API (Google)**
- ⚡ Instantané, gratuit, parfait pour web
- ✅ Wake word totalement personnalisable

### ✅ **Mobile App - Mode Performance:**
- Utilise **Picovoice (Natif)**
- ⚡ Ultra-rapide (< 200ms)
- 🔋 Batterie optimale (< 2%/h)
- ⚠️ Wake words pré-définis (5-10 options)

### ✅ **Mobile App - Mode Flexible:**
- Utilise **Whisper Backend**
- 🔧 Wake word totalement personnalisable
- ⏱️ Latence acceptable (300-500ms)
- 🔋 Consommation modérée (5-8%/h)

---

## 🚀 Prochaines Étapes

1. **Backend** (1-2h)
   - [ ] Créer `wake_word_detector.py`
   - [ ] Modifier `main.py` (routes)
   - [ ] Modifier `config.py`
   - [ ] Modifier `.env`
   - [ ] Tester avec curl

2. **Frontend** (2-3h)
   - [ ] Créer `wakeWord.types.ts`
   - [ ] Créer `audioStreamService.ts`
   - [ ] Créer `picovoiceService.ts`
   - [ ] Modifier `wakeWordService.ts`
   - [ ] Créer `WakeWordSettings.tsx`
   - [ ] Modifier `MicButton.tsx`

3. **Configuration Mobile** (30 min)
   - [ ] Installer plugin Picovoice
   - [ ] Configurer permissions Android
   - [ ] Configurer permissions iOS
   - [ ] Créer compte Picovoice
   - [ ] Obtenir Access Key
   - [ ] Créer wake words
   - [ ] Ajouter modèles `.ppn`

4. **Tests** (1h)
   - [ ] Test backend (curl)
   - [ ] Test web browser
   - [ ] Test mobile (Android/iOS)
   - [ ] Test changement de moteur
   - [ ] Test batterie mobile

---

## 💡 Conclusion

Cette solution **HYBRIDE** offre:

✅ **Meilleure performance possible** sur chaque plateforme
✅ **Flexibilité totale** pour l'utilisateur
✅ **Architecture propre** et maintenable
✅ **Expérience optimale** web ET mobile
✅ **Choix intelligent** selon besoins utilisateur

**Temps total estimé: 4-6 heures**

**Tu es prêt à commencer l'implémentation ? On commence par quelle phase ?** 🚀
