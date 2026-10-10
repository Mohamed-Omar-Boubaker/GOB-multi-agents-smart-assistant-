/**
 * Service API - Communication avec le backend Python
 * Utilise la configuration centralisée api.config.ts pour Capacitor
 */

import type { BackendResponse } from '../types';
import { getBackendURL, logAPIConfig } from '../config/api.config';

// Utiliser la configuration centralisée qui gère Capacitor correctement
const API_URL = getBackendURL();

// Afficher la config au démarrage
logAPIConfig();
console.log('🔗 API_URL utilisée:', API_URL);

/**
 * Récupérer la langue depuis les settings
 */
export function getLanguageFromSettings(): string {
  try {
    const settings = localStorage.getItem('gob-settings');
    if (settings) {
      const parsed = JSON.parse(settings);
      return parsed.language || 'fr';
    }
  } catch (e) {
    console.warn('Failed to read language from settings', e);
  }
  return 'fr'; // Défaut
}

/**
 * Récupérer si l'audio est activé
 */
function isAudioEnabled(): boolean {
  try {
    const settings = localStorage.getItem('gob-settings');
    if (settings) {
      const parsed = JSON.parse(settings);
      return parsed.audioEnabled !== false; // true par défaut
    }
  } catch (e) {
    console.warn('Failed to read audio setting', e);
  }
  return true;
}

/**
 * Convertir Blob en base64
 */
async function blobToBase64(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onloadend = () => {
      const base64 = reader.result as string;
      // Enlever le préfixe "data:audio/webm;base64,"
      const base64Data = base64.split(',')[1];
      resolve(base64Data);
    };
    reader.onerror = reject;
    reader.readAsDataURL(blob);
  });
}

export const apiService = {
  /**
   * Envoyer audio au backend pour traitement
   * @param audioBlob - Audio enregistré
   * @returns Réponse du backend avec transcription, réponse LLM, et métadonnées
   */
  async sendAudio(audioBlob: Blob): Promise<BackendResponse> {
    try {
      console.log(`📤 Sending audio to backend (${audioBlob.size} bytes)...`);
      
      // Convertir en base64
      const base64Audio = await blobToBase64(audioBlob);
      
      // Lire la langue depuis les settings
      const language = getLanguageFromSettings();
      console.log(`🌐 Using language: ${language}`);
      
      // Format identique à voice_client_pushto_talk.py
      const payload = {
        audio_data: base64Audio,
        audio_format: 'webm',
        user_id: 'web_user_001',
        language: language,
        source: 'react_web'
      };
      
      // Appel API
      const response = await fetch(`${API_URL}/command/audio`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload)
      });
      
      if (!response.ok) {
        throw new Error(`Backend error: ${response.status} ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log('✅ Backend response received');
      
      return data;
      
    } catch (error) {
      console.error('❌ API call failed:', error);
      throw error;
    }
  },
  
  /**
   * Envoyer texte au backend (pour tests)
   */
  async sendText(text: string): Promise<BackendResponse> {
    try {
      const language = getLanguageFromSettings();
      
      const response = await fetch(`${API_URL}/command/text`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text,
          user_id: 'web_user_001',
          language: language,
          source: 'react_web'
        })
      });
      
      if (!response.ok) {
        throw new Error(`Backend error: ${response.status}`);
      }
      
      return await response.json();
      
    } catch (error) {
      console.error('❌ API call failed:', error);
      throw error;
    }
  },
  
  /**
   * Vérifier si le backend est accessible
   */
  async healthCheck(): Promise<boolean> {
    try {
      const response = await fetch(`${API_URL}/health?t=${Date.now()}`, {
        method: 'GET',
        cache: 'no-store',
        signal: AbortSignal.timeout(5000)
      });
      return response.ok;
    } catch {
      return false;
    }
  },

  async getDevicesConfig(): Promise<any> {
    const response = await fetch(`${API_URL}/config/devices`, {
      method: 'GET'
    });

    if (!response.ok) {
      throw new Error(`Backend error: ${response.status}`);
    }

    return await response.json();
  },

  async upsertDevice(payload: { device_type: string; location: string; device_id: string }): Promise<any> {
    const response = await fetch(`${API_URL}/config/devices`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      throw new Error(`Backend error: ${response.status}`);
    }

    return await response.json();
  },

  async deleteDevice(deviceType: string, location: string): Promise<any> {
    const response = await fetch(`${API_URL}/config/devices/${encodeURIComponent(deviceType)}/${encodeURIComponent(location)}`, {
      method: 'DELETE'
    });

    if (!response.ok) {
      throw new Error(`Backend error: ${response.status}`);
    }

    return await response.json();
  },

  async addDeviceAlias(payload: { alias: string; location: string }): Promise<any> {
    const response = await fetch(`${API_URL}/config/device-aliases`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      throw new Error(`Backend error: ${response.status}`);
    }

    return await response.json();
  },

  async deleteDeviceAlias(alias: string): Promise<any> {
    const response = await fetch(`${API_URL}/config/device-aliases/${encodeURIComponent(alias)}`, {
      method: 'DELETE'
    });

    if (!response.ok) {
      throw new Error(`Backend error: ${response.status}`);
    }

    return await response.json();
  },

  async getContactsConfig(): Promise<any> {
    const response = await fetch(`${API_URL}/config/contacts`, {
      method: 'GET'
    });

    if (!response.ok) {
      throw new Error(`Backend error: ${response.status}`);
    }

    return await response.json();
  },

  async addContact(payload: {
    name: string;
    email: string;
    phone?: string;
    tags?: string[];
  }): Promise<any> {
    const response = await fetch(`${API_URL}/config/contacts`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      throw new Error(`Backend error: ${response.status}`);
    }

    return await response.json();
  },

  async updateContact(contactName: string, payload: {
    name?: string;
    email?: string;
    phone?: string;
    tags?: string[];
  }): Promise<any> {
    const response = await fetch(`${API_URL}/config/contacts/${encodeURIComponent(contactName)}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      throw new Error(`Backend error: ${response.status}`);
    }

    return await response.json();
  },

  async deleteContact(contactName: string): Promise<any> {
    const response = await fetch(`${API_URL}/config/contacts/${encodeURIComponent(contactName)}`, {
      method: 'DELETE'
    });

    if (!response.ok) {
      throw new Error(`Backend error: ${response.status}`);
    }

    return await response.json();
  },

  async addContactAlias(payload: { alias: string; contact_name: string }): Promise<any> {
    const response = await fetch(`${API_URL}/config/contact-aliases`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      throw new Error(`Backend error: ${response.status}`);
    }

    return await response.json();
  },

  async deleteContactAlias(alias: string): Promise<any> {
    const response = await fetch(`${API_URL}/config/contact-aliases/${encodeURIComponent(alias)}`, {
      method: 'DELETE'
    });

    if (!response.ok) {
      throw new Error(`Backend error: ${response.status}`);
    }

    return await response.json();
  },

  /**
   * Vérifier si l'audio est activé dans les settings
   */
  isAudioEnabled(): boolean {
    return isAudioEnabled();
  }
};
