/**
 * WakeWordPanel - Configuration du wake word dans les settings
 */

import { useState } from 'react';
import { useAgentStore } from '../../store/agentStore';
import { wakeWordService } from '../../services/wakeWordService';
import './WakeWordPanel.css';

export function WakeWordPanel() {
  const [inputValue, setInputValue] = useState('');
  const { wakeWord, wakeMode, setWakeWord, showToast } = useAgentStore();
  
  const handleSave = () => {
    const trimmed = inputValue.trim();
    if (!trimmed) {
      showToast('Wake word cannot be empty', 'warning');
      return;
    }
    
    setWakeWord(trimmed);
    wakeWordService.setWakeWord(trimmed);
    setInputValue('');
    showToast(`Wake word set to: ${trimmed}`, 'success');
  };
  
  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleSave();
    }
  };
  
  return (
    <div className="wake-word-panel">
      <h3 className="wake-word-title">Wake Word Configuration</h3>
      <p className="wake-word-description">
        Set a custom wake word. The agent will listen for this word in wake mode.
      </p>
      
      <div className="wake-word-input-group">
        <input
          type="text"
          placeholder="e.g., hi gob, hey assistant..."
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyPress={handleKeyPress}
          className="wake-word-input"
          disabled={wakeMode}
        />
        <button 
          onClick={handleSave} 
          className="wake-save-btn"
          disabled={wakeMode || !inputValue.trim()}
        >
          Save
        </button>
      </div>
      
      {wakeMode && (
        <div className="wake-word-warning">
          ⚠️ Disable wake mode to change the wake word
        </div>
      )}
      
      <div className="wake-word-current">
        {wakeWord ? (
          <>
            <span className="wake-word-label">Current wake word:</span>
            <span className="wake-word-value">{wakeWord}</span>
          </>
        ) : (
          <span className="wake-word-empty">No wake word set</span>
        )}
      </div>
      
      {!wakeWordService.isSupported() && (
        <div className="wake-word-unsupported">
          ❌ Speech Recognition not supported in this browser
        </div>
      )}
    </div>
  );
}
