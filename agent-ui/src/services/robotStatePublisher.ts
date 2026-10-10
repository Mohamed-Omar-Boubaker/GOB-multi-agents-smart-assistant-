/**
 * Robot state publisher (Phase 2)
 * Sends UX state transitions to backend relay: POST /robot/state
 */

import type { AgentState } from '../types';
import { getBackendURL } from '../config/api.config';

export type RobotState =
  | 'idle'
  | 'sleep'
  | 'listening'
  | 'thinking'
  | 'speaking'
  | 'happy'
  | 'error';

interface PublishOptions {
  wakeMode?: boolean;
  userId?: string;
  source?: string;
  force?: boolean;
}

const DEFAULT_USER_ID = 'web_user_001';
const DEFAULT_SOURCE = 'agent_ui';
const MIN_PUBLISH_GAP_MS = 120;

let lastState: RobotState | null = null;
let lastPublishAt = 0;

function getLanguageFromSettings(): string {
  try {
    const raw = localStorage.getItem('gob-settings');
    if (!raw) return 'fr';

    const parsed = JSON.parse(raw);
    const lang = String(parsed?.language || 'fr').toLowerCase();
    if (lang === 'fr' || lang === 'en' || lang === 'ar') {
      return lang;
    }
  } catch {
    // Keep default.
  }

  return 'fr';
}

function mapAgentStateToRobotState(state: AgentState, wakeMode: boolean): RobotState {
  if (wakeMode && state === 'idle') return 'sleep';

  switch (state) {
    case 'idle':
      return 'idle';
    case 'listening':
      return 'listening';
    case 'thinking':
    case 'confirmation':
    case 'execution':
      return 'thinking';
    case 'speaking':
      return 'speaking';
    case 'success':
      return 'happy';
    case 'error':
      return 'error';
    default:
      return 'idle';
  }
}

async function publishRobotState(state: RobotState, options: PublishOptions = {}): Promise<void> {
  const now = Date.now();
  const force = options.force === true;

  if (!force && state === lastState) {
    return;
  }

  if (!force && now - lastPublishAt < MIN_PUBLISH_GAP_MS) {
    return;
  }

  const payload = {
    request_id: `req_${now.toString(36)}_${Math.random().toString(36).slice(2, 8)}`,
    user_id: options.userId || DEFAULT_USER_ID,
    state,
    lang: getLanguageFromSettings(),
    source: options.source || DEFAULT_SOURCE,
    ts: Math.floor(now / 1000)
  };

  const url = `${getBackendURL().replace(/\/+$/, '')}/robot/state`;

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload),
      cache: 'no-store',
      signal: AbortSignal.timeout(4000)
    });

    if (!response.ok) {
      const body = await response.text().catch(() => '');
      throw new Error(`HTTP ${response.status} ${body}`);
    }

    lastState = state;
    lastPublishAt = now;
    console.log('[RobotState] Published:', state, payload);
  } catch (error) {
    console.warn('[RobotState] Publish failed:', state, error);
  }
}

export const robotStatePublisher = {
  async publishFromAgentState(state: AgentState, options: PublishOptions = {}): Promise<void> {
    const target = mapAgentStateToRobotState(state, options.wakeMode === true);
    await publishRobotState(target, options);
  },

  async publishExplicitState(state: RobotState, options: PublishOptions = {}): Promise<void> {
    await publishRobotState(state, options);
  }
};
