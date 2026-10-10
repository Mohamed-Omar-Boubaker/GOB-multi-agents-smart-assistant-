/**
 * MicButton Component - Bouton pour déclencher l'enregistrement
 * Phase 4: Support wake word mode avec navigation
 */

import { useEffect, useState, useCallback } from 'react';
import { useAgentStore } from '../../store/agentStore';
import { audioService } from '../../services/audio';
import { apiService, getLanguageFromSettings } from '../../services/api';
import { wakeWordService } from '../../services/wakeWordService';

export function MicButton() {
  const { 
    state, 
    setState, 
    setTranscription, 
    setResponse, 
    setPlayingAudio, 
    showToast, 
    addMessage,
    wakeMode,
    wakeWord,
    enableWakeMode,
    disableWakeMode
  } = useAgentStore();
  
  const [isWakeListening, setIsWakeListening] = useState(false);
  
  // ✅ Quand l'agent revient à idle → reprendre l'écoute du wake word
  useEffect(() => {
    if (state === 'idle' && wakeMode && wakeWordService.getIsActive()) {
      wakeWordService.resumeAfterDetection();
    }
  }, [state, wakeMode]);

  // Handle wake word detection and start recording
  const handleWakeWordDetected = useCallback(async (detectedWord: string) => {
    console.log('🎤 Wake word detected:', detectedWord);
    showToast(`Wake word detected: ${detectedWord}`, 'success');
    
    if (state === 'idle') {
      setState('listening');
      
      try {
        await audioService.startRecording();
        console.log('🎤 Auto-recording started after wake word');
        showToast('Recording started automatically', 'info');
        
      } catch (error) {
        console.error('❌ Recording failed:', error);
        showToast('Microphone access denied. Please allow permission.', 'error');
        setState('idle');
        // Reprendre wake word si recording fail
        wakeWordService.resumeAfterDetection();
      }
    }
  }, [state, setState, showToast]);
  
  // Start/stop wake word service when wake mode changes
  useEffect(() => {
    const startWakeService = async () => {
      if (wakeMode && wakeWord && !isWakeListening) {
        try {
          wakeWordService.setWakeWord(wakeWord);
          wakeWordService.onDetection(handleWakeWordDetected);
          wakeWordService.onErrorEvent((error) => {
            console.error('Wake word error:', error);
            showToast('Wake word detection error', 'error');
          });
          
          await wakeWordService.start();
          setIsWakeListening(true);
          console.log('👂 Wake word listening started');
          
        } catch (error) {
          console.error('Failed to start wake word service:', error);
          showToast('Failed to start wake word detection', 'error');
          disableWakeMode();
        }
      } else if (!wakeMode && isWakeListening) {
        wakeWordService.stop();
        setIsWakeListening(false);
        console.log('🔇 Wake word listening stopped');
      }
    };
    
    startWakeService();
    
    // Don't stop on unmount - let it continue for fullscreen mode
  }, [wakeMode, wakeWord]);
  
  // Toggle wake mode
  const handleToggleWakeMode = () => {
    if (!wakeWord) {
      showToast('Please set a wake word in settings first', 'warning');
      return;
    }
    
    if (wakeMode) {
      disableWakeMode();
      wakeWordService.stop();
      setIsWakeListening(false);
      showToast('Wake mode disabled', 'info');
    } else {
      enableWakeMode();
      showToast('Wake mode enabled', 'success');
    }
  };

  const handleMouseDown = async () => {
    if (state === 'idle') {
      if (wakeMode) {
        wakeWordService.pause();
      }
      setState('listening');
      
      try {
        await audioService.startRecording();
        console.log('🎤 Real recording started');
        showToast('Recording started', 'info');
      } catch (error) {
        console.error(' Recording failed:', error);
        showToast('Microphone access denied. Please allow permission.', 'error');
        setState('idle');
      }
    }
  };
  
  const handleMouseUp = async () => {
    if (state === 'listening') {
      setState('thinking');
      console.log(' Processing with backend...');
      
      try {
        // Arrêter l'enregistrement
        const audioBlob = await audioService.stopRecording();
        
        // Vérifier taille audio
        if (audioBlob.size < 1000) {
          showToast('Audio too short. Please speak longer.', 'warning');
          setState('idle');
          return;
        }
        
        // Envoyer au backend
        const response = await apiService.sendAudio(audioBlob);
        
        // Extraire les données
        const language = getLanguageFromSettings();
        const transcriptionFallbacks: Record<string, string> = {
          en: 'Could not transcribe',
          fr: 'Impossible de transcrire',
          ar: 'تعذر التفريغ'
        };
        const userTranscription = response.transcription || (transcriptionFallbacks[language] || transcriptionFallbacks.fr);
        const agentResponse = response.message || response.response || 'No response';
        const audioData = response.audio?.audio_data;
        const metadata = response.metadata;
        
        // Mettre à jour le state
        setTranscription(userTranscription);
        setResponse(agentResponse, metadata);
        
        // Ajouter à l'historique
        addMessage('user', userTranscription, metadata);
        addMessage('agent', agentResponse, metadata);
        
        console.log('📝 User said:', userTranscription);
        console.log('🤖 Agent replied:', agentResponse);
        if (metadata) {
          console.log('🏷️ Entities:', metadata.entities);
          console.log('😊 Emotion:', metadata.emotion);
          console.log('🎯 Intent:', metadata.intent);
          
          if (metadata.entities.length > 0) {
            const entityNames = metadata.entities.map((e: any) => e.name).join(', ');
            showToast(`Detected: ${entityNames}`, 'success');
          }
        }
        
        // Jouer l'audio de réponse
        if (audioData && apiService.isAudioEnabled()) {
          setState('speaking');
          setPlayingAudio(true);
          
          try {
            await audioService.playAudio(audioData);
            showToast('Response played successfully', 'success');
          } catch (error) {
            console.error('❌ Audio playback failed:', error);
            showToast('Could not play audio response', 'error');
          } finally {
            setPlayingAudio(false);
          }
        } else if (audioData) {
          console.log('🔇 Audio muted by user settings');
        } else {
          showToast('No audio response from backend', 'warning');
        }
        
        // Retour à idle → useEffect va appeler resumeAfterDetection automatiquement
        setState('idle');
        console.log('😌 Back to idle');
        
      } catch (error) {
        console.error('❌ Backend error:', error);
        setState('error');
        setResponse('Error: Could not reach backend. Make sure the server is running on port 8000.');
        showToast('Backend connection failed. Check if server is running.', 'error');
        
        setTimeout(() => setState('idle'), 3000);
      }
    }
  };

  const handlePressStart = (
    event: React.MouseEvent<HTMLButtonElement> | React.TouchEvent<HTMLButtonElement>
  ) => {
    event.preventDefault();
    handleMouseDown();
  };

  const handlePressEnd = (
    event: React.MouseEvent<HTMLButtonElement> | React.TouchEvent<HTMLButtonElement>
  ) => {
    event.preventDefault();
    handleMouseUp();
  };
  
  // Support clavier : Espace = hold to talk (disabled in wake mode)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.code === 'Space' && state === 'idle' && !e.repeat && !wakeMode) {
        e.preventDefault();
        handleMouseDown();
      }
    };
    
    const handleKeyUp = (e: KeyboardEvent) => {
      if (e.code === 'Space' && state === 'listening' && !wakeMode) {
        e.preventDefault();
        handleMouseUp();
      }
    };
    
    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('keyup', handleKeyUp);
    
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('keyup', handleKeyUp);
    };
  }, [state, wakeMode]);
  
  // Gérer aussi si la souris quitte le bouton pendant l'enregistrement
  const handleMouseLeave = () => {
    if (state === 'listening') {
      handleMouseUp();
    }
  };
  
  const isDisabled = state !== 'idle' || wakeMode;
  
  return (
    <div style={{ textAlign: 'center' }}>
      {/* Wake Mode Toggle */}
      <div style={{ marginBottom: '15px' }}>
        <button
          onClick={handleToggleWakeMode}
          style={{
            background: wakeMode ? '#4caf50' : '#666',
            color: 'white',
            border: 'none',
            borderRadius: '25px',
            padding: '10px 20px',
            fontSize: '0.9rem',
            fontWeight: '600',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            margin: '0 auto',
            transition: 'all 0.3s ease',
            boxShadow: wakeMode ? '0 0 20px rgba(76, 175, 80, 0.5)' : '0 2px 4px rgba(0,0,0,0.2)'
          }}
        >
          {wakeMode ? '🎙️ Wake Mode ON' : '🎙️ Wake Mode OFF'}
        </button>
        
        {wakeMode && (
          <p style={{ 
            marginTop: '8px', 
            color: '#4caf50', 
            fontSize: '0.85rem',
            fontWeight: '600'
          }}>
            👂 Listening for: "{wakeWord}"
          </p>
        )}
      </div>
      
      {/* Push-to-Talk Instructions */}
      {state === 'idle' && !wakeMode && (
        <p style={{ marginBottom: '10px', color: '#666', fontSize: '0.9rem' }}>
          👇 Click and <strong>HOLD</strong> the button, then release
          <br />
          <span style={{ fontSize: '0.8rem', color: '#999' }}>
            Or press and hold <kbd style={{ 
              background: '#f0f0f0', 
              padding: '2px 6px', 
              borderRadius: '4px',
              border: '1px solid #ccc',
              fontFamily: 'monospace'
            }}>SPACE</kbd>
          </span>
        </p>
      )}
      
      {wakeMode && (
        <p style={{ marginBottom: '10px', color: '#999', fontSize: '0.85rem', fontStyle: 'italic' }}>
          Push-to-talk disabled in wake mode
        </p>
      )}
      
      {state === 'listening' && (
        <p style={{ marginBottom: '10px', color: '#f5576c', fontSize: '0.9rem', fontWeight: 'bold' }}>
          ⚡ Release the button to send!
        </p>
      )}
      
      {state === 'thinking' && (
        <p style={{ marginBottom: '10px', color: '#4facfe', fontSize: '0.9rem', fontWeight: 'bold' }}>
          🧠 Processing with backend...
        </p>
      )}
      
      <button
        className={`mic-button ${state}`}
        onMouseDown={handlePressStart}
        onMouseUp={handlePressEnd}
        onMouseLeave={handleMouseLeave}
        onTouchStart={handlePressStart}
        onTouchEnd={handlePressEnd}
        onContextMenu={(event) => event.preventDefault()}
        disabled={isDisabled}
        style={{
          userSelect: 'none',
          WebkitUserSelect: 'none',
          MozUserSelect: 'none',
          msUserSelect: 'none',
          WebkitTouchCallout: 'none',
          touchAction: 'none'
        }}
      >
        {state === 'idle' && ' Press & Hold to Talk'}
        {state === 'listening' && ' Recording... (Release!)'}
        {state === 'thinking' && ' Thinking...'}
        {state === 'speaking' && ' Speaking...'}
        {state === 'error' && ' Error'}
      </button>
    </div>
  );
}