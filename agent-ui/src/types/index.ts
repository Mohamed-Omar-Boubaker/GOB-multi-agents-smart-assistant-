/**
 * Types TypeScript pour l'application Agent IA
 * Phase 1: Types de base pour la state machine
 */

// États possibles de l'agent
export type AgentState = 
  | 'idle' 
  | 'listening' 
  | 'thinking' 
  | 'speaking' 
  | 'confirmation'
  | 'execution'
  | 'success'
  | 'error';

// Entité extraite par le Memory Extractor
export interface Entity {
  type: 'food' | 'device' | 'person' | 'location' | 'object';
  name: string;
  confidence: number;
}

// Métadonnées de la conversation
export interface ConversationMetadata {
  entities: Entity[];
  emotion: 'happy' | 'satisfied' | 'neutral' | 'frustrated' | 'angry';
  intent: 'order_food' | 'control_device' | 'ask_info' | 'general_chat' | 'complaint' | 'request_help';
  summary: string;
  extracted_at?: string;
}

// Réponse du backend
export interface BackendResponse {
  type: 'conversation' | 'action';
  response?: string;  // For conversations
  message?: string;   // For actions (confirmation message)
  transcription?: string; // User's transcribed speech
  audio?: {
    audio_data: string; // base64
    audio_format: string;
  };
  metadata?: ConversationMetadata;
  status: string;
}

// Configuration audio
export interface AudioConfig {
  sampleRate: number;
  channels: number;
  bitDepth: number;
}
