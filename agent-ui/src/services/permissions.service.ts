/**
 * Service de gestion des permissions système (Android/iOS)
 * Gère: Microphone, Réseau, Stockage, etc.
 */

/**
 * Demander permission d'accès au microphone
 * Déclenche la popup système Android/iOS
 * 
 * @returns {Promise<boolean>} true si accordée, false sinon
 */
export const requestMicrophonePermission = async (): Promise<boolean> => {
  try {
    console.log('🎤 Demande permission microphone...');
    
    // Demander accès microphone avec contraintes optimisées
    const stream = await navigator.mediaDevices.getUserMedia({ 
      audio: {
        echoCancellation: true,      // Annulation d'écho
        noiseSuppression: true,      // Suppression bruit
        autoGainControl: true,       // Contrôle gain auto
        sampleRate: 16000,           // 16kHz (optimal pour voix)
        channelCount: 1,             // Mono
      } 
    });
    
    // Libérer immédiatement les ressources
    // (On voulait juste vérifier la permission)
    stream.getTracks().forEach(track => {
      track.stop();
      console.log('✅ Track audio libéré');
    });
    
    console.log('✅ Permission microphone accordée');
    return true;
    
  } catch (error: any) {
    console.error('❌ Permission microphone refusée:', error);
    
    // Messages d'erreur détaillés
    let errorMessage = 'Permission microphone requise pour utiliser l\'agent vocal.';
    
    if (error.name === 'NotAllowedError') {
      errorMessage += '\n\n📱 Veuillez autoriser l\'accès au microphone dans les paramètres de votre téléphone.';
    } else if (error.name === 'NotFoundError') {
      errorMessage += '\n\n⚠️ Aucun microphone détecté sur votre appareil.';
    } else if (error.name === 'NotReadableError') {
      errorMessage += '\n\n⚠️ Microphone déjà utilisé par une autre application.';
    }
    
    alert(errorMessage);
    return false;
  }
};

/**
 * Vérifier si permission microphone est déjà accordée
 * Sans déclencher de popup
 * 
 * @returns {Promise<boolean>} true si accordée
 */
export const checkMicrophonePermission = async (): Promise<boolean> => {
  try {
    // Utiliser l'API Permissions (pas supportée partout)
    const result = await navigator.permissions.query({ name: 'microphone' as PermissionName });
    
    console.log('🔍 Statut permission micro:', result.state);
    
    // États possibles: 'granted', 'denied', 'prompt'
    if (result.state === 'granted') {
      return true;
    } else if (result.state === 'denied') {
      console.warn('⚠️ Permission microphone refusée précédemment');
      return false;
    }
    
    // État 'prompt' → demander permission
    return await requestMicrophonePermission();
    
  } catch (error) {
    // API Permissions non supportée (iOS Safari, anciens Android)
    console.warn('⚠️ API Permissions non supportée, test direct');
    return await requestMicrophonePermission();
  }
};

/**
 * Vérifier connexion réseau
 * 
 * @returns {boolean} true si connecté
 */
export const checkNetworkConnection = (): boolean => {
  const isOnline = navigator.onLine;
  
  if (!isOnline) {
    console.error('❌ Pas de connexion internet');
    alert('⚠️ Connexion internet requise pour utiliser l\'agent.');
    return false;
  }
  
  console.log('✅ Connexion internet OK');
  return true;
};

/**
 * Vérifier toutes les permissions nécessaires
 * 
 * @returns {Promise<Object>} Objet avec statut de chaque permission
 */
export const checkAllPermissions = async (): Promise<{
  microphone: boolean;
  network: boolean;
  timestamp: string;
}> => {
  console.group('🔐 Vérification Permissions');
  
  const permissions = {
    microphone: await checkMicrophonePermission(),
    network: checkNetworkConnection(),
    timestamp: new Date().toISOString(),
  };
  
  console.table(permissions);
  console.groupEnd();
  
  return permissions;
};

/**
 * Demander toutes les permissions au démarrage
 * 
 * @returns {Promise<boolean>} true si toutes accordées
 */
export const requestAllPermissions = async (): Promise<boolean> => {
  console.log('🚀 Demande de toutes les permissions...');
  
  // Vérifier réseau
  if (!checkNetworkConnection()) {
    return false;
  }
  
  // Demander microphone
  const micGranted = await requestMicrophonePermission();
  
  if (!micGranted) {
    console.error('❌ Permissions insuffisantes');
    return false;
  }
  
  console.log('✅ Toutes les permissions accordées');
  return true;
};

/**
 * Gestionnaire d'événement pour changement de connexion
 */
export const setupNetworkListener = (callback: (isOnline: boolean) => void): (() => void) => {
  const handleOnline = () => {
    console.log('✅ Connexion internet rétablie');
    callback(true);
  };
  
  const handleOffline = () => {
    console.warn('⚠️ Connexion internet perdue');
    callback(false);
  };
  
  window.addEventListener('online', handleOnline);
  window.addEventListener('offline', handleOffline);
  
  // Retourner fonction de cleanup
  return () => {
    window.removeEventListener('online', handleOnline);
    window.removeEventListener('offline', handleOffline);
  };
};

// Export par défaut
export default {
  requestMicrophonePermission,
  checkMicrophonePermission,
  checkNetworkConnection,
  checkAllPermissions,
  requestAllPermissions,
  setupNetworkListener,
};
