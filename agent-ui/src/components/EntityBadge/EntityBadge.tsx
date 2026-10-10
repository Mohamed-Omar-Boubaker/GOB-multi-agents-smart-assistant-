/**
 * EntityBadge Component - Affiche une entity avec son icône
 * Phase 4A: Visualisation des entities extraites
 */

import './EntityBadge.css';
import type { Entity } from '../../types';

interface EntityBadgeProps {
  entity: Entity;
  index: number;
}

// Mapping des types d'entities vers des emojis/icônes
const ENTITY_ICONS: Record<string, string> = {
  // Personnes
  person: '👤',
  user: '👤',
  name: '👤',
  
  // Nourriture & Boissons
  food: '🍕',
  drink: '☕',
  pizza: '🍕',
  coffee: '☕',
  tea: '🍵',
  burger: '🍔',
  pasta: '🍝',
  
  // Objets & Devices
  object: '📦',
  device: '💡',
  lamp: '💡',
  light: '💡',
  tv: '📺',
  phone: '📱',
  computer: '💻',
  watch: '⌚',
  
  // Lieux
  location: '📍',
  place: '🏠',
  city: '🌆',
  country: '🌍',
  
  // Émotions
  emotion: '😊',
  happy: '😊',
  sad: '😢',
  angry: '😠',
  excited: '🤩',
  tired: '😴',
  
  // Temps
  time: '⏰',
  date: '📅',
  
  // Actions
  action: '⚡',
  task: '✓',
  
  // Autres
  number: '🔢',
  color: '🎨',
  animal: '🐾',
  music: '🎵',
  
  // Fallback
  default: '🏷️'
};

// Mapping des types vers des couleurs
const ENTITY_COLORS: Record<string, string> = {
  person: '#4caf50',    // Vert
  food: '#ff9800',      // Orange
  drink: '#795548',     // Marron
  object: '#2196f3',    // Bleu
  device: '#9c27b0',    // Violet
  location: '#f44336',  // Rouge
  emotion: '#ffeb3b',   // Jaune
  time: '#00bcd4',      // Cyan
  action: '#ff5722',    // Orange foncé
  default: '#9e9e9e'    // Gris
};

export function EntityBadge({ entity, index }: EntityBadgeProps) {
  // Récupérer l'icône (chercher par type ou par nom)
  const icon = ENTITY_ICONS[entity.type.toLowerCase()] 
    || ENTITY_ICONS[entity.name.toLowerCase()] 
    || ENTITY_ICONS.default;
  
  // Récupérer la couleur
  const color = ENTITY_COLORS[entity.type.toLowerCase()] || ENTITY_COLORS.default;
  
  return (
    <div 
      className="entity-badge"
      style={{ 
        '--entity-color': color,
        animationDelay: `${index * 0.1}s`
      } as React.CSSProperties}
    >
      <span className="entity-icon">{icon}</span>
      <span className="entity-name">{entity.name}</span>
      <span className="entity-type">{entity.type}</span>
    </div>
  );
}
