/**
 * State Machine - Gestion de l'état global de l'agent
 * Phase 3: Ajout système de toast notifications
 * 
 * Utilise Zustand pour la gestion d'état (plus simple que Redux)
 */

import { create } from 'zustand';
import type { AgentState, ConversationMetadata } from '../types';
import type { ToastType } from '../components/Toast';
import type { Message } from '../components/ConversationHistory';
import { robotStatePublisher } from '../services/robotStatePublisher';

interface ToastMessage {
  id: string;
  message: string;
  type: ToastType;
}

interface AgentStore {
  // État actuel
  state: AgentState;
  
  // Dernière transcription
  transcription: string;
  
  // Dernière réponse
  response: string;
  
  // Métadonnées (entities, emotions, intent)
  metadata: ConversationMetadata | null;
  
  // Audio en cours de lecture
  isPlayingAudio: boolean;
  
  // Toast notifications
  toasts: ToastMessage[];
  
  // Historique des conversations
  messages: Message[];
  
  // Wake Word Mode
  wakeMode: boolean;           // Wake mode activé ou non
  wakeWord: string;            // Wake word configuré par l'utilisateur
  
  // Actions pour changer d'état
  setState: (state: AgentState) => void;
  setTranscription: (text: string) => void;
  setResponse: (text: string, metadata?: ConversationMetadata) => void;
  setPlayingAudio: (playing: boolean) => void;
  showToast: (message: string, type: ToastType) => void;
  hideToast: (id: string) => void;
  addMessage: (sender: 'user' | 'agent', text: string, metadata?: ConversationMetadata) => void;
  clearMessages: () => void;
  reset: () => void;
  
  // Actions Wake Word
  setWakeWord: (word: string) => void;
  enableWakeMode: () => void;
  disableWakeMode: () => void;
  toggleWakeMode: () => void;
}

export const useAgentStore = create<AgentStore>((set, get) => ({
  // État initial
  state: 'idle',
  transcription: '',
  response: '',
  metadata: null,
  isPlayingAudio: false,
  toasts: [],
  messages: [],
  wakeMode: false,        // Wake mode désactivé par défaut
  wakeWord: 'hi',         // Wake word par défaut
  
  // Actions
  setState: (state) => {
    set({ state });
    const wakeMode = get().wakeMode;
    void robotStatePublisher.publishFromAgentState(state, {
      wakeMode,
      source: 'agent_ui'
    });
  },
  
  setTranscription: (text) => set({ transcription: text }),
  
  setResponse: (text, metadata) => set({ 
    response: text,
    metadata: metadata || null
  }),
  
  setPlayingAudio: (playing) => set({ isPlayingAudio: playing }),
  
  showToast: (message, type) => set((state) => ({
    toasts: [...state.toasts, { 
      id: Date.now().toString(), 
      message, 
      type 
    }]
  })),
  
  hideToast: (id) => set((state) => ({
    toasts: state.toasts.filter((toast) => toast.id !== id)
  })),
  
  addMessage: (sender, text, metadata) => set((state) => ({
    messages: [...state.messages, {
      id: `${Date.now()}-${sender}`,
      sender,
      text,
      timestamp: new Date(),
      emotion: metadata?.emotion,
      entities: metadata?.entities
    }]
  })),
  
  clearMessages: () => set({ messages: [] }),
  
  reset: () => set({
    state: 'idle',
    transcription: '',
    response: '',
    metadata: null,
    isPlayingAudio: false
  }),
  
  // Actions Wake Word
  setWakeWord: (word) => {
    console.log('[Store] Wake word set to:', word);
    set({ wakeWord: word });
  },
  
  enableWakeMode: () => {
    console.log('[Store] Wake mode enabled');
    set({ wakeMode: true });
    void robotStatePublisher.publishFromAgentState(get().state, {
      wakeMode: true,
      source: 'agent_ui',
      force: true
    });
  },
  
  disableWakeMode: () => {
    console.log('[Store] Wake mode disabled');
    set({ wakeMode: false });
    void robotStatePublisher.publishFromAgentState(get().state, {
      wakeMode: false,
      source: 'agent_ui',
      force: true
    });
  },
  
  toggleWakeMode: () => set((state) => {
    const newMode = !state.wakeMode;
    console.log('[Store] Wake mode toggled to:', newMode);
    void robotStatePublisher.publishFromAgentState(state.state, {
      wakeMode: newMode,
      source: 'agent_ui',
      force: true
    });
    return { wakeMode: newMode };
  }),
}));
