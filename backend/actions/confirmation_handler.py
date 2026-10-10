"""
Confirmation Handler - Gestion confirmations utilisateur
Responsable: montassar
Priorité: 🟠 HAUTE
Temps estimé: 15h

INPUT JSON (Génération demande):
{
  "action_json": {...},  # ActionJSON DRAFT complet
  "generate_audio": true,
  "language": "fr"
}

OUTPUT JSON (Demande):
{
  "action_id": "act_abc123xyz",
  "confirmation_text": "Voulez-vous vraiment allumer la lampe du salon ?",
  "action_summary": {...},
  "options": [...],
  "timeout_seconds": 30
}

INPUT JSON (Réponse utilisateur):
{
  "action_id": "act_abc123xyz",
  "user_response": "oui",
  "user_id": "user_001"
}

OUTPUT JSON (Résultat):
{
  "action_id": "act_abc123xyz",
  "parsed_response": {
    "intent": "confirm",  # "confirm", "cancel", "modify"
    "confidence": 0.98
  },
  "new_state": "CONFIRMED"
}
"""

#===============================================================================================================================================================

"""
Ce code définit une classe ConfirmationHandler qui sert à gérer les confirmations utilisateur dans un système intelligent (type assistant ou AI agent).

Son rôle est double :

1) Générer une demande de confirmation

À partir d’un ActionJSON (une action à exécuter), il :

génère une phrase de confirmation (ex: “Voulez-vous allumer la lampe ?”)
crée un résumé de l’action
propose des options (oui / non / modifier)

Méthode principale : generate_request()

2) Analyser la réponse utilisateur

Il prend une réponse comme :

"oui"
"non"
"change ça"

Et il :

détecte l’intention (confirm / cancel / modify)
attribue une confidence
met à jour l’état (CONFIRMED, CANCELED, DRAFT)

Méthode principale : parse_response()

⚙️ Logique importante
Utilise des listes de mots-clés multilingues (FR + EN)
Détection via regex sécurisée (évite faux positifs)
Génération dynamique selon le type d’action :
IoT (lampe, ventilateur…)
Email
Reminder
Web search

"""

from datetime import datetime, timezone
from typing import Dict, Optional
import logging
import re

# Import validation
from backend.utils.validators import JSONValidator
from backend.utils.exceptions import ValidationError
from backend.config import Config

logger = logging.getLogger(__name__)


class ConfirmationHandler:
    """
    Gestionnaire de confirmations utilisateur.
    Génère demandes et parse réponses.
    """
    
    def __init__(self):
        """Initialiser le handler."""
        # Mots-clés de confirmation (français + anglais)
        self.confirm_keywords = [
            "oui", "yes", "ok", "d'accord", "valide", "confirme",
            "ouais", "yep", "yeah", "vas-y", "go", "correct", "confirm", "confirmed"
        ]
        
        # Mots-clés d'annulation (français + anglais)
        self.cancel_keywords = [
            "non", "no", "annule", "cancel", "stop", "arrête",
            "nope", "pas", "jamais", "négatif", "negative", "canceled", "cancelled"
        ]
        
        # Mots-clés de modification (français + anglais)
        self.modify_keywords = [
            "modifier", "modify", "change", "changer", "corriger",
            "correction", "plutôt", "instead", "rather"
        ]

    @staticmethod
    def _contains_keyword(response_text: str, keywords: list[str]) -> bool:
        """
        Détecter un mot-clé avec bornes de mots pour éviter les faux positifs.
        Ex: "no" ne doit pas matcher "not" dans "could not transcribe".
        """
        for keyword in keywords:
            pattern = rf"(?<!\w){re.escape(keyword.lower())}(?!\w)"
            if re.search(pattern, response_text):
                return True
        return False
    
    async def generate_confirmation(self, action_json: Dict) -> str:
        """
        Générer texte de confirmation à partir d'ActionJSON.
        
        Args:
            action_json: ActionJSON en état DRAFT
            
        Returns:
            Texte de confirmation en français
        """
        intent = action_json.get("intent", "unknown")
        payload = action_json.get("payload", {})
        language = action_json.get("context", {}).get("language", Config.DEFAULT_LANGUAGE)
        
        # Générer le texte selon l'intent
        if intent == "control_iot":
            return self._generate_iot_confirmation(payload, language)
        elif intent == "send_email":
            return self._generate_email_confirmation(payload, language)
        elif intent == "set_reminder":
            return self._generate_reminder_confirmation(payload, language)
        elif intent == "web_search":
            return self._generate_search_confirmation(payload, language)
        else:
            if language == "en":
                return "Do you want to confirm this action?"
            return "Voulez-vous confirmer cette action ?"
    
    def generate_request(self, input_data: dict) -> dict:
        """
        Générer demande de confirmation complète.
        
        Args:
            input_data: Dict avec action_json, language
            
        Returns:
            Dict avec confirmation_text, action_summary, options
        """
        # ✅ VALIDATION: Valider input de génération de confirmation
        try:
            if not isinstance(input_data, dict):
                raise ValidationError("Confirmation request input must be a dictionary")
            
            if "action_json" not in input_data:
                raise ValidationError("Missing required field: action_json")
            
            action_json = input_data["action_json"]
            
            # Valider l'ActionJSON
            JSONValidator.validate_action_json_complete(action_json)
            logger.info(f"✅ Confirmation request validé pour {action_json.get('action_id')}")
        
        except ValidationError as e:
            logger.error(f"❌ Confirmation request invalide: {e}")
            return {
                "status": "validation_error",
                "error": str(e)
            }
        
        language = input_data.get("language", Config.DEFAULT_LANGUAGE)
        
        action_id = action_json.get("action_id", "unknown")
        intent = action_json.get("intent", "unknown")
        payload = action_json.get("payload", {})
        
        # Générer le texte de confirmation
        if intent == "control_iot":
            confirmation_text = self._generate_iot_confirmation(payload, language)
            action_summary = self._summarize_iot_action(payload)
        elif intent == "send_email":
            confirmation_text = self._generate_email_confirmation(payload, language)
            action_summary = self._summarize_email_action(payload)
        elif intent == "set_reminder":
            confirmation_text = self._generate_reminder_confirmation(payload, language)
            action_summary = self._summarize_reminder_action(payload)
        elif intent == "web_search":
            confirmation_text = self._generate_search_confirmation(payload, language)
            action_summary = self._summarize_search_action(payload)
        else:
            confirmation_text = "Do you want to confirm this action?" if language == "en" else "Voulez-vous confirmer cette action ?"
            action_summary = {"intent": intent, "details": "unknown"}
        
        # Options de réponse
        options = [
            {"response": "oui", "action": "confirm"},
            {"response": "non", "action": "cancel"},
            {"response": "modifier", "action": "modify"}
        ]
        
        return {
            "action_id": action_id,
            "confirmation_text": confirmation_text,
            "action_summary": action_summary,
            "options": options,
            "timeout_seconds": 30,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def parse_response(self, input_data: dict) -> dict:
        """
        Parser réponse utilisateur (méthode synchrone pour compatibilité).
        
        Args:
            input_data: Dict avec action_id, user_response, user_id
            
        Returns:
            Dict avec parsed_response (intent, confidence), new_state
        """
        # ✅ VALIDATION: Valider input de réponse confirmation
        try:
            if not isinstance(input_data, dict):
                raise ValidationError("Confirmation response input must be a dictionary")
            
            required = ["action_id", "user_response"]
            for field in required:
                if field not in input_data:
                    raise ValidationError(f"Missing required field: {field}")
            
            logger.info(f"✅ Confirmation response validé pour {input_data.get('action_id')}")
        
        except ValidationError as e:
            logger.error(f"❌ Confirmation response invalide: {e}")
            return {
                "status": "validation_error",
                "error": str(e)
            }
        
        action_id = input_data.get("action_id", "unknown")
        user_response = input_data.get("user_response", "")
        
        response_lower = user_response.lower().strip()
        
        # Vérifier confirmation
        if self._contains_keyword(response_lower, self.confirm_keywords):
            return {
                "action_id": action_id,
                "parsed_response": {
                    "intent": "confirm",
                    "confidence": 0.98
                },
                "new_state": "CONFIRMED",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        
        # Vérifier annulation
        if self._contains_keyword(response_lower, self.cancel_keywords):
            return {
                "action_id": action_id,
                "parsed_response": {
                    "intent": "cancel",
                    "confidence": 0.98
                },
                "new_state": "CANCELED",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        
        # Vérifier modification
        if self._contains_keyword(response_lower, self.modify_keywords):
            return {
                "action_id": action_id,
                "parsed_response": {
                    "intent": "modify",
                    "confidence": 0.95
                },
                "new_state": "DRAFT",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        
        # Par défaut, si incertain - on annule par sécurité
        return {
            "action_id": action_id,
            "parsed_response": {
                "intent": "unknown",
                "confidence": 0.3
            },
            "new_state": "DRAFT",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    # ==================== Générateurs de texte par intent ====================
    
    def _generate_iot_confirmation(self, payload: Dict, language: str) -> str:
        """Générer confirmation pour control_iot."""
        action = payload.get("action", "unknown")
        device_type = payload.get("device_type", "appareil")
        location = payload.get("location", "")
        
        # English confirmation
        if language == "en":
            action_verbs = {
                "turn_on": "turn on",
                "turn_off": "turn off",
                "open": "open",
                "close": "close",
                "increase": "increase",
                "decrease": "decrease",
                "set": "set"
            }
            
            device_names = {
                "light": "the light",
                "lamp": "the lamp",
                "shutter": "the shutter",
                "thermostat": "the thermostat",
                "door": "the door",
                "window": "the window",
                "camera": "the camera",
                "heater": "the heater",
                "fan": "the fan",
                "tv": "the TV"
            }
            
            action_en = action_verbs.get(action, action)
            device_en = device_names.get(device_type, f"the {device_type}")
            
            if location:
                return f"Do you want to {action_en} {device_en} in the {location}?"
            else:
                return f"Do you want to {action_en} {device_en}?"
        
        # French confirmation (default)
        action_verbs = {
            "turn_on": "allumer",
            "turn_off": "éteindre",
            "open": "ouvrir",
            "close": "fermer",
            "set": "régler",
            "set_value": "régler",
            "get_status": "vérifier l'état de",
            "increase": "augmenter",
            "decrease": "diminuer",
            "lock": "verrouiller",
            "unlock": "déverrouiller"
        }
        
        # Traduction des types de devices
        device_names = {
            "light": "la lampe",
            "lamp": "la lampe",
            "lumiere": "la lumière",
            "shutter": "les volets",
            "volet": "les volets",
            "temperature": "le thermostat",
            "thermostat": "le thermostat",
            "door": "la porte",
            "porte": "la porte",
            "window": "la fenêtre",
            "fenetre": "la fenêtre",
            "camera": "la caméra",
            "speaker": "le haut-parleur",
            "heater": "le radiateur",
            "chauffage": "le chauffage",
            "fan": "le ventilateur",
            "ventilateur": "le ventilateur",
            "tv": "la télévision",
            "television": "la télévision"
        }
        
        action_fr = action_verbs.get(action, action)
        device_fr = device_names.get(device_type, f"le {device_type}")
        
        if location:
            return f"Voulez-vous vraiment {action_fr} {device_fr} du {location} ?"
        else:
            return f"Voulez-vous vraiment {action_fr} {device_fr} ?"
    
    def _generate_email_confirmation(self, payload: Dict, language: str) -> str:
        """Générer confirmation pour send_email."""
        recipient = payload.get("recipient_name", payload.get("recipient_email", "le destinataire"))
        subject = payload.get("subject", "")
        
        if language == "en":
            if subject:
                return f"Do you want to send an email to {recipient} with subject '{subject}'?"
            else:
                return f"Do you want to send an email to {recipient}?"
        
        # French
        if subject:
            return f"Voulez-vous envoyer un email à {recipient} avec le sujet '{subject}' ?"
        else:
            return f"Voulez-vous envoyer un email à {recipient} ?"
    
    def _generate_reminder_confirmation(self, payload: Dict, language: str) -> str:
        """Générer confirmation pour set_reminder."""
        title = payload.get("title", "ce rappel")
        reminder_time = payload.get("reminder_time", "")
        
        if language == "en":
            if reminder_time:
                return f"Do you want to create a reminder '{title}' for {reminder_time}?"
            else:
                return f"Do you want to create the reminder '{title}'?"
        
        # French
        if reminder_time:
            return f"Voulez-vous créer un rappel '{title}' pour {reminder_time} ?"
        else:
            return f"Voulez-vous créer le rappel '{title}' ?"
    
    def _generate_search_confirmation(self, payload: Dict, language: str) -> str:
        """Générer confirmation pour web_search."""
        query = payload.get("query", "cette recherche")
        
        if language == "en":
            return f"Do you want to search for '{query}'?"
        
        return f"Voulez-vous rechercher '{query}' ?"
    
    # ==================== Résumés d'action pour output ====================
    
    def _summarize_iot_action(self, payload: Dict) -> Dict:
        """Résumer action IoT."""
        return {
            "intent": "control_iot",
            "target": payload.get("device_type", "unknown"),
            "location": payload.get("location"),
            "action": payload.get("action", "unknown")
        }
    
    def _summarize_email_action(self, payload: Dict) -> Dict:
        """Résumer action email."""
        return {
            "intent": "send_email",
            "recipient": payload.get("recipient_name", payload.get("recipient_email")),
            "subject": payload.get("subject")
        }
    
    def _summarize_reminder_action(self, payload: Dict) -> Dict:
        """Résumer action rappel."""
        return {
            "intent": "set_reminder",
            "title": payload.get("title"),
            "time": payload.get("reminder_time")
        }
    
    def _summarize_search_action(self, payload: Dict) -> Dict:
        """Résumer action recherche."""
        return {
            "intent": "web_search",
            "query": payload.get("query"),
            "type": payload.get("search_type")
        }
