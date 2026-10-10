/**
 * ConversationHistory Component - Historique des messages
 * Phase 4B: Affichage chronologique des échanges
 */

import { useEffect, useRef, useState } from 'react';
import './ConversationHistory.css';

export interface Message {
  id: string;
  sender: 'user' | 'agent';
  text: string;
  timestamp: Date;
  emotion?: string;
  entities?: Array<{ name: string; type: string }>;
}

interface ConversationHistoryProps {
  messages: Message[];
}

export function ConversationHistory({ messages }: ConversationHistoryProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [isCollapsed, setIsCollapsed] = useState(false);
  
  // Auto-scroll vers le bas quand nouveau message
  useEffect(() => {
    if (!isCollapsed && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isCollapsed]);
  
  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('fr-FR', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };
  
  const getEmotionEmoji = (emotion?: string) => {
    const emojiMap: Record<string, string> = {
      happy: '😊',
      sad: '😢',
      angry: '😠',
      excited: '🤩',
      neutral: '😐',
      tired: '😴',
      confused: '😕'
    };
    return emotion ? emojiMap[emotion] || '' : '';
  };
  
  return (
    <section className={`conversation-panel ${isCollapsed ? 'collapsed' : ''}`}>
      <button
        type="button"
        className="conversation-toggle"
        onClick={() => setIsCollapsed((prev) => !prev)}
        aria-expanded={!isCollapsed}
        aria-label={isCollapsed ? 'Expand conversation' : 'Collapse conversation'}
      >
        <div className="conversation-title-wrap">
          <span className="conversation-title">Conversation</span>
          <span className="conversation-count">{messages.length}</span>
        </div>
        <span className="conversation-chevron" aria-hidden="true">▾</span>
      </button>

      <div className="conversation-body">
        <div className="conversation-body-inner">
          {messages.length === 0 ? (
            <div className="conversation-history empty">
              <div className="empty-state">
                <div className="empty-icon">💬</div>
                <p>No conversation yet</p>
                <span>Press the button and start talking!</span>
              </div>
            </div>
          ) : (
            <div className="conversation-history" ref={scrollRef}>
              {messages.map((message) => (
                <div 
                  key={message.id} 
                  className={`message ${message.sender}`}
                >
                  <div className="message-avatar">
                    {message.sender === 'user' ? '👤' : '🤖'}
                  </div>
                  
                  <div className="message-content">
                    <div className="message-header">
                      <span className="message-sender">
                        {message.sender === 'user' ? 'You' : 'GOB Agent'}
                      </span>
                      <span className="message-time">{formatTime(message.timestamp)}</span>
                      {message.emotion && (
                        <span className="message-emotion" title={message.emotion}>
                          {getEmotionEmoji(message.emotion)}
                        </span>
                      )}
                    </div>
                    
                    <div className="message-text">{message.text}</div>
                    
                    {message.entities && message.entities.length > 0 && (
                      <div className="message-entities">
                        {message.entities.map((entity, idx) => (
                          <span key={idx} className="mini-entity">
                            {entity.name}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
