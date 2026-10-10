/**
 * AgentScreen - Écran principal avec avatar et micro
 * Phase 3: Toast notifications
 */

import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Avatar } from '../../components/Avatar/Avatar';
import { MicButton } from '../../components/MicButton/MicButton';
import { Waveform } from '../../components/Waveform/Waveform';
import { Toast } from '../../components/Toast';
import { EntityBadge } from '../../components/EntityBadge';
import { ConversationHistory } from '../../components/ConversationHistory';
import { MemoryPanel } from '../../components/MemoryPanel';
import ActionPanel from '../../components/ActionPanel/ActionPanel';
import SettingsPanel from '../../components/SettingsPanel/SettingsPanel';
import DeviceManagerPanel from '../../components/DeviceManagerPanel/DeviceManagerPanel';
import ContactManagerPanel from '../../components/ContactManagerPanel/ContactManagerPanel';
import { useAgentStore } from '../../store/agentStore';
import { apiService } from '../../services/api';

export function AgentScreen() {
  const navigate = useNavigate();
  const { state, transcription, response, metadata, toasts, messages, hideToast, showToast, wakeMode, wakeWord } = useAgentStore();
  const [micPermission, setMicPermission] = useState<'granted' | 'denied' | 'pending'>('pending');
  const [backendOnline, setBackendOnline] = useState<boolean>(false);
  
  // Navigate to fullscreen when wake mode is enabled
  useEffect(() => {
    if (wakeMode) {
      navigate('/wake');
    }
  }, [wakeMode, navigate]);
  
  // Demander permission micro au chargement
  useEffect(() => {
    const initAudio = async () => {
      // Permission is already requested at app bootstrap.
      // Avoid opening getUserMedia stream here to prevent mic contention
      // with wake-word recognition on mobile.
      setMicPermission('granted');
      console.log('✅ Microphone ready (lazy capture mode)');
      showToast('Microphone ready!', 'success');
    };
    
    const checkBackend = async () => {
      const online = await apiService.healthCheck();
      setBackendOnline(online);
      if (online) {
        showToast('Backend connected!', 'success');
      } else {
        console.warn('⚠️ Backend not reachable from current app context');
        showToast('Backend offline. Check backend IP/port and mobile network.', 'warning');
      }
    };
    
    initAudio();
    checkBackend();
  }, []);
  
  return (
    <div className="agent-screen">
      {/* Settings Panel (floating button) */}
      <SettingsPanel />
      <DeviceManagerPanel />
      <ContactManagerPanel />
      
      <header className="agent-header">
        <div className="agent-header-main">
          <h1>GOB Agent</h1>
          <span className={`agent-state-badge state-${state}`}>State: {state}</span>
        </div>

        {/* Wake Mode Status Indicator */}
        {wakeMode && (
          <div className="wake-mode-badge">
            <span className="wake-mode-dot" />
            Wake Mode: "{wakeWord}"
          </div>
        )}
      </header>
      
      {/* Avertissements */}
      {micPermission === 'denied' && (
        <div style={{ 
          background: '#ffebee', 
          border: '2px solid #f44336', 
          borderRadius: '12px', 
          padding: '15px', 
          color: '#c62828',
          marginBottom: '20px'
        }}>
          <strong>❌ Microphone Access Denied</strong>
          <p style={{ margin: '5px 0 0 0', fontSize: '0.9rem' }}>
            Please allow microphone access in your browser settings to use voice features.
          </p>
        </div>
      )}
      
      {!backendOnline && micPermission === 'granted' && (
        <div style={{ 
          background: '#fff3e0', 
          border: '2px solid #ff9800', 
          borderRadius: '12px', 
          padding: '15px', 
          color: '#e65100',
          marginBottom: '20px'
        }}>
          <strong>⚠️ Backend Offline</strong>
          <p style={{ margin: '5px 0 0 0', fontSize: '0.9rem' }}>
            Make sure backend is running and reachable from phone (same Wi-Fi + port 8000).
          </p>
        </div>
      )}
      {/*
      {micPermission === 'granted' && backendOnline && (
        <div style={{ 
          background: '#e8f5e9', 
          border: '2px solid #4caf50', 
          borderRadius: '12px', 
          padding: '15px', 
          color: '#2e7d32',
          marginBottom: '20px'
        }}>
          <strong>✅ System Ready</strong>
          <p style={{ margin: '5px 0 0 0', fontSize: '0.9rem' }}>
            Microphone and backend connected. Ready to talk!
          </p>
        </div>
      )} 
      */}
      
      <main>
        {/* Avatar animé Lottie */}
        <Avatar />
        
        {/* Waveform audio */}
        <Waveform />
        
        {/* Panneau de mémoire */}
        <MemoryPanel userId="web_user_001" />
        
        {/* Panneau des actions IoT */}
        <ActionPanel userId="web_user_001" />
        
        {/* Historique des conversations */}
        <ConversationHistory messages={messages} />
        
        {/* Transcription (dernière uniquement - optionnel maintenant) */}
        {transcription && (
          <div className="transcription" style={{ display: 'none' }}>
            <strong>You:</strong> {transcription}
          </div>
        )}
        
        {/* Réponse (dernière uniquement - optionnel maintenant) */}
        {response && (
          <div className="response" style={{ display: 'none' }}>
            <strong>GOB:</strong> {response}
          </div>
        )}
        
        {/* Entités extraites avec icônes */}
        {metadata && metadata.entities.length > 0 && (
          <div className="entities-container">
            <div className="entities-header">
              Detected Entities
              <span className="entities-count">{metadata.entities.length}</span>
            </div>
            {metadata.entities.map((entity, i) => (
              <EntityBadge key={i} entity={entity} index={i} />
            ))}
          </div>
        )}
      </main>
      
      {/* Toast notifications */}
      <div style={{ position: 'fixed', top: '20px', right: '20px', zIndex: 1000 }}>
        {toasts.map((toast) => (
          <Toast
            key={toast.id}
            message={toast.message}
            type={toast.type}
            onClose={() => hideToast(toast.id)}
          />
        ))}
      </div>
      
      <footer>
        {/* Bouton micro */}
        <MicButton />
      </footer>
    </div>
  );
}
