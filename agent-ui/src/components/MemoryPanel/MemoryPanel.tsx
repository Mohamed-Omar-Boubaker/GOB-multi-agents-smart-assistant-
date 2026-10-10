/**
 * MemoryPanel Component - Affiche ce que l'agent sait sur l'utilisateur
 * Phase 4C: Visualisation des facts mémorisés
 */

import { useEffect, useState } from 'react';
import { buildURL } from '../../config/api.config';
import './MemoryPanel.css';

interface Fact {
  id: number;
  fact_type: string;
  fact_key: string;
  fact_value: string;
  confidence: number;
  timestamp: string;
}

interface MemoryData {
  user_id: string;
  total_facts: number;
  facts: Fact[];
  recent_emotions: string[];
  preferences: Record<string, string>;
}

interface MemoryPanelProps {
  userId: string;
}

export function MemoryPanel({ userId }: MemoryPanelProps) {
  const [memory, setMemory] = useState<MemoryData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isExpanded, setIsExpanded] = useState(false);
  
  useEffect(() => {
    fetchMemory();
  }, [userId]);
  
  const fetchMemory = async () => {
    try {
      setLoading(true);
      const response = await fetch(buildURL(`/memory/${encodeURIComponent(userId)}`));
      
      if (!response.ok) {
        throw new Error('Could not fetch memory');
      }
      
      const data = await response.json();
      setMemory(data);
      setError(null);
    } catch (err) {
      console.error('Memory fetch error:', err);
      setError('Memory not available');
    } finally {
      setLoading(false);
    }
  };
  
  const getFactIcon = (factType: string) => {
    const icons: Record<string, string> = {
      person: '👤',
      preference: '❤️',
      food: '🍕',
      drink: '☕',
      emotion: '😊',
      location: '📍',
      device: '💡',
      skill: '🎯',
      hobby: '🎨',
      default: '📝'
    };
    return icons[factType] || icons.default;
  };
  
  if (loading) {
    return (
      <div className="memory-panel loading">
        <div className="memory-header">
          <span className="memory-icon">🧠</span>
          <h3>Memory</h3>
        </div>
        <p className="loading-text">Loading memory...</p>
      </div>
    );
  }
  
  if (error || !memory) {
    return (
      <div className="memory-panel empty">
        <div className="memory-header">
          <span className="memory-icon">🧠</span>
          <h3>Memory</h3>
        </div>
        <p className="empty-text">No memory yet. Talk to me!</p>
      </div>
    );
  }
  
  return (
    <div className={`memory-panel ${isExpanded ? 'expanded' : ''}`}>
      <div className="memory-header" onClick={() => setIsExpanded(!isExpanded)}>
        <span className="memory-icon">🧠</span>
        <h3>What I Remember</h3>
        <span className="fact-count">{memory.total_facts}</span>
        <button className="expand-button">
          {isExpanded ? '▼' : '▶'}
        </button>
      </div>
      
      {isExpanded && (
        <div className="memory-content">
          {/* User Info */}
          <div className="memory-section">
            <h4>👤 About You</h4>
            {memory.facts
              .filter(f => f.fact_type === 'person' || f.fact_key.includes('name'))
              .map(fact => (
                <div key={fact.id} className="fact-item">
                  <span className="fact-icon">{getFactIcon(fact.fact_type)}</span>
                  <span className="fact-text">
                    <strong>{fact.fact_key}:</strong> {fact.fact_value}
                  </span>
                  <span className="fact-confidence">{Math.round(fact.confidence * 100)}%</span>
                </div>
              ))}
          </div>
          
          {/* Preferences */}
          {memory.facts.filter(f => f.fact_type === 'food' || f.fact_type === 'drink' || f.fact_type === 'preference').length > 0 && (
            <div className="memory-section">
              <h4>❤️ Your Preferences</h4>
              {memory.facts
                .filter(f => f.fact_type === 'food' || f.fact_type === 'drink' || f.fact_type === 'preference')
                .map(fact => (
                  <div key={fact.id} className="fact-item">
                    <span className="fact-icon">{getFactIcon(fact.fact_type)}</span>
                    <span className="fact-text">
                      You like <strong>{fact.fact_value}</strong>
                    </span>
                  </div>
                ))}
            </div>
          )}
          
          {/* Recent Emotions */}
          {memory.recent_emotions && memory.recent_emotions.length > 0 && (
            <div className="memory-section">
              <h4>😊 Recent Emotions</h4>
              <div className="emotion-tags">
                {memory.recent_emotions.map((emotion, idx) => (
                  <span key={idx} className="emotion-tag">
                    {emotion}
                  </span>
                ))}
              </div>
            </div>
          )}
          
          {/* Other Facts */}
          {memory.facts
            .filter(f => !['person', 'food', 'drink', 'preference'].includes(f.fact_type) && !f.fact_key.includes('name'))
            .length > 0 && (
            <div className="memory-section">
              <h4>📝 Other Information</h4>
              {memory.facts
                .filter(f => !['person', 'food', 'drink', 'preference'].includes(f.fact_type))
                .slice(0, 5)
                .map(fact => (
                  <div key={fact.id} className="fact-item">
                    <span className="fact-icon">{getFactIcon(fact.fact_type)}</span>
                    <span className="fact-text">
                      <strong>{fact.fact_key}:</strong> {fact.fact_value}
                    </span>
                  </div>
                ))}
            </div>
          )}
          
          <button className="refresh-button" onClick={fetchMemory}>
            🔄 Refresh Memory
          </button>
        </div>
      )}
    </div>
  );
}
