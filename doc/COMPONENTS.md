# Documentation des Composants React - GOB Agent

Guide détaillé de tous les composants frontend.

---

## 📚 Table des Matières

1. [MicButton](#micbutton) - Enregistrement vocal principal
2. [Avatar](#avatar) - Animations Lottie agent
3. [Waveform](#waveform) - Visualisation audio
4. [Toast](#toast) - Notifications utilisateur
5. [EntityBadge](#entitybadge) - Badges entités
6. [ConversationHistory](#conversationhistory) - Historique messages
7. [MemoryPanel](#memorypanel) - Panneau mémoire utilisateur
8. [ActionPanel](#actionpanel) - Visualisation actions IoT
9. [SettingsPanel](#settingspanel) - Configuration utilisateur
10. [AgentScreen](#agentscreen) - Écran principal

---

## 1. MicButton

### 📝 Description

Composant principal pour l'enregistrement vocal. Gère le cycle complet:
- Enregistrement audio (MediaRecorder)
- Envoi au backend
- Affichage transcription et réponse
- Playback audio TTS

### 🎨 Interface

```typescript
interface MicButtonProps {
  // Aucune prop (utilise Zustand store)
}
```

### 🔄 Flux de Données

```
User presse espace/bouton
    ↓
handleMouseDown()
    ↓
navigator.mediaDevices.getUserMedia({ audio: true })
    ↓
MediaRecorder.start()
    ↓
setState('listening')
    ↓
User relâche
    ↓
handleMouseUp()
    ↓
MediaRecorder.stop()
    ↓
ondataavailable → audioChunks.push(data)
    ↓
onstop → new Blob(audioChunks, { type: 'audio/webm' })
    ↓
setState('thinking')
    ↓
apiService.sendAudio(audioBlob)
    ↓
Backend processing (STT → Classification → LLM/Action → TTS)
    ↓
Response: { transcription, response/message, audio, metadata }
    ↓
setTranscription(response.transcription)
addMessage('user', transcription)
    ↓
const agentResponse = response.message || response.response
addMessage('agent', agentResponse, metadata)
    ↓
setState('speaking')
    ↓
audioService.playAudio(audioData)
    ↓
audio.onended → setState('idle')
```

### 💡 Code Clé

```typescript
// src/components/MicButton/MicButton.tsx

const MicButton: React.FC = () => {
  const { state, setState, setTranscription, addMessage, showToast } = useAgentStore();
  const [isRecording, setIsRecording] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  // Keyboard shortcut
  useEffect(() => {
    const settings = JSON.parse(localStorage.getItem('gob-settings') || '{}');
    const shortcut = settings.keyboardShortcut || 'space';

    const handleKeyDown = (e: KeyboardEvent) => {
      if (shortcut === 'space' && e.code === 'Space') {
        if (!isRecording) handleMouseDown();
      } else if (shortcut === 'ctrl+k' && e.ctrlKey && e.key === 'k') {
        if (!isRecording) handleMouseDown();
      }
    };

    const handleKeyUp = (e: KeyboardEvent) => {
      if (shortcut === 'space' && e.code === 'Space') {
        if (isRecording) handleMouseUp();
      } else if (shortcut === 'ctrl+k' && e.ctrlKey && e.key === 'k') {
        if (isRecording) handleMouseUp();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('keyup', handleKeyUp);

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('keyup', handleKeyUp);
    };
  }, [isRecording]);

  const handleMouseDown = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      });
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        await processAudio(audioBlob);
        
        // Cleanup
        streamRef.current?.getTracks().forEach(track => track.stop());
        streamRef.current = null;
      };

      mediaRecorder.start();
      setIsRecording(true);
      setState('listening');
    } catch (error) {
      console.error('❌ Microphone access denied:', error);
      showToast('Microphone access denied. Please enable it in browser settings.', 'error');
    }
  };

  const handleMouseUp = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const processAudio = async (audioBlob: Blob) => {
    setState('thinking');

    try {
      const userId = localStorage.getItem('user_id') || 'web_user_001';
      const response = await apiService.sendAudio(audioBlob, userId);

      // Transcription
      const transcription = response.transcription || 'No transcription';
      setTranscription(transcription);
      addMessage('user', transcription);

      // Agent response (handle both conversation and action)
      const agentResponse = response.message || response.response || 'No response';
      addMessage('agent', agentResponse, response.metadata);

      // Audio playback (check settings)
      const audioData = response.audio;
      if (audioData && apiService.isAudioEnabled()) {
        setState('speaking');
        await audioService.playAudio(audioData);
        setState('idle');
      } else {
        if (audioData) {
          console.log('🔇 Audio muted by user settings');
        }
        setState('idle');
      }
    } catch (error: any) {
      console.error('❌ Error processing audio:', error);
      showToast(error.message || 'Failed to process audio', 'error');
      setState('idle');
    }
  };

  return (
    <div className="mic-button-container">
      <button
        className={`mic-button ${state === 'listening' ? 'recording' : ''}`}
        onMouseDown={handleMouseDown}
        onMouseUp={handleMouseUp}
        onMouseLeave={() => { if (isRecording) handleMouseUp(); }}
        disabled={state === 'thinking' || state === 'speaking'}
      >
        {state === 'listening' ? '🎙️' : '🎤'}
      </button>
      <p className="mic-hint">
        {state === 'idle' && 'Press and hold to speak'}
        {state === 'listening' && 'Listening...'}
        {state === 'thinking' && 'Processing...'}
        {state === 'speaking' && 'Speaking...'}
      </p>
    </div>
  );
};

export default MicButton;
```

### 🎨 Styling

```css
/* src/components/MicButton/MicButton.css */

.mic-button-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.mic-button {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  border: 3px solid #00d4ff;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  font-size: 2rem;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(0, 212, 255, 0.4);
}

.mic-button:hover {
  transform: scale(1.1);
  box-shadow: 0 6px 20px rgba(0, 212, 255, 0.6);
}

.mic-button.recording {
  animation: pulse 1s infinite;
  background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%);
  border-color: #ff6b6b;
}

.mic-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}

.mic-hint {
  font-size: 0.9rem;
  color: #888;
  text-align: center;
  min-height: 20px;
}
```

---

## 2. Avatar

### 📝 Description

Affiche les animations Lottie selon l'état de l'agent (idle, listening, thinking, speaking).

### 🎨 Interface

```typescript
interface AvatarProps {
  state: AgentState; // 'idle' | 'listening' | 'thinking' | 'speaking'
}
```

### 💡 Code

```typescript
// src/components/Avatar/Avatar.tsx

import Lottie from 'lottie-react';
import idleAnimation from '../../assets/animations/idle.json';
import listeningAnimation from '../../assets/animations/listening.json';
import thinkingAnimation from '../../assets/animations/thinking.json';
import speakingAnimation from '../../assets/animations/speaking.json';

interface AvatarProps {
  state: AgentState;
}

const Avatar: React.FC<AvatarProps> = ({ state }) => {
  const getAnimation = () => {
    switch (state) {
      case 'listening':
        return listeningAnimation;
      case 'thinking':
        return thinkingAnimation;
      case 'speaking':
        return speakingAnimation;
      default:
        return idleAnimation;
    }
  };

  const getLabel = () => {
    switch (state) {
      case 'listening':
        return '👂 Listening...';
      case 'thinking':
        return '🧠 Processing...';
      case 'speaking':
        return '💬 Speaking...';
      default:
        return '🤖 GOB Agent';
    }
  };

  return (
    <div className="avatar-container">
      <div className="avatar-circle">
        <Lottie
          animationData={getAnimation()}
          loop={true}
          autoplay={true}
          style={{ width: 200, height: 200 }}
        />
      </div>
      <h2 className="avatar-label">{getLabel()}</h2>
    </div>
  );
};

export default Avatar;
```

### 🎨 Styling

```css
/* src/components/Avatar/Avatar.css */

.avatar-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  margin-bottom: 2rem;
}

.avatar-circle {
  width: 220px;
  height: 220px;
  border-radius: 50%;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  border: 3px solid #00d4ff;
  box-shadow: 0 8px 32px rgba(0, 212, 255, 0.3);
  transition: all 0.3s ease;
}

.avatar-circle:hover {
  transform: scale(1.05);
  box-shadow: 0 12px 48px rgba(0, 212, 255, 0.5);
}

.avatar-label {
  font-size: 1.5rem;
  font-weight: 600;
  color: #333;
  text-align: center;
  margin: 0;
  transition: color 0.3s ease;
}

body.dark-mode .avatar-label {
  color: #eaeaea;
}

body.dark-mode .avatar-circle {
  border-color: #a78bfa;
  box-shadow: 0 8px 32px rgba(167, 139, 250, 0.3);
}
```

---

## 3. ActionPanel

### 📝 Description

Visualise les actions IoT en temps réel avec états, progression, et polling automatique.

### 🎨 Interface

```typescript
interface Action {
  action_id: string;
  current_state: string;
  action_json: ActionJSON;
  created_at: string;
  updated_at: string;
}

interface ActionJSON {
  device_type: string;
  action: string;
  location?: string;
  entities: Record<string, any>;
}
```

### 🔄 State Machine

```
DRAFT → PENDING_CONFIRMATION → CONFIRMED → EXECUTING → COMPLETED
                             ↘ CANCELED               ↘ FAILED
```

### 💡 Code Clé

```typescript
// src/components/ActionPanel/ActionPanel.tsx

const ActionPanel: React.FC = () => {
  const [actions, setActions] = useState<Action[]>([]);
  const [isExpanded, setIsExpanded] = useState(false);
  const [loading, setLoading] = useState(false);

  const userId = localStorage.getItem('user_id') || 'web_user_001';

  // Fetch actions
  const fetchActions = async () => {
    try {
      const data = await apiService.getActions(userId);
      setActions(data.actions || []);
    } catch (error) {
      console.error('Failed to fetch actions:', error);
    }
  };

  // Polling when expanded (10s interval)
  useEffect(() => {
    fetchActions();

    let interval: NodeJS.Timeout | null = null;

    if (isExpanded) {
      interval = setInterval(fetchActions, 10000); // 10 seconds
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [userId, isExpanded]);

  // Get state color
  const getStateColor = (state: string): string => {
    switch (state) {
      case 'PENDING_CONFIRMATION':
        return 'orange';
      case 'CONFIRMED':
      case 'EXECUTING':
        return 'violet';
      case 'COMPLETED':
        return 'green';
      case 'CANCELED':
      case 'FAILED':
        return 'red';
      default:
        return 'gray';
    }
  };

  // Get device icon
  const getDeviceIcon = (deviceType: string): string => {
    const icons: Record<string, string> = {
      lamp: '💡',
      light: '💡',
      door: '🚪',
      window: '🪟',
      tv: '📺',
      fan: '🌀',
      heater: '🔥',
      ac: '❄️',
      coffee: '☕',
      camera: '📷',
    };
    return icons[deviceType.toLowerCase()] || '🔌';
  };

  // Get progress percentage
  const getProgress = (state: string): number => {
    const progressMap: Record<string, number> = {
      'DRAFT': 10,
      'PENDING_CONFIRMATION': 20,
      'CONFIRMED': 50,
      'EXECUTING': 80,
      'COMPLETED': 100,
      'CANCELED': 0,
      'FAILED': 0,
    };
    return progressMap[state] || 0;
  };

  return (
    <div className="action-panel">
      <div className="action-panel-header" onClick={() => setIsExpanded(!isExpanded)}>
        <h3>⚡ Actions ({actions.length})</h3>
        <div className="action-panel-controls">
          <button onClick={(e) => { e.stopPropagation(); fetchActions(); }}>
            🔄
          </button>
          <span>{isExpanded ? '▼' : '▶'}</span>
        </div>
      </div>

      {isExpanded && (
        <div className="action-panel-content">
          {actions.length === 0 ? (
            <p className="no-actions">No actions yet</p>
          ) : (
            actions.map((action) => (
              <div key={action.action_id} className="action-item">
                <div className="action-header">
                  <span
                    className="action-state-indicator"
                    style={{ backgroundColor: getStateColor(action.current_state) }}
                  />
                  <span className="action-id">{action.action_id}</span>
                  <span className="action-state-label">{action.current_state}</span>
                </div>

                <div className="action-body">
                  <div className="action-device">
                    <span className="device-icon">
                      {getDeviceIcon(action.action_json.device_type)}
                    </span>
                    <span className="device-info">
                      <strong>{action.action_json.device_type}</strong>
                      {action.action_json.location && ` - ${action.action_json.location}`}
                    </span>
                  </div>

                  <div className="action-details">
                    <span>Action: {action.action_json.action}</span>
                    <span className="action-time">
                      ⏱️ {formatTime(action.updated_at)}
                    </span>
                  </div>

                  {/* Progress bar */}
                  <div className="action-progress-bar">
                    <div
                      className="action-progress-fill"
                      style={{
                        width: `${getProgress(action.current_state)}%`,
                        backgroundColor: getStateColor(action.current_state),
                      }}
                    />
                  </div>

                  <div className="action-message">
                    {action.current_state === 'PENDING_CONFIRMATION' && '⏳ Waiting for confirmation...'}
                    {action.current_state === 'CONFIRMED' && '✅ Confirmed, preparing...'}
                    {action.current_state === 'EXECUTING' && '🔄 Sending to smart home...'}
                    {action.current_state === 'COMPLETED' && '✅ Done!'}
                    {action.current_state === 'CANCELED' && '❌ Canceled'}
                    {action.current_state === 'FAILED' && '⚠️ Failed'}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
};

function formatTime(timestamp: string): string {
  const date = new Date(timestamp);
  const now = new Date();
  const diff = Math.floor((now.getTime() - date.getTime()) / 1000);

  if (diff < 60) return `${diff} seconds ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)} minutes ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)} hours ago`;
  return date.toLocaleDateString();
}

export default ActionPanel;
```

### 🎨 Styling

```css
/* src/components/ActionPanel/ActionPanel.css */

.action-panel {
  position: fixed;
  top: 80px;
  right: 20px;
  width: 350px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  z-index: 999;
  transition: all 0.3s ease;
}

.action-panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  cursor: pointer;
  user-select: none;
}

.action-panel-header h3 {
  margin: 0;
  font-size: 1.1rem;
}

.action-panel-controls {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.action-panel-controls button {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  padding: 0.3rem 0.5rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 1rem;
  transition: background 0.2s;
}

.action-panel-controls button:hover {
  background: rgba(255, 255, 255, 0.3);
}

.action-panel-content {
  max-height: 500px;
  overflow-y: auto;
  padding: 1rem;
}

.action-item {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 1rem;
  border-left: 4px solid #ccc;
  transition: all 0.2s;
}

.action-item:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.action-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.8rem;
}

.action-state-indicator {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.action-id {
  font-family: 'Courier New', monospace;
  font-size: 0.85rem;
  color: #666;
  flex: 1;
}

.action-state-label {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  color: #333;
}

.action-device {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.device-icon {
  font-size: 1.5rem;
}

.action-details {
  display: flex;
  justify-content: space-between;
  font-size: 0.85rem;
  color: #666;
  margin-bottom: 0.5rem;
}

.action-progress-bar {
  width: 100%;
  height: 6px;
  background: #e0e0e0;
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: 0.5rem;
}

.action-progress-fill {
  height: 100%;
  transition: width 0.3s ease;
}

.action-message {
  font-size: 0.85rem;
  color: #555;
  font-style: italic;
}

/* Dark mode */
body.dark-mode .action-panel {
  background: #16213e;
}

body.dark-mode .action-item {
  background: #1a1a2e;
  color: #eaeaea;
}

body.dark-mode .action-state-label {
  color: #eaeaea;
}
```

---

## 4. SettingsPanel

### 📝 Description

Modal de configuration utilisateur avec:
- Sélection langue (EN/FR/AR)
- Toggle audio
- Dark mode
- Raccourcis clavier

### 🎨 Interface

```typescript
interface Settings {
  language: 'en' | 'fr' | 'ar';
  audioEnabled: boolean;
  darkMode: boolean;
  keyboardShortcut: 'space' | 'ctrl+k';
}
```

### 💡 Code Clé

```typescript
// src/components/SettingsPanel/SettingsPanel.tsx

const SettingsPanel: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [settings, setSettings] = useState<Settings>({
    language: 'en',
    audioEnabled: true,
    darkMode: false,
    keyboardShortcut: 'space',
  });

  // Load from localStorage on mount
  useEffect(() => {
    const savedSettings = localStorage.getItem('gob-settings');
    if (savedSettings) {
      const parsed = JSON.parse(savedSettings);
      setSettings(parsed);
      applySettings(parsed);
    }
  }, []);

  const applySettings = (newSettings: Settings) => {
    // Apply dark mode
    if (newSettings.darkMode) {
      document.body.classList.add('dark-mode');
    } else {
      document.body.classList.remove('dark-mode');
    }

    // Dispatch event for other components
    window.dispatchEvent(new CustomEvent('settingsChanged', { detail: newSettings }));
  };

  const updateSettings = (partial: Partial<Settings>) => {
    const newSettings = { ...settings, ...partial };
    setSettings(newSettings);
    localStorage.setItem('gob-settings', JSON.stringify(newSettings));
    applySettings(newSettings);
  };

  const resetSettings = () => {
    const defaultSettings: Settings = {
      language: 'en',
      audioEnabled: true,
      darkMode: false,
      keyboardShortcut: 'space',
    };
    updateSettings(defaultSettings);
  };

  return (
    <>
      {/* Floating trigger button */}
      <button
        className="settings-trigger"
        onClick={() => setIsOpen(true)}
        title="Settings"
      >
        ⚙️
      </button>

      {/* Modal */}
      {isOpen && (
        <div className="settings-overlay" onClick={() => setIsOpen(false)}>
          <div className="settings-modal" onClick={(e) => e.stopPropagation()}>
            <div className="settings-header">
              <h2>⚙️ Settings</h2>
              <button className="settings-close" onClick={() => setIsOpen(false)}>
                ✕
              </button>
            </div>

            <div className="settings-body">
              {/* Language */}
              <div className="settings-section">
                <h3>🌐 Language</h3>
                <div className="language-options">
                  <div
                    className={`language-card ${settings.language === 'en' ? 'selected' : ''}`}
                    onClick={() => updateSettings({ language: 'en' })}
                  >
                    <span className="flag">🇬🇧</span>
                    <span>English</span>
                  </div>
                  <div
                    className={`language-card ${settings.language === 'fr' ? 'selected' : ''}`}
                    onClick={() => updateSettings({ language: 'fr' })}
                  >
                    <span className="flag">🇫🇷</span>
                    <span>Français</span>
                  </div>
                  <div
                    className={`language-card ${settings.language === 'ar' ? 'selected' : ''}`}
                    onClick={() => updateSettings({ language: 'ar' })}
                  >
                    <span className="flag">🇸🇦</span>
                    <span>العربية</span>
                  </div>
                </div>
              </div>

              {/* Audio Toggle */}
              <div className="settings-section">
                <h3>🔊 Audio Output</h3>
                <label className="toggle-switch">
                  <input
                    type="checkbox"
                    checked={settings.audioEnabled}
                    onChange={(e) => updateSettings({ audioEnabled: e.target.checked })}
                  />
                  <span className="toggle-slider"></span>
                  <span className="toggle-label">
                    {settings.audioEnabled ? 'Enabled' : 'Disabled'}
                  </span>
                </label>
              </div>

              {/* Dark Mode */}
              <div className="settings-section">
                <h3>🌙 Dark Mode</h3>
                <label className="toggle-switch">
                  <input
                    type="checkbox"
                    checked={settings.darkMode}
                    onChange={(e) => updateSettings({ darkMode: e.target.checked })}
                  />
                  <span className="toggle-slider"></span>
                  <span className="toggle-label">
                    {settings.darkMode ? 'On' : 'Off'}
                  </span>
                </label>
              </div>

              {/* Keyboard Shortcut */}
              <div className="settings-section">
                <h3>⌨️ Keyboard Shortcut</h3>
                <div className="keyboard-options">
                  <label>
                    <input
                      type="radio"
                      name="shortcut"
                      value="space"
                      checked={settings.keyboardShortcut === 'space'}
                      onChange={() => updateSettings({ keyboardShortcut: 'space' })}
                    />
                    <span>SPACE</span>
                  </label>
                  <label>
                    <input
                      type="radio"
                      name="shortcut"
                      value="ctrl+k"
                      checked={settings.keyboardShortcut === 'ctrl+k'}
                      onChange={() => updateSettings({ keyboardShortcut: 'ctrl+k' })}
                    />
                    <span>CTRL + K</span>
                  </label>
                </div>
              </div>

              {/* Reset */}
              <div className="settings-section">
                <button className="reset-button" onClick={resetSettings}>
                  Reset to Defaults
                </button>
              </div>
            </div>

            <div className="settings-footer">
              <p>Version: 1.0.0</p>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default SettingsPanel;
```

### 🎨 Styling

```css
/* src/components/SettingsPanel/SettingsPanel.css */

.settings-trigger {
  position: fixed;
  top: 20px;
  right: 20px;
  width: 50px;
  height: 50px;
  border-radius: 50%;
  border: none;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  font-size: 1.5rem;
  cursor: pointer;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
  transition: all 0.3s ease;
  z-index: 1000;
}

.settings-trigger:hover {
  transform: scale(1.1) rotate(90deg);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
}

.settings-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1100;
  animation: fadeIn 0.2s ease;
}

.settings-modal {
  background: white;
  border-radius: 16px;
  width: 500px;
  max-width: 90vw;
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: 0 10px 50px rgba(0, 0, 0, 0.3);
  animation: slideUp 0.3s ease;
}

.settings-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 2px solid #f0f0f0;
}

.settings-header h2 {
  margin: 0;
  font-size: 1.5rem;
}

.settings-close {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #999;
  transition: color 0.2s;
}

.settings-close:hover {
  color: #333;
}

.settings-body {
  padding: 1.5rem;
}

.settings-section {
  margin-bottom: 2rem;
}

.settings-section h3 {
  margin-top: 0;
  margin-bottom: 1rem;
  font-size: 1.1rem;
  color: #333;
}

.language-options {
  display: flex;
  gap: 1rem;
}

.language-card {
  flex: 1;
  padding: 1rem;
  border: 2px solid #ddd;
  border-radius: 8px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
}

.language-card:hover {
  border-color: #667eea;
  transform: translateY(-2px);
}

.language-card.selected {
  border-color: #667eea;
  background: rgba(102, 126, 234, 0.1);
}

.language-card .flag {
  font-size: 2rem;
  display: block;
  margin-bottom: 0.5rem;
}

.toggle-switch {
  display: flex;
  align-items: center;
  gap: 1rem;
  cursor: pointer;
}

.toggle-switch input[type="checkbox"] {
  display: none;
}

.toggle-slider {
  width: 50px;
  height: 26px;
  background: #ccc;
  border-radius: 13px;
  position: relative;
  transition: background 0.3s;
}

.toggle-slider::before {
  content: '';
  position: absolute;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: white;
  top: 3px;
  left: 3px;
  transition: transform 0.3s;
}

.toggle-switch input:checked + .toggle-slider {
  background: #667eea;
}

.toggle-switch input:checked + .toggle-slider::before {
  transform: translateX(24px);
}

.keyboard-options {
  display: flex;
  gap: 1rem;
}

.keyboard-options label {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.8rem;
  border: 2px solid #ddd;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.keyboard-options label:hover {
  border-color: #667eea;
}

.keyboard-options input:checked + span {
  color: #667eea;
  font-weight: 600;
}

.reset-button {
  width: 100%;
  padding: 0.8rem;
  border: 2px solid #ff6b6b;
  background: white;
  color: #ff6b6b;
  border-radius: 8px;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.2s;
}

.reset-button:hover {
  background: #ff6b6b;
  color: white;
}

.settings-footer {
  padding: 1rem 1.5rem;
  border-top: 2px solid #f0f0f0;
  text-align: center;
  color: #999;
  font-size: 0.85rem;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideUp {
  from {
    transform: translateY(50px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

/* Dark mode */
body.dark-mode .settings-modal {
  background: #16213e;
}

body.dark-mode .settings-header {
  border-bottom-color: #0f3460;
}

body.dark-mode .settings-section h3,
body.dark-mode .settings-close:hover {
  color: #eaeaea;
}

body.dark-mode .language-card,
body.dark-mode .keyboard-options label {
  border-color: #0f3460;
  color: #eaeaea;
}

body.dark-mode .language-card:hover,
body.dark-mode .keyboard-options label:hover {
  border-color: #a78bfa;
}

body.dark-mode .language-card.selected {
  background: rgba(167, 139, 250, 0.2);
  border-color: #a78bfa;
}
```

---

## 📊 Résumé des Composants

| Composant | Lignes CSS | Lignes TSX | État | Dépendances |
|-----------|-----------|-----------|------|-------------|
| MicButton | 80 | 150 | Zustand | MediaRecorder, apiService |
| Avatar | 60 | 50 | Props | lottie-react |
| Waveform | 40 | 30 | Props | Canvas API |
| Toast | 50 | 40 | Zustand | setTimeout |
| EntityBadge | 30 | 20 | Props | - |
| ConversationHistory | 100 | 80 | Zustand | useRef (scroll) |
| MemoryPanel | 120 | 100 | State | apiService |
| ActionPanel | 150 | 200 | State | apiService, polling |
| SettingsPanel | 200 | 150 | State | localStorage |
| AgentScreen | 100 | 120 | Zustand | All components |

**Total: ~930 lignes CSS + ~940 lignes TSX = 1870 lignes frontend**

---

**Version**: 1.0.0  
**Dernière mise à jour**: 14 février 2026
