/**
 * CanvasEyes - Composant React pour afficher les yeux animés
 * Version: Section Avatar (pas fullscreen)
 */

import { useEffect, useRef } from 'react';
import { useAgentStore } from '../../store/agentStore';
import { EyesEngine } from './eyesEngine';
import type { EyesStateName } from './eyesConfig';
import type { AgentState } from '../../types';
import './CanvasEyes.css';

// Mapping des états React vers états Canvas
function mapStateToCanvasState(reactState: AgentState, wakeMode: boolean): EyesStateName {
  // Si wake mode est activé mais idle → sleep
  if (wakeMode && reactState === 'idle') return 'sleep';
  
  // Mapping direct des états
  const stateMap: Record<AgentState, EyesStateName> = {
    'idle': 'idle',
    'listening': 'listening',
    'thinking': 'thinking',
    'speaking': 'speaking',
    'confirmation': 'thinking', // map to thinking
    'execution': 'thinking',    // map to thinking
    'success': 'happy',
    'error': 'error'
  };
  
  return stateMap[reactState] || 'idle';
}

export function CanvasEyes() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const offscreenRef = useRef<HTMLCanvasElement>(null);
  const engineRef = useRef<EyesEngine | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  
  const state = useAgentStore((s) => s.state);
  const wakeMode = useAgentStore((s) => s.wakeMode);
  
  // Initialize engine quand les canvas sont prêts
  useEffect(() => {
    if (!canvasRef.current || !offscreenRef.current) return;
    
    try {
      engineRef.current = new EyesEngine(canvasRef.current, offscreenRef.current);
      engineRef.current.start();
      console.log('✅ CanvasEyes engine started');
    } catch (error) {
      console.error('❌ Failed to initialize CanvasEyes:', error);
    }
    
    return () => {
      if (engineRef.current) {
        engineRef.current.stop();
        console.log('🛑 CanvasEyes engine stopped');
      }
    };
  }, []);
  
  // Sync state avec le moteur
  useEffect(() => {
    if (!engineRef.current) return;
    
    const canvasState = mapStateToCanvasState(state, wakeMode);
    engineRef.current.setState(canvasState);
  }, [state, wakeMode]);
  
  // Mouse tracking (seulement dans le container)
  useEffect(() => {
    const container = containerRef.current;
    const canvas = canvasRef.current;
    if (!container || !canvas || !engineRef.current) return;
    
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
    
    container.addEventListener('mousemove', handleMouseMove);
    container.addEventListener('touchmove', handleTouchMove, { passive: false });
    
    return () => {
      container.removeEventListener('mousemove', handleMouseMove);
      container.removeEventListener('touchmove', handleTouchMove);
    };
  }, []);
  
  return (
    <div className="canvas-eyes-container" ref={containerRef}>
      <canvas ref={canvasRef} className="canvas-eyes" />
      <canvas ref={offscreenRef} className="canvas-offscreen" />
    </div>
  );
}
