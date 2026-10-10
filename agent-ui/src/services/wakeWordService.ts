/**
 * Wake Word Service - Détection du mot-clé
 * - Sur Capacitor (Android): utilise @capacitor-community/speech-recognition
 * - Sur Web: utilise Web Speech API (Chrome desktop)
 *
 * FIXES v2:
 *  [FIX-1] Langue dynamique selon la langue du wake word (fr-FR / en-US / auto)
 *  [FIX-2] Match normalisé + fuzzy léger (accents/punct + tolérance faible)
 *  [FIX-3] Guard contre double-émission partialResults (debounce + flag detectedThisSession)
 *  [FIX-4] Health watchdog basé sur isListening() pour Android no-speech timeout
 *  [FIX-5] Listeners retirés proprement via références nommées (pas removeAllListeners)
 *  [FIX-6] Langue configurable par setLanguage() ou auto-détectée depuis le wake word
 */

import { SpeechRecognition } from '@capacitor-community/speech-recognition';

type WakeWordCallback = (transcript: string) => void;
type ErrorCallback = (error: string) => void;

declare global {
  interface Window {
    SpeechRecognition: any;
    webkitSpeechRecognition: any;
    Capacitor?: any;
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────────────────────────────────────

const isCapacitor = (): boolean => {
  try {
    const cap = (window as any).Capacitor;
    if (cap && typeof cap.isNativePlatform === 'function') return cap.isNativePlatform();
    if (cap?.getPlatform) {
      const p = cap.getPlatform();
      return p === 'android' || p === 'ios';
    }
    return false;
  } catch {
    return false;
  }
};

/**
 * [FIX-2] Match strict par word-boundary.
 * "bob" dans "hibou" ou "Reebok" → pas détecté.
 * "bob" dans "hi bob" ou "Bob!" → détecté ✅
 */
const normalizeSpeechText = (value: string): string => {
  return value
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9\s]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
};

const levenshteinDistance = (a: string, b: string): number => {
  if (a === b) return 0;
  if (!a.length) return b.length;
  if (!b.length) return a.length;

  const prev = new Array(b.length + 1);
  const curr = new Array(b.length + 1);

  for (let j = 0; j <= b.length; j += 1) prev[j] = j;

  for (let i = 1; i <= a.length; i += 1) {
    curr[0] = i;
    for (let j = 1; j <= b.length; j += 1) {
      const cost = a[i - 1] === b[j - 1] ? 0 : 1;
      curr[j] = Math.min(
        prev[j] + 1,
        curr[j - 1] + 1,
        prev[j - 1] + cost
      );
    }
    for (let j = 0; j <= b.length; j += 1) prev[j] = curr[j];
  }

  return prev[b.length];
};

const fuzzyTokenMatch = (token: string, wakeToken: string): boolean => {
  if (token === wakeToken) return true;
  if (!token || !wakeToken) return false;

  const maxLen = Math.max(token.length, wakeToken.length);
  if (maxLen <= 4) {
    return levenshteinDistance(token, wakeToken) <= 1;
  }
  if (maxLen <= 7) {
    return levenshteinDistance(token, wakeToken) <= 1;
  }
  return false;
};

const matchesWakeWord = (transcript: string, wakeWord: string): boolean => {
  const normalizedTranscript = normalizeSpeechText(transcript);
  const normalizedWakeWord = normalizeSpeechText(wakeWord);
  if (!normalizedWakeWord || !normalizedTranscript) return false;
  if (normalizedTranscript === normalizedWakeWord) return true;

  if ((` ${normalizedTranscript} `).includes(` ${normalizedWakeWord} `)) return true;

  const transcriptTokens = normalizedTranscript.split(' ').filter(Boolean);
  const wakeTokens = normalizedWakeWord.split(' ').filter(Boolean);
  if (wakeTokens.length === 0 || transcriptTokens.length === 0) return false;

  if (wakeTokens.length === 1) {
    return transcriptTokens.some((token) => fuzzyTokenMatch(token, wakeTokens[0]));
  }

  for (let i = 0; i <= transcriptTokens.length - wakeTokens.length; i += 1) {
    let allMatch = true;
    for (let j = 0; j < wakeTokens.length; j += 1) {
      if (!fuzzyTokenMatch(transcriptTokens[i + j], wakeTokens[j])) {
        allMatch = false;
        break;
      }
    }
    if (allMatch) return true;
  }

  return false;
};

const getDeviceLanguage = (): string => {
  try {
    const lang = typeof navigator !== 'undefined' ? navigator.language : '';
    if (lang && lang.trim()) return lang;
  } catch {
    // Ignore and fallback to en-US
  }
  return 'en-US';
};

/**
 * [FIX-1] Détecter si un mot est majoritairement latin/anglais ou français
 * pour choisir la langue de reconnaissance.
 * On peut aussi forcer via setLanguage().
 */
const guessLanguage = (word: string): string => {
  const deviceLang = getDeviceLanguage();
  // Mots connus français
  const frWords = ['bonjour', 'salut', 'allô', 'allo', 'aide', 'hé', 'hey', 'démarrer', 'stop'];
  const lower = word.toLowerCase();
  if (frWords.includes(lower)) return 'fr-FR';

  // Si wake word en caractères latins simples, l'anglais est souvent plus fiable
  // pour des mots courts comme "red", "bob", "jarvis".
  const isAsciiLatin = /^[a-z0-9\s]+$/.test(lower);
  if (isAsciiLatin) return 'en-US';

  // Sinon, fallback sur la locale device (et non forcer en-US).
  return deviceLang;
};

const buildLanguageCandidates = (wakeWord: string): string[] => {
  const guessed = guessLanguage(wakeWord);
  const device = getDeviceLanguage();
  const candidates = [
    guessed,
    guessed === 'en-US' ? 'fr-FR' : 'en-US',
    device,
  ];

  return Array.from(new Set(candidates.filter((lang) => !!lang && !!lang.trim())));
};

// ─────────────────────────────────────────────────────────────────────────────
// Service
// ─────────────────────────────────────────────────────────────────────────────

export class WakeWordService {
  private recognition: any = null;
  private wakeWord: string = '';
  private language: string = 'en-US'; // [FIX-1]
  private languageCandidates: string[] = ['en-US'];
  private languageCandidateIndex: number = 0;
  private heardSinceLastStart: boolean = false;
  private isActive: boolean = false;
  private onWakeWordDetected: WakeWordCallback | null = null;
  private onError: ErrorCallback | null = null;

  // Listener Capacitor references (pour retrait propre) [FIX-5]
  private partialResultsListener: any = null;
  private listeningStateListener: any = null;

  private restartTimer: any = null;
  private isDetecting: boolean = false;
  private detectionWatchdog: any = null;
  private isPaused: boolean = false;
  private isStarting: boolean = false;

  private lastStartAt: number = 0;
  private lastRestartAt: number = 0;
  private consecutiveStops: number = 0;
  private startWatchdog: any = null;
  private ignoreStoppedUntil: number = 0;

  // [FIX-3] Guard double-détection dans la même session
  private detectedThisSession: boolean = false;
  private lastDetectedAt: number = 0;
  private readonly DETECTION_DEBOUNCE_MS = 1500;
  private readonly QUICK_RESTART_DELAY_MS = 250;
  private readonly FAST_BACKOFF_DELAY_MS = 700;
  private readonly RESTART_MIN_GAP_MS = 250;
  private readonly HEALTH_POLL_MS = 2500;

  constructor() {
    if (!isCapacitor()) {
      this.initializeSpeechRecognition();
    }
  }

  // ── Web Speech API ──────────────────────────────────────────────────────────

  private initializeSpeechRecognition(): void {
    if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
      console.warn('[WakeWord] Web Speech Recognition not supported');
      return;
    }
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    this.recognition = new SR();
    this.recognition.continuous = true;
    this.recognition.interimResults = false;
    // [FIX-1] langue dynamique
    this.recognition.lang = this.language;

    this.recognition.onresult = (event: any) => {
      for (let i = event.resultIndex; i < event.results.length; i++) {
        if (!event.results[i].isFinal) continue;
        const raw: string = event.results[i][0].transcript;
        console.log('[WakeWord] Heard:', raw);
        // [FIX-2] word-boundary match
        if (this.isActive && this.wakeWord && matchesWakeWord(raw, this.wakeWord)) {
          console.log('[WakeWord] 🔥 DETECTED!', raw);
          this.onWakeWordDetected?.(raw.trim());
        }
      }
    };

    this.recognition.onerror = (event: any) => {
      if (event.error === 'no-speech') return;
      console.warn('[WakeWord] Error:', event.error);
      if (event.error === 'not-allowed' || event.error === 'service-not-allowed') {
        this.onError?.('Microphone access denied');
        this.isActive = false;
      }
    };

    this.recognition.onend = () => {
      if (this.isActive && !this.isDetecting && !this.isPaused) {
        try { this.recognition?.start(); } catch (e) {
          console.error('[WakeWord] Failed to restart:', e);
        }
      }
    };
  }

  // ── Public API ──────────────────────────────────────────────────────────────

  /**
   * [FIX-1] Forcer une langue spécifique (ex: 'fr-FR', 'en-US', 'ar-TN')
   * À appeler avant setWakeWord() si besoin.
   */
  setLanguage(lang: string): void {
    this.language = lang;
    this.languageCandidates = [lang];
    this.languageCandidateIndex = 0;
    if (this.recognition) {
      this.recognition.lang = lang;
    }
  }

  setWakeWord(word: string): void {
    const newWord = word.trim().toLowerCase();
    console.log('[WakeWord] Wake word set to:', newWord);
    const changed = newWord !== this.wakeWord;
    this.wakeWord = newWord;

    // [FIX-1] Auto-detect langue si pas forcée manuellement
    this.languageCandidates = buildLanguageCandidates(newWord);
    this.languageCandidateIndex = 0;

    const autoLang = this.languageCandidates[0] || guessLanguage(newWord);
    if (autoLang !== this.language) {
      this.language = autoLang;
      console.log('[WakeWord] Auto language →', autoLang, '| candidates:', this.languageCandidates.join(', '));
    }

    if (changed && this.isActive && isCapacitor() && !this.isDetecting) {
      console.log('[WakeWord] Word changed, restarting...');
      this.isActive = false;
      SpeechRecognition.stop().catch(() => {}).finally(() => {
        this.startCapacitor().catch((e) =>
          console.error('[WakeWord] Restart after word change failed:', e)
        );
      });
    }
  }

  async start(): Promise<void> {
    if (!this.wakeWord) throw new Error('Wake word not set');
    if (this.isActive) {
      console.log('[WakeWord] Already active');
      return;
    }
    this.isPaused = false;
    this.detectedThisSession = false; // [FIX-3]

    if (isCapacitor()) {
      await this.startCapacitor();
      return;
    }

    if (!this.recognition) throw new Error('Speech Recognition not supported');
    this.recognition.lang = this.language; // [FIX-1]
    return new Promise((resolve, reject) => {
      try {
        this.isActive = true;
        this.isDetecting = false;
        this.isPaused = false;
        this.recognition!.start();
        console.log('[WakeWord] Web: listening for:', this.wakeWord, 'lang:', this.language);
        resolve();
      } catch (error) {
        this.isActive = false;
        reject(error);
      }
    });
  }

  // ── Capacitor internals ─────────────────────────────────────────────────────

  private async startCapacitor(): Promise<void> {
    try {
      const { available } = await SpeechRecognition.available();
      if (!available) throw new Error('Speech Recognition not available');

      await SpeechRecognition.requestPermissions();
      const permCheck = await SpeechRecognition.checkPermissions();
      if (permCheck.speechRecognition === 'denied') throw new Error('Permission denied');

      // [FIX-5] Retirer les anciens listeners via références nommées avant d'en ajouter
      await this.removeCapacitorListeners();

      // ── partialResults listener ──
      this.partialResultsListener = await SpeechRecognition.addListener(
        'partialResults',
        (data: { matches: string[] }) => {
          if (!this.isActive || this.isDetecting) return;
          const matches = data.matches || [];
          if (matches.length === 0) return;

          this.heardSinceLastStart = true;
          this.lastStartAt = Date.now();
          this.consecutiveStops = 0;
          this.armStartWatchdog();

          console.log('[WakeWord] Heard:', matches.join(','));

          // [FIX-3] Debounce anti double-détection
          const now = Date.now();
          if (this.detectedThisSession && now - this.lastDetectedAt < this.DETECTION_DEBOUNCE_MS) {
            return;
          }

          for (const raw of matches) {
            // [FIX-2] word-boundary match
            if (this.wakeWord && matchesWakeWord(raw, this.wakeWord)) {
              console.log('[WakeWord] 🔥 DETECTED:', raw);

              // [FIX-3] Marquer détection
              this.detectedThisSession = true;
              this.lastDetectedAt = now;
              this.isDetecting = true;

              if (this.detectionWatchdog) {
                clearTimeout(this.detectionWatchdog);
                this.detectionWatchdog = null;
              }
              this.detectionWatchdog = setTimeout(() => {
                console.warn('[WakeWord] Detection watchdog expired, forcing restart');
                this.isDetecting = false;
                this.detectedThisSession = false;
                this.doRestart().catch(() => {});
              }, 15000);
              console.log('[WakeWord] Detection watchdog set (15s)');

              SpeechRecognition.stop().catch(() => {});
              this.onWakeWordDetected?.(raw.trim());
              return; // sortir dès la première détection
            }
          }
        }
      );

      // ── listeningState listener ──
      this.listeningStateListener = await SpeechRecognition.addListener(
        'listeningState',
        (data: { status: 'started' | 'stopped' }) => {
          console.log('[WakeWord] State:', data.status);

          if (data.status === 'started') {
            this.lastStartAt = Date.now();
            this.consecutiveStops = 0;
            this.armStartWatchdog();

            // If Android auto-restarted by itself, cancel any queued manual restart.
            if (this.restartTimer) {
              clearTimeout(this.restartTimer);
              this.restartTimer = null;
            }
          }

          if (data.status === 'stopped' && this.isActive && !this.isDetecting && !this.isPaused) {
            const now = Date.now();
            if (now < this.ignoreStoppedUntil) {
              console.log('[WakeWord] Ignoring self-induced stopped event');
              return;
            }

            const sinceStart = this.lastStartAt ? now - this.lastStartAt : 9999;
            this.consecutiveStops += 1;

            let delay = this.QUICK_RESTART_DELAY_MS;
            if (sinceStart < 500) delay = 450;
            if (this.consecutiveStops >= 6) delay = this.FAST_BACKOFF_DELAY_MS;

            this.scheduleRestartWithStop(delay, false);
          }
        }
      );

      this.isActive = true;
      this.isDetecting = false;
      this.isPaused = false;
      this.detectedThisSession = false; // [FIX-3]
      await this.startRecognitionCapacitor('initial');

    } catch (error: any) {
      const message = this.getErrorMessage(error);
      if (this.isTransientError(message)) {
        console.warn('[WakeWord] ⚠️ Transient start error:', message);
        this.isActive = true;
        this.isDetecting = false;
        this.isPaused = false;
        this.scheduleRestartWithStop(this.FAST_BACKOFF_DELAY_MS, false);
        return;
      }
      this.isActive = false;
      console.error('[WakeWord] ❌ Start failed:', error);
      throw error;
    }
  }

  resumeAfterDetection(): void {
    if (!this.isActive) return;
    console.log('[WakeWord] Resuming after detection...');
    this.isDetecting = false;
    this.isPaused = false;
    this.detectedThisSession = false; // [FIX-3] reset pour prochaine session

    if (this.restartTimer) { clearTimeout(this.restartTimer); this.restartTimer = null; }
    if (this.detectionWatchdog) { clearTimeout(this.detectionWatchdog); this.detectionWatchdog = null; }

    if (isCapacitor()) {
      SpeechRecognition.stop().catch((e: any) =>
        console.warn('[WakeWord] Resume stop error:', e)
      );
      this.ignoreStoppedUntil = Date.now() + 1500;
      setTimeout(() => {
        if (this.isActive && !this.isDetecting && !this.isPaused) {
          this.doRestart().catch(() => {});
        }
      }, 200);
      return;
    }

    try { this.recognition?.stop(); } catch (e) {
      console.warn('[WakeWord] Resume stop error:', e);
    }
    setTimeout(() => {
      if (this.isActive && !this.isDetecting && !this.isPaused) {
        this.recognition?.start();
        console.log('[WakeWord] Web: restarted after detection');
      }
    }, 150);
  }

  private async doRestart(): Promise<void> {
    if (!this.isActive || this.isDetecting || this.isPaused) return;
    if (this.detectionWatchdog) { clearTimeout(this.detectionWatchdog); this.detectionWatchdog = null; }

    try {
      await this.startRecognitionCapacitor('restart');
    } catch (e: any) {
      const message = this.getErrorMessage(e);
      if (this.isTransientError(message)) {
        console.warn('[WakeWord] ⚠️ Transient restart error:', message);
        this.scheduleRestartWithStop(this.FAST_BACKOFF_DELAY_MS, false);
        return;
      }
      if (this.isActive && !this.isDetecting && !this.isPaused) {
        this.scheduleRestartWithStop(this.FAST_BACKOFF_DELAY_MS, false);
      }
    }
  }

  private async startRecognitionCapacitor(reason: 'initial' | 'restart'): Promise<void> {
    if (this.isStarting) {
      console.log('[WakeWord] Start skipped (already starting):', reason);
      return;
    }
    this.isStarting = true;
    try {
      const activeLanguage = this.languageCandidates[this.languageCandidateIndex] || this.language;
      this.language = activeLanguage;
      this.heardSinceLastStart = false;

      await SpeechRecognition.start({
        language: activeLanguage, // [FIX-1] langue dynamique + fallback auto
        maxResults: 10,          // plus d'alternatives ASR pour améliorer hit-rate wake word
        partialResults: true,
        popup: false,
      });
      // Le plugin peut ne pas émettre "started" tant qu'on ne parle pas.
      // On marque donc le démarrage ici pour éviter les faux redémarrages.
      this.lastStartAt = Date.now();
      console.log(`[WakeWord] ✅ Listening (${reason}) for: "${this.wakeWord}" [${activeLanguage}]`);
      this.armStartWatchdog();
    } finally {
      this.isStarting = false;
    }
  }

  private scheduleRestartWithStop(delayMs: number, forceStop: boolean = true): void {
    if (this.isPaused) return;
    if (this.restartTimer) { clearTimeout(this.restartTimer); this.restartTimer = null; }

    const now = Date.now();
    const sinceRestart = this.lastRestartAt ? now - this.lastRestartAt : 9999;
    const minGap = this.RESTART_MIN_GAP_MS;
    const extraDelay = sinceRestart < minGap ? minGap - sinceRestart : 0;
    const effectiveDelay = delayMs + extraDelay;

    this.restartTimer = setTimeout(() => {
      this.restartTimer = null;
      if (!this.isActive || this.isDetecting || this.isPaused) return;
      this.lastRestartAt = Date.now();
      this.clearStartWatchdog();
      if (forceStop) {
        this.ignoreStoppedUntil = Date.now() + 1500;
        SpeechRecognition.stop().catch(() => {});
      }
      this.doRestart().catch(() => {});
    }, effectiveDelay);
  }

  private armStartWatchdog(): void {
    this.clearStartWatchdog();
    // Health watchdog: vérifie l'état réel du moteur natif.
    this.startWatchdog = setTimeout(async () => {
      if (!this.isActive || this.isDetecting || this.isPaused) return;
      if (this.isStarting) {
        this.armStartWatchdog();
        return;
      }

      try {
        const status = await SpeechRecognition.isListening();
        if (status?.listening) {
          // Le moteur tourne, on réarme simplement le watchdog.
          this.armStartWatchdog();
          return;
        }

        const sinceStart = Date.now() - this.lastStartAt;
        if (sinceStart < this.HEALTH_POLL_MS) {
          // Laisse un court délai de warm-up avant de conclure à un arrêt.
          console.warn('[WakeWord] Health watchdog: recognizer not listening yet, retrying...');
          this.armStartWatchdog();
          return;
        }

        console.warn('[WakeWord] Health watchdog: recognizer stopped → soft restart');
        if (!this.heardSinceLastStart && this.languageCandidates.length > 1) {
          this.languageCandidateIndex = (this.languageCandidateIndex + 1) % this.languageCandidates.length;
          const nextLanguage = this.languageCandidates[this.languageCandidateIndex];
          console.warn('[WakeWord] Switching language fallback →', nextLanguage);
        }
        this.scheduleRestartWithStop(this.QUICK_RESTART_DELAY_MS, false);
      } catch (e) {
        // Fallback défensif si isListening échoue sur certains devices.
        console.warn('[WakeWord] Health watchdog check failed, soft restart:', e);
        if (!this.heardSinceLastStart && this.languageCandidates.length > 1) {
          this.languageCandidateIndex = (this.languageCandidateIndex + 1) % this.languageCandidates.length;
          const nextLanguage = this.languageCandidates[this.languageCandidateIndex];
          console.warn('[WakeWord] Switching language fallback (check failed) →', nextLanguage);
        }
        this.scheduleRestartWithStop(this.QUICK_RESTART_DELAY_MS, false);
      }
    }, this.HEALTH_POLL_MS);
  }

  private clearStartWatchdog(): void {
    if (this.startWatchdog) { clearTimeout(this.startWatchdog); this.startWatchdog = null; }
  }

  // [FIX-5] Retrait propre des listeners via leurs références
  private async removeCapacitorListeners(): Promise<void> {
    try {
      if (this.partialResultsListener) {
        await this.partialResultsListener.remove();
        this.partialResultsListener = null;
      }
      if (this.listeningStateListener) {
        await this.listeningStateListener.remove();
        this.listeningStateListener = null;
      }
    } catch (e) {
      console.warn('[WakeWord] Remove listeners error:', e);
    }
  }

  pause(): void {
    this.isPaused = true;
    this.isDetecting = false;
    this.clearStartWatchdog();
    if (this.restartTimer) { clearTimeout(this.restartTimer); this.restartTimer = null; }
    if (this.detectionWatchdog) { clearTimeout(this.detectionWatchdog); this.detectionWatchdog = null; }

    if (isCapacitor()) {
      this.ignoreStoppedUntil = Date.now() + 1500;
      SpeechRecognition.stop().catch((e: any) =>
        console.warn('[WakeWord] Pause stop error:', e)
      );
      return;
    }
    try { this.recognition?.stop(); } catch (e) {
      console.warn('[WakeWord] Pause stop error:', e);
    }
  }

  async stop(): Promise<void> {
    this.isActive = false;
    this.isDetecting = false;
    this.isPaused = true;
    this.detectedThisSession = false;
    this.clearStartWatchdog();
    if (this.restartTimer) { clearTimeout(this.restartTimer); this.restartTimer = null; }
    if (this.detectionWatchdog) { clearTimeout(this.detectionWatchdog); this.detectionWatchdog = null; }

    if (isCapacitor()) {
      this.ignoreStoppedUntil = Date.now() + 1500;
      SpeechRecognition.stop().catch((e: any) =>
        console.warn('[WakeWord] Stop error:', e)
      );
      // [FIX-5] Retrait propre
      await this.removeCapacitorListeners();
      return;
    }
    try { this.recognition?.stop(); } catch (e) {
      console.warn('[WakeWord] Stop error:', e);
    }
  }

  // ── Accessors ───────────────────────────────────────────────────────────────

  onDetection(callback: WakeWordCallback): void { this.onWakeWordDetected = callback; }
  onErrorEvent(callback: ErrorCallback): void { this.onError = callback; }
  isSupported(): boolean { return isCapacitor() ? true : this.recognition !== null; }
  getIsActive(): boolean { return this.isActive; }
  getWakeWord(): string { return this.wakeWord; }
  getLanguage(): string { return this.language; }

  // ── Utils ───────────────────────────────────────────────────────────────────

  private isTransientError(message: string): boolean {
    const lower = message.toLowerCase();
    return (
      lower.includes('no match') ||
      lower.includes('client side error') ||
      lower.includes('not connected')
    );
  }

  private getErrorMessage(error: any): string {
    if (!error) return '';
    if (typeof error === 'string') return error;
    if (error.message) return error.message;
    try { return JSON.stringify(error); } catch { return String(error); }
  }
}

export const wakeWordService = new WakeWordService();