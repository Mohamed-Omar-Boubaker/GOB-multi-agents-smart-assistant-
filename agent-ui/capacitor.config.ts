import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.pcd.agent',
  appName: 'Agent Intelligent',
  webDir: 'dist',
  server: {
    androidScheme: 'http', // HTTP pour développement local
    cleartext: true, // Autoriser HTTP non sécurisé (LAN local)
    allowNavigation: [
      // URL backend gérée côté app via VITE_BACKEND_URL
      'http://localhost:8000',
    ]
  }
};

export default config;
