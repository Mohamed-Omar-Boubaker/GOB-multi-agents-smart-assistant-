import React, { useState, useEffect, useRef } from 'react';
import { WakeWordPanel } from '../WakeWordPanel/WakeWordPanel';
import API_CONFIG from '../../config/api.config';
import './SettingsPanel.css';

interface Settings {
  language: 'en' | 'fr' | 'ar';
  audioEnabled: boolean;
  darkMode: boolean;
  keyboardShortcut: 'space' | 'ctrl+k';
}

interface SettingsPanelProps {
  onSettingsChange?: (settings: Settings) => void;
}

const LANGUAGES = [
  { code: 'en', label: 'English', flag: '🇬🇧' },
  { code: 'fr', label: 'Français', flag: '🇫🇷' },
  { code: 'ar', label: 'العربية', flag: '🇸🇦' }
];

const SettingsPanel: React.FC<SettingsPanelProps> = ({ onSettingsChange }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [settings, setSettings] = useState<Settings>({
    language: 'fr',
    audioEnabled: true,
    darkMode: false,
    keyboardShortcut: 'space'
  });
  const [fabPosition, setFabPosition] = useState({ x: 0, y: 0 });
  const backendLabel = API_CONFIG.BASE_URL.replace(/^https?:\/\//, '');
  const dragStateRef = useRef({
    dragging: false,
    moved: false,
    startX: 0,
    startY: 0,
    offsetX: 0,
    offsetY: 0
  });

  // Charger les paramètres depuis localStorage
  useEffect(() => {
    const savedSettings = localStorage.getItem('gob-settings');
    if (savedSettings) {
      try {
        const parsed = JSON.parse(savedSettings);
        setSettings(parsed);
        applySettings(parsed);
      } catch (e) {
        console.error('Failed to load settings', e);
      }
    }
  }, []);

  useEffect(() => {
    const setDefaultPosition = () => {
      const margin = 16;
      const size = 50;
      const x = Math.max(margin, window.innerWidth - size - margin);
      const y = Math.max(margin, margin);
      setFabPosition({ x, y });
    };

    setDefaultPosition();
    window.addEventListener('resize', setDefaultPosition);

    return () => {
      window.removeEventListener('resize', setDefaultPosition);
    };
  }, []);

  const handleFabPointerDown = (event: React.PointerEvent<HTMLButtonElement>) => {
    const button = event.currentTarget;
    button.setPointerCapture(event.pointerId);

    dragStateRef.current.dragging = true;
    dragStateRef.current.moved = false;
    dragStateRef.current.startX = event.clientX;
    dragStateRef.current.startY = event.clientY;
    dragStateRef.current.offsetX = event.clientX - fabPosition.x;
    dragStateRef.current.offsetY = event.clientY - fabPosition.y;
  };

  const handleFabPointerMove = (event: React.PointerEvent<HTMLButtonElement>) => {
    if (!dragStateRef.current.dragging) return;

    const deltaX = Math.abs(event.clientX - dragStateRef.current.startX);
    const deltaY = Math.abs(event.clientY - dragStateRef.current.startY);
    if (deltaX > 4 || deltaY > 4) {
      dragStateRef.current.moved = true;
    }

    const size = 50;
    const margin = 8;
    const maxX = window.innerWidth - size - margin;
    const maxY = window.innerHeight - size - margin;
    const nextX = Math.min(Math.max(margin, event.clientX - dragStateRef.current.offsetX), maxX);
    const nextY = Math.min(Math.max(margin, event.clientY - dragStateRef.current.offsetY), maxY);

    setFabPosition({ x: nextX, y: nextY });
  };

  const handleFabPointerUp = (event: React.PointerEvent<HTMLButtonElement>) => {
    const button = event.currentTarget;
    button.releasePointerCapture(event.pointerId);

    const wasMoved = dragStateRef.current.moved;
    dragStateRef.current.dragging = false;

    if (!wasMoved) {
      setIsOpen(true);
    }
  };

  // Appliquer les paramètres (dark mode, etc.)
  const applySettings = (newSettings: Settings) => {
    // Dark mode
    if (newSettings.darkMode) {
      document.body.classList.add('dark-mode');
    } else {
      document.body.classList.remove('dark-mode');
    }

    // Callback
    onSettingsChange?.(newSettings);
  };

  // Sauvegarder et appliquer
  const updateSettings = (partial: Partial<Settings>) => {
    const newSettings = { ...settings, ...partial };
    setSettings(newSettings);
    localStorage.setItem('gob-settings', JSON.stringify(newSettings));
    applySettings(newSettings);
    
    console.log('⚙️ Settings updated:', newSettings);
  };

  const resetSettings = () => {
    const defaultSettings: Settings = {
      language: 'fr',
      audioEnabled: true,
      darkMode: false,
      keyboardShortcut: 'space'
    };
    setSettings(defaultSettings);
    localStorage.removeItem('gob-settings');
    applySettings(defaultSettings);
    console.log('🔄 Settings reset to default');
  };

  return (
    <>
      {/* Bouton flottant pour ouvrir les paramètres */}
      <button 
        className="settings-trigger"
        style={{ left: `${fabPosition.x}px`, top: `${fabPosition.y}px` }}
        onPointerDown={handleFabPointerDown}
        onPointerMove={handleFabPointerMove}
        onPointerUp={handleFabPointerUp}
        onPointerCancel={handleFabPointerUp}
        title="Settings"
      >
        ⚙️
      </button>

      {/* Modal overlay */}
      {isOpen && (
        <div className="settings-overlay" onClick={() => setIsOpen(false)}>
          <div className="settings-panel" onClick={(e) => e.stopPropagation()}>
            {/* Header */}
            <div className="settings-header">
              <div className="settings-title">
                <span className="settings-icon">⚙️</span>
                <h2>Settings</h2>
              </div>
              <button 
                className="settings-close"
                onClick={() => setIsOpen(false)}
              >
                ✕
              </button>
            </div>

            {/* Content */}
            <div className="settings-content">
              
              {/* Language Selection */}
              <div className="settings-section">
                <div className="settings-section-title">
                  <span className="section-icon">🌐</span>
                  <span>Language</span>
                </div>
                <div className="language-options">
                  {LANGUAGES.map((lang) => (
                    <button
                      key={lang.code}
                      className={`language-option ${settings.language === lang.code ? 'active' : ''}`}
                      onClick={() => updateSettings({ language: lang.code as any })}
                    >
                      <span className="language-flag">{lang.flag}</span>
                      <span className="language-label">{lang.label}</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Audio Toggle */}
              <div className="settings-section">
                <div className="settings-section-title">
                  <span className="section-icon">🔊</span>
                  <span>Audio Feedback</span>
                </div>
                <div className="settings-row">
                  <div className="settings-description">
                    Play audio responses from the agent
                  </div>
                  <label className="toggle-switch">
                    <input
                      type="checkbox"
                      checked={settings.audioEnabled}
                      onChange={(e) => updateSettings({ audioEnabled: e.target.checked })}
                    />
                    <span className="toggle-slider"></span>
                  </label>
                </div>
              </div>

              {/* Wake Word Configuration */}
              <div className="settings-section">
                <div className="settings-section-title">
                  <span className="section-icon">🎙️</span>
                  <span>Wake Word</span>
                </div>
                <WakeWordPanel />
              </div>

              {/* Dark Mode Toggle */}
              <div className="settings-section">
                <div className="settings-section-title">
                  <span className="section-icon">🌙</span>
                  <span>Dark Mode</span>
                </div>
                <div className="settings-row">
                  <div className="settings-description">
                    Enable dark theme for better night viewing
                  </div>
                  <label className="toggle-switch">
                    <input
                      type="checkbox"
                      checked={settings.darkMode}
                      onChange={(e) => updateSettings({ darkMode: e.target.checked })}
                    />
                    <span className="toggle-slider"></span>
                  </label>
                </div>
              </div>

              {/* Keyboard Shortcut */}
              <div className="settings-section">
                <div className="settings-section-title">
                  <span className="section-icon">⌨️</span>
                  <span>Keyboard Shortcut</span>
                </div>
                <div className="keyboard-options">
                  <button
                    className={`keyboard-option ${settings.keyboardShortcut === 'space' ? 'active' : ''}`}
                    onClick={() => updateSettings({ keyboardShortcut: 'space' })}
                  >
                    <span className="keyboard-key">SPACE</span>
                    <span className="keyboard-label">Hold to talk</span>
                  </button>
                  <button
                    className={`keyboard-option ${settings.keyboardShortcut === 'ctrl+k' ? 'active' : ''}`}
                    onClick={() => updateSettings({ keyboardShortcut: 'ctrl+k' })}
                  >
                    <span className="keyboard-key">CTRL + K</span>
                    <span className="keyboard-label">Quick command</span>
                  </button>
                </div>
              </div>

              {/* Info Section */}
              <div className="settings-section settings-info">
                <div className="info-item">
                  <span className="info-label">Version</span>
                  <span className="info-value">1.0.0</span>
                </div>
                <div className="info-item">
                  <span className="info-label">Backend</span>
                  <span className="info-value">{backendLabel}</span>
                </div>
              </div>

            </div>

            {/* Footer */}
            <div className="settings-footer">
              <button 
                className="settings-reset"
                onClick={resetSettings}
              >
                🔄 Reset to Default
              </button>
              <button 
                className="settings-save"
                onClick={() => setIsOpen(false)}
              >
                ✓ Done
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default SettingsPanel;
