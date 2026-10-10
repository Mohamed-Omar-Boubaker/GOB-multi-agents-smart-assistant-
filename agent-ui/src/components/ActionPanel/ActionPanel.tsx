import React, { useState, useEffect, useRef } from 'react';
import './ActionPanel.css';

interface ActionEntity {
  device_type?: string;
  action?: string;
  location?: string;
  recipient?: string;
  subject?: string;
  [key: string]: any;
}

interface Action {
  action_id: string;
  current_state: string;
  intent: string;
  original_text: string;
  timestamp: string;
  entities: ActionEntity;
  language: string;
}

interface ActionPanelProps {
  userId: string;
}

// Mapping icons par intent
const INTENT_ICONS: Record<string, string> = {
  control_iot: '💡',
  send_email: '📧',
  query_status: '❓',
  set_reminder: '⏰',
  control_temperature: '🌡️',
  control_light: '💡',
  control_door: '🚪',
  control_window: '🪟',
  play_music: '🎵',
  default: '⚙️'
};

// Mapping couleurs par état
const STATE_COLORS: Record<string, string> = {
  DRAFT: '#9e9e9e',
  PENDING_CONFIRMATION: '#ff9800',
  CONFIRMED: '#2196f3',
  EXECUTING: '#673ab7',
  COMPLETED: '#4caf50',
  CANCELED: '#607d8b',
  FAILED: '#f44336'
};

// Mapping libellés par état
const STATE_LABELS: Record<string, string> = {
  DRAFT: 'Draft',
  PENDING_CONFIRMATION: 'Awaiting Confirmation',
  CONFIRMED: 'Confirmed',
  EXECUTING: 'Executing',
  COMPLETED: 'Completed',
  CANCELED: 'Canceled',
  FAILED: 'Failed'
};

const ActionPanel: React.FC<ActionPanelProps> = ({ userId }) => {
  const [actions, setActions] = useState<Action[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isExpanded, setIsExpanded] = useState(false);
  const [fabPosition, setFabPosition] = useState({ x: 0, y: 0 });
  const dragStateRef = useRef({
    dragging: false,
    moved: false,
    startX: 0,
    startY: 0,
    offsetX: 0,
    offsetY: 0
  });

  const fetchActions = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`/api/actions/${userId}?limit=10`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      setActions(data.actions || []);
    } catch (err) {
      console.error('Error fetching actions:', err);
      setError('Failed to load actions');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchActions();
    
    // Refresh only when panel is expanded (smart polling)
    let interval: number | null = null;
    
    if (isExpanded) {
      interval = setInterval(fetchActions, 10000); // 10 seconds
    }
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [userId, isExpanded]);

  useEffect(() => {
    const setDefaultPosition = () => {
      const margin = 16;
      const size = 50;
      const x = margin;
      const y = Math.max(margin, window.innerHeight - size - 120);
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
      setIsExpanded((prev) => !prev);
    }
  };


  const getActionIcon = (intent: string, entities: ActionEntity): string => {
    // Try specific device type first
    if (entities.device_type) {
      const deviceIcons: Record<string, string> = {
        light: '💡',
        lamp: '💡',
        door: '🚪',
        window: '🪟',
        thermostat: '🌡️',
        speaker: '🔊',
        tv: '📺',
        camera: '📷'
      };
      const icon = deviceIcons[entities.device_type.toLowerCase()];
      if (icon) return icon;
    }

    // Fallback to intent
    return INTENT_ICONS[intent] || INTENT_ICONS.default;
  };

  const getActionDescription = (action: Action): string => {
    const { entities } = action;
    
    if (entities.device_type && entities.action) {
      const location = entities.location ? ` in ${entities.location}` : '';
      return `${entities.action} ${entities.device_type}${location}`;
    }
    
    if (entities.recipient) {
      return `Email to ${entities.recipient}`;
    }
    
    return action.original_text;
  };

  const formatTimestamp = (timestamp: string): string => {
    try {
      const date = new Date(timestamp);
      const now = new Date();
      const diffMs = now.getTime() - date.getTime();
      const diffMins = Math.floor(diffMs / 60000);
      
      if (diffMins < 1) return 'just now';
      if (diffMins < 60) return `${diffMins}m ago`;
      
      const diffHours = Math.floor(diffMins / 60);
      if (diffHours < 24) return `${diffHours}h ago`;
      
      return date.toLocaleDateString();
    } catch {
      return 'Unknown';
    }
  };

  const getStateProgressPercent = (state: string): number => {
    const stateProgression = {
      DRAFT: 10,
      PENDING_CONFIRMATION: 30,
      CONFIRMED: 50,
      EXECUTING: 70,
      COMPLETED: 100,
      CANCELED: 100,
      FAILED: 100
    };
    return stateProgression[state as keyof typeof stateProgression] || 0;
  };

  return (
    <>
      <button
        className={`action-panel-fab ${isExpanded ? 'open' : ''}`}
        title="IoT"
        aria-hidden={false}
        tabIndex={0}
        style={{ left: `${fabPosition.x}px`, top: `${fabPosition.y}px` }}
        onPointerDown={handleFabPointerDown}
        onPointerMove={handleFabPointerMove}
        onPointerUp={handleFabPointerUp}
        onPointerCancel={handleFabPointerUp}
      >
        📡
      </button>

      <div className={`action-panel ${!isExpanded ? 'collapsed' : ''}`}>
        <div className="action-panel-header" onClick={() => setIsExpanded(!isExpanded)}>
        <div className="action-panel-title">
          <span className="action-panel-icon" aria-hidden="true">📡</span>
          <span>Actions IoT</span>
          <span className="action-panel-count">({actions.length})</span>
        </div>
        <button className="action-panel-toggle">
          {isExpanded ? '▶' : '◀'}
        </button>
      </div>

      {isExpanded && (
        <div className="action-panel-content">
          {loading && actions.length === 0 ? (
            <div className="action-panel-loading">Loading actions...</div>
          ) : error ? (
            <div className="action-panel-error">
              <p>{error}</p>
              <button onClick={fetchActions} className="action-refresh-btn">
                Retry
              </button>
            </div>
          ) : actions.length === 0 ? (
            <div className="action-panel-empty">
              <span className="empty-icon">📋</span>
              <p>No actions yet</p>
            </div>
          ) : (
            <div className="action-list">
              {actions.map((action, index) => (
                <div
                  key={action.action_id}
                  className={`action-item action-state-${action.current_state.toLowerCase()}`}
                  style={{ animationDelay: `${index * 0.05}s` }}
                >
                  <div className="action-icon-wrapper">
                    <span className="action-icon">
                      {getActionIcon(action.intent, action.entities)}
                    </span>
                  </div>
                  
                  <div className="action-details">
                    <div className="action-description">
                      {getActionDescription(action)}
                    </div>
                    <div className="action-meta">
                      <span className="action-timestamp">
                        {formatTimestamp(action.timestamp)}
                      </span>
                      <span 
                        className="action-state-badge"
                        style={{ 
                          backgroundColor: STATE_COLORS[action.current_state],
                          color: 'white'
                        }}
                      >
                        {STATE_LABELS[action.current_state] || action.current_state}
                      </span>
                    </div>
                    
                    {/* Progress bar */}
                    <div className="action-progress-bar">
                      <div 
                        className="action-progress-fill"
                        style={{ 
                          width: `${getStateProgressPercent(action.current_state)}%`,
                          backgroundColor: STATE_COLORS[action.current_state]
                        }}
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
          
          <div className="action-panel-footer">
            <button onClick={fetchActions} className="action-refresh-btn" disabled={loading}>
              {loading ? '⟳' : '🔄'} Refresh
            </button>
          </div>
        </div>
      )}
      </div>
    </>
  );
};

export default ActionPanel;
