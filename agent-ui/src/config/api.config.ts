/**
 * Configuration API pour connexion Backend
 * Adapté automatiquement selon environnement (dev/mobile/prod)
 */

const isDevelopment = import.meta.env.DEV;
const envBackendURL = (import.meta.env.VITE_BACKEND_URL as string | undefined)?.trim();

// Local fallback used only when no env value is provided.
const DEFAULT_LOCAL_BACKEND_URL = 'http://localhost:8000';

const isLocalHostName = (hostname: string): boolean => {
  return hostname === 'localhost' || hostname === '127.0.0.1';
};

const normalizeBaseURL = (url: string): string => url.replace(/\/+$/, '');

const getRuntimeLANURL = (): string | null => {
  if (typeof window === 'undefined') return null;
  const host = window.location.hostname;
  if (!host || isLocalHostName(host)) return null;
  return `http://${host}:8000`;
};

/**
 * Détecte si l'app tourne dans Capacitor (app mobile)
 */
const isCapacitor = (): boolean => {
  if (typeof window === 'undefined') return false;

  // Méthode 1: Vérifier window.Capacitor
  if (typeof window !== 'undefined' && (window as any).Capacitor !== undefined) {
    console.log('🔍 isCapacitor check: TRUE (via window.Capacitor)');
    return true;
  }
  
  // Méthode 2: Vérifier si on est en production + pas localhost
  const isProductionBuild = import.meta.env.PROD;
  const isLocalhost = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
  
  console.log('🔍 isCapacitor check:', isProductionBuild && !isLocalhost);
  console.log('🔍 PROD:', isProductionBuild, 'localhost:', isLocalhost);
  console.log('🔍 hostname:', window.location.hostname);
  
  return isProductionBuild && !isLocalhost;
};

/**
 * Obtenir l'URL du backend selon l'environnement
 *
 * Recommande pour mobile: definir VITE_BACKEND_URL dans .env
 */
export const getBackendURL = (): string => {
  console.log('🔧 getBackendURL called');
  console.log('🔧 isDevelopment:', isDevelopment);
  console.log('🔧 import.meta.env.DEV:', import.meta.env.DEV);
  console.log('🔧 import.meta.env.PROD:', import.meta.env.PROD);

  if (envBackendURL) {
    const normalized = normalizeBaseURL(envBackendURL);
    console.log('🔧 Backend URL depuis VITE_BACKEND_URL:', normalized);
    return normalized;
  }

  const runtimeLANURL = getRuntimeLANURL();

  if (isDevelopment) {
    if (runtimeLANURL) {
      console.log('💻 Mode Dev réseau: Connexion backend via host de la page');
      return runtimeLANURL;
    }
    console.log('💻 Mode Dev local: Connexion au backend localhost');
    return DEFAULT_LOCAL_BACKEND_URL;
  }

  if (isCapacitor()) {
    console.warn('⚠️ Mode Mobile: VITE_BACKEND_URL non défini.');
    console.warn('⚠️ Définissez VITE_BACKEND_URL dans agent-ui/.env puis rebuild/sync.');
    console.warn('⚠️ Fallback utilisé:', runtimeLANURL || DEFAULT_LOCAL_BACKEND_URL);
    return runtimeLANURL || DEFAULT_LOCAL_BACKEND_URL;
  }

  console.warn('⚠️ Mode Production: VITE_BACKEND_URL non défini, fallback utilisé.');
  return runtimeLANURL || DEFAULT_LOCAL_BACKEND_URL;
};

/**
 * Configuration complète de l'API
 */
export const API_CONFIG = {
  BASE_URL: getBackendURL(),
  
  // Endpoints disponibles
  ENDPOINTS: {
    HEALTH: '/health',
    AUDIO_STREAM: '/audio/stream',
    AUDIO_UPLOAD: '/audio/upload',
    CHAT: '/chat',
    TTS: '/tts',
    AGENTS: '/agents',
    HISTORY: '/history',
    WAKE_WORD: '/wake-word',
  },
  
  // Timeouts (en millisecondes)
  TIMEOUT: {
    DEFAULT: 30000,      // 30 secondes
    AUDIO_UPLOAD: 60000, // 60 secondes pour audio
    STREAMING: 120000,   // 2 minutes pour streaming
  },
  
  // Headers par défaut
  DEFAULT_HEADERS: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
  
  // Configuration audio
  AUDIO_CONFIG: {
    SAMPLE_RATE: 16000,
    CHANNELS: 1,
    BIT_DEPTH: 16,
    FORMAT: 'wav',
  },
};

/**
 * Helper pour construire URL complète
 */
export const buildURL = (endpoint: string): string => {
  const base = API_CONFIG.BASE_URL.replace(/\/$/, ''); // Enlever / final
  const path = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  return `${base}${path}`;
};

/**
 * Afficher configuration actuelle (debug)
 */
export const logAPIConfig = (): void => {
  console.group('🔧 Configuration API');
  console.log('Environment:', isDevelopment ? 'Development' : 'Production');
  console.log('Is Capacitor:', isCapacitor());
  console.log('Backend URL:', API_CONFIG.BASE_URL);
  console.groupEnd();
};

export default API_CONFIG;
