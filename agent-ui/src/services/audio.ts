/**
 * Service Audio - Gestion de l'enregistrement et lecture
 * Phase 2: Implémentation avec MediaRecorder
 */

class AudioService {
  private mediaRecorder: MediaRecorder | null = null;
  private audioChunks: Blob[] = [];
  private stream: MediaStream | null = null;
  private hasPermission: boolean = false;

  private readonly audioConstraints: MediaTrackConstraints = {
    channelCount: 1,
    sampleRate: 16000,
    echoCancellation: true,
    noiseSuppression: true,
  };

  private releaseStream(): void {
    if (this.stream) {
      this.stream.getTracks().forEach((track) => track.stop());
      this.stream = null;
    }
  }
  
  /**
   * Initialiser et demander permission micro
   */
  async initialize(): Promise<void> {
    try {
      // Permission warm-up only: release immediately to avoid locking mic
      // when wake-word recognizer needs exclusive access on mobile.
      const probeStream = await navigator.mediaDevices.getUserMedia({
        audio: this.audioConstraints,
      });
      probeStream.getTracks().forEach((track) => track.stop());
      this.hasPermission = true;
      console.log('🎤 Microphone access granted');
    } catch (error) {
      console.error('❌ Microphone access denied:', error);
      throw new Error('Microphone permission denied. Please allow microphone access.');
    }
  }
  
  /**
   * Démarrer l'enregistrement audio
   */
  async startRecording(): Promise<void> {
    if (!this.hasPermission) {
      await this.initialize();
    }

    if (!this.stream) {
      this.stream = await navigator.mediaDevices.getUserMedia({
        audio: this.audioConstraints,
      });
    }
    
    this.audioChunks = [];
    
    // Utiliser webm pour compatibilité navigateur
    const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus') 
      ? 'audio/webm;codecs=opus'
      : 'audio/webm';
    
    this.mediaRecorder = new MediaRecorder(this.stream!, { mimeType });
    
    this.mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        this.audioChunks.push(event.data);
      }
    };
    
    this.mediaRecorder.start();
    console.log('🎤 Recording started');
  }
  
  /**
   * Arrêter l'enregistrement et retourner le Blob audio
   */
  async stopRecording(): Promise<Blob> {
    return new Promise((resolve, reject) => {
      if (!this.mediaRecorder) {
        reject(new Error('No recording in progress'));
        return;
      }
      
      this.mediaRecorder.onstop = () => {
        const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });
        console.log(`⏹️ Recording stopped (${audioBlob.size} bytes)`);
        this.releaseStream();
        this.mediaRecorder = null;
        resolve(audioBlob);
      };
      
      this.mediaRecorder.stop();
    });
  }
  
  /**
   * Jouer un audio depuis base64
   */
  async playAudio(base64Audio: string): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        // Décoder base64 en audio
        const binaryString = atob(base64Audio);
        const bytes = new Uint8Array(binaryString.length);
        for (let i = 0; i < binaryString.length; i++) {
          bytes[i] = binaryString.charCodeAt(i);
        }
        const audioBlob = new Blob([bytes], { type: 'audio/wav' });
        const audioUrl = URL.createObjectURL(audioBlob);
        
        const audio = new Audio(audioUrl);
        
        audio.onended = () => {
          URL.revokeObjectURL(audioUrl);
          console.log('🔊 Playback complete');
          resolve();
        };
        
        audio.onerror = (error) => {
          URL.revokeObjectURL(audioUrl);
          console.error('❌ Playback error:', error);
          reject(error);
        };
        
        console.log('🔊 Playing audio...');
        audio.play();
      } catch (error) {
        console.error('❌ Audio playback failed:', error);
        reject(error);
      }
    });
  }
  
  /**
   * Vérifier si le micro est disponible
   */
  isInitialized(): boolean {
    return this.hasPermission;
  }
  
  /**
   * Nettoyer les ressources
   */
  cleanup(): void {
    this.releaseStream();
    this.mediaRecorder = null;
    this.audioChunks = [];
  }
}

export const audioService = new AudioService();

