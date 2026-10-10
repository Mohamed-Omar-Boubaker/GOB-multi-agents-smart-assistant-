/**
 * Avatar Component - Affiche l'animation Lottie selon l'état
 * Phase 1: Composant avec mapping état → animation
 */

import Lottie from 'lottie-react';
import { useAgentStore } from '../../store/agentStore';
import type { AgentState } from '../../types';

// Import direct des animations
import idleAnimation from '../../assets/animations/Little power robot.json';
import thinkingAnimation from '../../assets/animations/ai animation Flow 1.json';
import loadingAnimation from '../../assets/animations/Loading.json';
import welcomeAnimation from '../../assets/animations/Welcome.json';
import alertAnimation from '../../assets/animations/Alert.json';
import confirmAnimation from '../../assets/animations/Confirm Popup 2.json';

// Mapping état → animation
const ANIMATION_MAP: Record<AgentState, any> = {
  idle: idleAnimation,
  listening: idleAnimation, // Temporaire - sound wave est vide
  thinking: thinkingAnimation,
  speaking: idleAnimation, // Temporaire
  confirmation: confirmAnimation,
  execution: loadingAnimation,
  success: welcomeAnimation,
  error: alertAnimation
};

export function Avatar() {
  const state = useAgentStore((s) => s.state);
  const currentAnimation = ANIMATION_MAP[state];
  
  return (
    <div className="avatar-container">
      <Lottie 
        animationData={currentAnimation}
        loop={true}
        autoplay={true}
        style={{ width: '100%', maxWidth: '400px', height: 'auto' }}
      />
    </div>
  );
}
