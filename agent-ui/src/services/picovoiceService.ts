/**
 * PicovoiceService - DÉSACTIVÉ
 * Remplacé par @capacitor-community/speech-recognition dans wakeWordService.ts
 * Fichier gardé pour éviter les erreurs d'import
 */

export class PicovoiceService {
  async initialize(): Promise<void> {}
  async start(): Promise<void> {}
  async stop(): Promise<void> {}
  async cleanup(): Promise<void> {}
  onDetection(_callback: (keyword: string) => void): void {}
  getIsListening(): boolean { return false; }
  getAvailableWakeWords(): string[] { return []; }
}

export const picovoiceService = new PicovoiceService();