"""
Exceptions personnalisées
Responsable: Équipe 

Rôle:
- Définir exceptions spécifiques au projet
- Faciliter gestion erreurs
"""

from typing import Optional

class AgentError(Exception):
    """Exception de base pour l'agent."""
    pass

class ValidationError(AgentError):
    """Erreur de validation JSON avec détails structurés."""
    
    def __init__(self, message: str, code: Optional[str] = None, field: Optional[str] = None, details: Optional[dict] = None):
        """
        Initialiser une erreur de validation.
        
        Args:
            message: Message d'erreur descriptif
            code: Code d'erreur (ex: 'CONTACT_NOT_FOUND')
            field: Champ concerné (ex: 'recipient_email')
            details: Détails additionnels (dict)
        """
        super().__init__(message)
        self.message = message
        self.code = code
        self.field = field
        self.details = details or {}
    
    def to_dict(self):
        """Convertir en dictionnaire pour API response."""
        return {
            "error_code": self.code,
            "message": self.message,
            "field": self.field,
            "details": self.details
        }
    
    def __str__(self):
        """Représentation string pour logs."""
        if self.code:
            return f"[{self.code}] {self.message}"
        return self.message

class ClassificationError(AgentError):
    """Erreur de classification."""
    pass

class LLMError(AgentError):
    """Erreur communication LLM."""
    pass

class AudioProcessingError(AgentError):
    """Erreur traitement audio."""
    pass

class StateTransitionError(AgentError):
    """Erreur transition d'état."""
    pass

class SecurityError(AgentError):
    """Erreur sécurité (signature, etc.)."""
    pass

class IntegrationError(AgentError):
    """Erreur intégration (n8n, MQTT, etc.)."""
    pass
