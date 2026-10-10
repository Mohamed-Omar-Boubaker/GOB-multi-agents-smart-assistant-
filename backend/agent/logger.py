"""
Logger - Journalisation centralisée
Responsable: Montassar
Priorité: 🟠 HAUTE
Temps estimé: 6h

Fonctionnalités:
- Logs JSON structurés
- Rotation automatique
- Niveaux: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Contexte (request_id, user_id, action_id)
"""

import logging
import json
from datetime import datetime, UTC
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional, Dict, Any


class Logger:
    """
    Logger centralisé avec logs JSON structurés.
    Supporte rotation automatique et logs structurés.
    """
    
    def __init__(
        self,
        log_file: str = "logs/agent.log",
        max_bytes: int = 10485760,  # 10MB
        backup_count: int = 5,
        level: str = "INFO"
    ):
        """
        Initialiser le logger.
        
        Args:
            log_file: Chemin fichier log
            max_bytes: Taille max avant rotation (défaut 10MB)
            backup_count: Nombre de fichiers backup (défaut 5)
            level: Niveau de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        # Utiliser nom unique basé sur le fichier log pour éviter conflits
        logger_name = "AgentIntelligent_" + log_file.replace('/', '_').replace('\\', '_')
        self.logger = logging.getLogger(logger_name)
        
        # Éviter les handlers multiples si logger déjà initialisé
        if self.logger.handlers:
            return
            
        # Configurer niveau
        log_level = getattr(logging, level.upper(), logging.INFO)
        self.logger.setLevel(log_level)
        
        # Créer dossier logs si nécessaire
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Handler fichier avec rotation
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(log_level)
        
        # Format JSON pour fichier
        file_formatter = logging.Formatter(
            '{"timestamp": "%(asctime)s", "level": "%(levelname)s", '
            '"logger": "%(name)s", "message": "%(message)s", "extra": %(extra)s}'
        )
        file_handler.setFormatter(file_formatter)
        
        # Handler console (format lisible)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        
        # Ajouter handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def _format_extra(self, **context) -> str:
        """Formatter le contexte en JSON."""
        if not context:
            return '{}'
        try:
            return json.dumps(context, ensure_ascii=False)
        except (TypeError, ValueError):
            return '{}'
    
    def info(self, message: str, **context):
        """
        Log niveau INFO.
        
        Args:
            message: Message à logger
            **context: Contexte supplémentaire (request_id, user_id, etc.)
        """
        extra_str = self._format_extra(**context)
        self.logger.info(message, extra={'extra': extra_str})
    
    def warning(self, message: str, **context):
        """
        Log niveau WARNING.
        
        Args:
            message: Message à logger
            **context: Contexte supplémentaire
        """
        extra_str = self._format_extra(**context)
        self.logger.warning(message, extra={'extra': extra_str})
    
    def error(self, message: str, exc_info: bool = False, **context):
        """
        Log niveau ERROR.
        
        Args:
            message: Message à logger
            exc_info: Inclure traceback exception (défaut False)
            **context: Contexte supplémentaire
        """
        extra_str = self._format_extra(**context)
        self.logger.error(message, exc_info=exc_info, extra={'extra': extra_str})
    
    def debug(self, message: str, **context):
        """
        Log niveau DEBUG.
        
        Args:
            message: Message à logger
            **context: Contexte supplémentaire
        """
        extra_str = self._format_extra(**context)
        self.logger.debug(message, extra={'extra': extra_str})
    
    def critical(self, message: str, **context):
        """
        Log niveau CRITICAL.
        
        Args:
            message: Message à logger
            **context: Contexte supplémentaire
        """
        extra_str = self._format_extra(**context)
        self.logger.critical(message, extra={'extra': extra_str})
    
    # Méthodes spécialisées pour événements métier
    
    def log_conversation(
        self,
        user_id: str,
        input_text: str,
        response_text: str,
        request_id: Optional[str] = None
    ):
        """
        Journaliser une conversation.
        
        Args:
            user_id: ID utilisateur
            input_text: Texte d'entrée utilisateur
            response_text: Réponse générée
            request_id: ID de la requête (optionnel)
        """
        self.info(
            f"Conversation: User={user_id}",
            event_type="conversation",
            user_id=user_id,
            request_id=request_id,
            input=input_text,
            response=response_text,
            timestamp=datetime.now(UTC).isoformat()
        )
    
    def log_action_created(
        self,
        action_id: str,
        action_json: Dict[str, Any],
        user_id: Optional[str] = None
    ):
        """
        Journaliser la création d'une action.
        
        Args:
            action_id: ID de l'action
            action_json: JSON complet de l'action
            user_id: ID utilisateur (optionnel)
        """
        self.info(
            f"Action created: {action_id}",
            event_type="action_created",
            action_id=action_id,
            user_id=user_id,
            intent=action_json.get("intent"),
            state=action_json.get("state"),
            timestamp=datetime.now(UTC).isoformat()
        )
    
    def log_action_state_change(
        self,
        action_id: str,
        old_state: str,
        new_state: str,
        reason: Optional[str] = None
    ):
        """
        Journaliser un changement d'état d'action.
        
        Args:
            action_id: ID de l'action
            old_state: État précédent
            new_state: Nouvel état
            reason: Raison du changement (optionnel)
        """
        self.info(
            f"Action state changed: {action_id} ({old_state} → {new_state})",
            event_type="action_state_change",
            action_id=action_id,
            old_state=old_state,
            new_state=new_state,
            reason=reason,
            timestamp=datetime.now(UTC).isoformat()
        )
    
    def log_action_executed(
        self,
        action_id: str,
        success: bool,
        result: Optional[Dict[str, Any]] = None
    ):
        """
        Journaliser l'exécution d'une action.
        
        Args:
            action_id: ID de l'action
            success: Succès de l'exécution
            result: Résultat de l'exécution (optionnel)
        """
        level_method = self.info if success else self.error
        level_method(
            f"Action executed: {action_id} ({'SUCCESS' if success else 'FAILED'})",
            event_type="action_executed",
            action_id=action_id,
            success=success,
            result=result,
            timestamp=datetime.now(UTC).isoformat()
        )
    
    def log_security_event(
        self,
        event: str,
        user_id: Optional[str] = None,
        action_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Journaliser un événement de sécurité.
        
        Args:
            event: Type d'événement (signature_created, signature_verified, etc.)
            user_id: ID utilisateur (optionnel)
            action_id: ID action (optionnel)
            details: Détails supplémentaires (optionnel)
        """
        self.warning(
            f"Security event: {event}",
            event_type="security",
            security_event=event,
            user_id=user_id,
            action_id=action_id,
            details=details,
            timestamp=datetime.now(UTC).isoformat()
        )
