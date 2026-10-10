/**
 * FullscreenEyesScreen - Page fullscreen pour mode Wake Word
 * Les yeux occupent tout l'écran comme dans le test HTML
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAgentStore } from '../../store/agentStore';
import { EyesEngine } from '../../components/CanvasEyes/eyesEngine';
import { wakeWordService } from '../../services/wakeWordService';
import { audioService } from '../../services/audio';
import { apiService, getLanguageFromSettings } from '../../services/api';
import type { EyesStateName } from '../../components/CanvasEyes/eyesConfig';
import type { AgentState } from '../../types';
import './FullscreenEyesScreen.css';

// Mapping états React → Canvas
function mapStateToCanvasState(reactState: AgentState): EyesStateName {
  const stateMap: Record<AgentState, EyesStateName> = {
    'idle': 'sleep', // En wake mode, idle = sleep
    'listening': 'listening',
    'thinking': 'thinking',
    'speaking': 'speaking',
    'confirmation': 'thinking',
    'execution': 'thinking',
    'success': 'happy',
    'error': 'error'
  };
  
  return stateMap[reactState] || 'sleep';
}

export function FullscreenEyesScreen() {
  const navigate = useNavigate();
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const offscreenRef = useRef<HTMLCanvasElement>(null);
  const engineRef = useRef<EyesEngine | null>(null);
  const recordingRef = useRef<boolean>(false);
  
  const { 
    state, 
    setState,
    wakeMode, 
    wakeWord, 
    disableWakeMode,
    setTranscription,
    setResponse,
    setPlayingAudio,
    showToast,
    addMessage
  } = useAgentStore();
  const [isWakeListening, _setIsWakeListening] = useState(true);
  
  // Handle wake word detection and start recording  
  const handleWakeWordDetected = useCallback(async (detectedWord: string) => {
    console.log('🎤 [Fullscreen] Wake word detected:', detectedWord);
    showToast(`Wake word detected: ${detectedWord}`, 'success');
    
    // Prevent multiple recordings
    if (recordingRef.current || state !== 'idle') {
      console.log('[Fullscreen] Already recording or busy, ignoring wake word');
      return;
    }
    
    // Start recording automatically
    recordingRef.current = true;
    setState('listening');
    
    try {
      wakeWordService.pause();
      await audioService.startRecording();
      console.log('🎤 [Fullscreen] Auto-recording started after wake word');
      showToast('Listening...', 'info');
      
      // Auto-stop after 5 seconds and send to backend
      setTimeout(async () => {
        console.log('[Fullscreen] Auto-stopping recording after 5 seconds');
        if (!recordingRef.current) {
          console.log('[Fullscreen] Recording already stopped');
          return;
        }
        
        // Call handleStopRecording directly
        setState('thinking');
        console.log('[Fullscreen] Processing with backend...');
        
        try {
          const audioBlob = await audioService.stopRecording();
          recordingRef.current = false;
          
          if (audioBlob.size < 1000) {
            showToast('Audio too short. Please speak longer.', 'warning');
            setState('idle');
            return;
          }
          
          const response = await apiService.sendAudio(audioBlob);
          
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
          
          setTranscription(userTranscription);
          setResponse(agentResponse, metadata);
          
          addMessage('user', userTranscription, metadata);
          addMessage('agent', agentResponse, metadata);
          
          console.log('📝 [Fullscreen] User said:', userTranscription);
          console.log('🤖 [Fullscreen] Agent replied:', agentResponse);
          
          if (audioData && apiService.isAudioEnabled()) {
            setState('speaking');
            setPlayingAudio(true);
            
            try {
              await audioService.playAudio(audioData);
            } catch (error) {
              console.error('❌ Audio playback failed:', error);
            } finally {
              setPlayingAudio(false);
            }
          }
          
          setState('idle');
          console.log('😌 [Fullscreen] Back to idle');
          if (wakeMode) {
            wakeWordService.resumeAfterDetection();
          }
          
        } catch (error) {
          console.error('❌ [Fullscreen] Backend error:', error);
          setState('error');
          setResponse('Error: Could not reach backend.');
          showToast('Backend connection failed', 'error');
          recordingRef.current = false;
          setTimeout(() => setState('idle'), 3000);
          if (wakeMode) {
            wakeWordService.resumeAfterDetection();
          }
        }
      }, 5000);
      
    } catch (error) {
      console.error('❌ [Fullscreen] Recording failed:', error);
      showToast('Microphone access denied', 'error');
      setState('idle');
      recordingRef.current = false;
    }
  }, [state, setState, showToast, setTranscription, setResponse, setPlayingAudio, addMessage]);
  
  // Setup wake word callback
  useEffect(() => {
    console.log('[Fullscreen] Setting up wake word callback');
    wakeWordService.onDetection(handleWakeWordDetected);
  }, [handleWakeWordDetected]);
  
  // Si wake mode est désactivé, retourner à la page normale
  useEffect(() => {
    if (!wakeMode) {
      wakeWordService.stop();
      console.log('[Fullscreen] Wake mode disabled, navigating back');
      navigate('/');
    }
  }, [wakeMode, navigate]);
  
  // Initialize engine
  useEffect(() => {
    if (!canvasRef.current || !offscreenRef.current) return;
    
    try {
      engineRef.current = new EyesEngine(canvasRef.current, offscreenRef.current);
      engineRef.current.start();
      // Démarrer en mode sleep car wake mode est actif
      engineRef.current.setState('sleep');
      console.log('✅ Fullscreen Eyes engine started');
    } catch (error) {
      console.error('❌ Failed to initialize Fullscreen Eyes:', error);
    }
    
    return () => {
      if (engineRef.current) {
        engineRef.current.stop();
        console.log('🛑 Fullscreen Eyes engine stopped');
      }
    };
  }, []);
  
  // Sync state
  useEffect(() => {
    if (!engineRef.current) return;
    
    const canvasState = mapStateToCanvasState(state);
    engineRef.current.setState(canvasState);
  }, [state]);
  
  // Mouse tracking fullscreen
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !engineRef.current) return;
    
    const handleMouseMove = (e: MouseEvent) => {
      const rect = canvas.getBoundingClientRect();
      const x = (e.clientX - rect.left) / rect.width;
      const y = (e.clientY - rect.top) / rect.height;
      engineRef.current?.setMousePosition(x, y);
    };
    
    const handleTouchMove = (e: TouchEvent) => {
      e.preventDefault();
      const touch = e.touches[0];
      const rect = canvas.getBoundingClientRect();
      const x = (touch.clientX - rect.left) / rect.width;
      const y = (touch.clientY - rect.top) / rect.height;
      engineRef.current?.setMousePosition(x, y);
    };
    
    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('touchmove', handleTouchMove, { passive: false });
    
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('touchmove', handleTouchMove);
    };
  }, []);
  
  // Handler pour désactiver wake mode et retourner
  const handleDisableWakeMode = () => {
    wakeWordService.stop();
    disableWakeMode();
    navigate('/');
  };
  
  return (
    <div className="fullscreen-eyes-screen">
      {/* Canvas fullscreen */}
      <canvas ref={canvasRef} className="fullscreen-canvas" />
      <canvas ref={offscreenRef} className="fullscreen-offscreen" />
      
      {/* UI Overlay */}
      <div className="fullscreen-ui">
        {/* Header */}
        <div className="fullscreen-topbar">
          <span className="fullscreen-logo">GOB AGENT</span>
          <div className={`fullscreen-status-dot ${state === 'listening' ? 'listening' : ''} ${state === 'thinking' ? 'thinking' : ''} ${state === 'speaking' ? 'speaking' : ''}`}></div>
        </div>
        
        {/* State chip */}
        <div className="fullscreen-state-chip">
          {state === 'idle' ? 'Dormant' : state.charAt(0).toUpperCase() + state.slice(1)}
        </div>
        
        {/* Wake word status */}
        <div className={`fullscreen-wake-status ${isWakeListening ? 'active' : ''}`}>
          {wakeWord ? `Wake word: ${wakeWord.toUpperCase()}` : 'No wake word'}
        </div>
        
        {/* Hint text */}
        {state === 'idle' && (
          <div className="fullscreen-hint">
            Say &ldquo;{wakeWord}&rdquo; to wake up
          </div>
        )}
        
        {state === 'listening' && (
          <div className="fullscreen-hint" style={{ color: '#4caf50', fontWeight: 'bold' }}>
            Listening... (will send automatically)
          </div>
        )}
        
        {/* Exit button */}
        <button 
          className="fullscreen-exit-btn" 
          onClick={(e) => {
            e.stopPropagation();
            handleDisableWakeMode();
          }} 
          title="Exit wake mode"
        >
          ✕
        </button>
      </div>
    </div>
  );
}
