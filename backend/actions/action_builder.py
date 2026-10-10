"""
Action Builder - Construction ActionJSON
Responsable: AMINE
Priorité: 🔴 CRITIQUE
Temps estimé: 20h

INTÉGRATION: ContactManager pour résolution nom→email (Option 1+2)
- Résout les contacts depuis contacts.json
- Rejette les emails fictifs (@example.com)
- Demande clarification si contact inconnu

INPUT JSON:
{
  "request_id": "req_builder_001",
  "user_id": "user_001",
  "intent": "control_iot",
  "entities": {...},
  "original_text": "Allume la lampe du salon",
  "confidence": 0.94,
  "language": "fr"
}

OUTPUT JSON (ActionJSON COMPLET):
{
  "action_id": "act_abc123xyz",
  "user_id": "user_001",
  "request_id": "req_builder_001",
  "intent": "control_iot",
  "confirmed": false,
  "state": "DRAFT",
  "payload": {...},
  "context": {...},
  "security": {...},
  "timestamps": {...},
  "metadata": {...}
}

Intents supportés:
- control_iot
- send_email
- set_reminder
- web_search
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Optional, Any
import logging

# Import validation
from backend.utils.validators import JSONValidator
from backend.utils.exceptions import ValidationError
from backend.config import Config

# Import ContactManager pour résolution nom→email
from backend.utils.contact_manager import contact_manager
# Import DeviceManager pour résolution device_id
from backend.utils.device_manager import device_manager

logger = logging.getLogger(__name__)


class ActionBuilder:
    """
    Constructeur d'ActionJSON.
    Transforme intent + entités en ActionJSON complet.
    """
    
    def __init__(self):
        """Initialiser le builder."""
        self.device_manager = device_manager
    
    async def build_action(self, llm_analysis: Dict, user_id: str, 
                          original_text: str, language: str) -> Dict:
        """
        Construire ActionJSON complet à partir de l'analyse LLM.
        
        Args:
            llm_analysis: Analyse LLM avec intent, entities, confidence
            user_id: ID utilisateur
            original_text: Texte original de la commande
            language: Langue de la commande
            
        Returns:
            ActionJSON complet en état DRAFT
        """
        # Extraire les données de l'analyse LLM
        intent = llm_analysis.get("primary_intent", "unknown")
        confidence = llm_analysis.get("confidence", 0.0)
        entities = llm_analysis.get("entities", {})
        request_id = llm_analysis.get("request_id", f"req_{uuid.uuid4().hex[:8]}")
        
        # Générer action_id unique
        action_id = f"act_{uuid.uuid4().hex[:12]}"
        
        # Timestamp actuel
        now = datetime.now(timezone.utc).isoformat()
        
        # Construire le payload selon l'intent
        payload = self._build_payload(intent, entities)
        
        # Construire ActionJSON complet
        action_json = {
            "action_id": action_id,
            "user_id": user_id,
            "request_id": request_id,
            "intent": intent,
            "confirmed": False,
            "state": "DRAFT",
            "payload": payload,
            "context": {
                "original_command": original_text,
                "language": language,
                "source": "voice",
                "confidence": confidence
            },
            "security": {
                "user_token": None,
                "signature": None,
                "signature_algorithm": "HMAC-SHA256"
            },
            "timestamps": {
                "created_at": now,
                "updated_at": now,
                "confirmed_at": None,
                "executed_at": None
            },
            "metadata": {
                "priority": "normal",
                "timeout_seconds": 30,
                "retry_count": 0,
                "max_retries": 3
            }
        }
        
        # ✅ VALIDATION: Valider ActionJSON avant retour
        try:
            JSONValidator.validate_action_json_complete(action_json)
            logger.info(f"✅ ActionJSON validé (__init__): {action_id}")
        except ValidationError as e:
            logger.error(f"❌ ActionJSON invalide (__init__) pour {action_id}: {e}")
            raise ValueError(f"ActionJSON construction failed: {e}")
        
        return action_json
    
    def build(self, input_data: dict) -> dict:
        """
        Construire ActionJSON complet (méthode synchrone pour compatibilité).
        
        Args:
            input_data: Dict avec intent, entities, original_text, user_id, etc.
            
        Returns:
            ActionJSON complet en état DRAFT
        """
        # Extraire les données d'input
        request_id = input_data.get("request_id", f"req_{uuid.uuid4().hex[:8]}")
        user_id = input_data.get("user_id", "unknown")
        intent = input_data.get("intent", "unknown")
        entities = input_data.get("entities", {})
        original_text = input_data.get("original_text", "")
        confidence = input_data.get("confidence", 0.0)
        language = input_data.get("language", Config.DEFAULT_LANGUAGE)
        
        # Générer action_id unique
        action_id = f"act_{uuid.uuid4().hex[:12]}"
        
        # Timestamp actuel
        now = datetime.now(timezone.utc).isoformat()
        
        # Construire le payload selon l'intent
        payload = self._build_payload(intent, entities)
        
        # Construire ActionJSON complet
        action_json = {
            "action_id": action_id,
            "user_id": user_id,
            "request_id": request_id,
            "intent": intent,
            "confirmed": False,
            "state": "DRAFT",
            "payload": payload,
            "context": {
                "original_command": original_text,
                "language": language,
                "source": "voice",
                "confidence": confidence
            },
            "security": {
                "user_token": None,
                "signature": None,
                "signature_algorithm": "HMAC-SHA256"
            },
            "timestamps": {
                "created_at": now,
                "updated_at": now,
                "confirmed_at": None,
                "executed_at": None
            },
            "metadata": {
                "priority": "normal",
                "timeout_seconds": 30,
                "retry_count": 0,
                "max_retries": 3
            }
        }
        
        # ✅ VALIDATION: Valider ActionJSON avant retour
        try:
            JSONValidator.validate_action_json_complete(action_json)
            logger.info(f"✅ ActionJSON validé: {action_id}")
        except ValidationError as e:
            logger.error(f"❌ ActionJSON invalide pour {action_id}: {e}")
            raise ValueError(f"ActionJSON construction failed: {e}")
        
        return action_json
    
    def _build_payload(self, intent: str, entities: Dict) -> Dict:
        """
        Construire le payload selon le type d'intent.
        
        Args:
            intent: Type d'intent (control_iot, send_email, etc.)
            entities: Entités extraites par le LLM
            
        Returns:
            Payload structuré selon l'intent
        """
        if intent == "control_iot":
            return self._build_iot_payload(entities)
        elif intent == "send_email":
            return self._build_email_payload(entities)
        elif intent == "set_reminder":
            return self._build_reminder_payload(entities)
        elif intent == "web_search":
            return self._build_search_payload(entities)
        else:
            # Intent inconnu, payload générique
            return {"raw_entities": entities}
    
    def _build_iot_payload(self, entities: Dict) -> Dict:
        """Construire payload pour control_iot."""
        # Gérer 2 formats: nouveau (devices=[]) et ancien (device/action/location directs)
        devices = entities.get("devices", [])
        
        if not devices:
            # Format alternatif: entités directes (device, action, location)
            device_type = entities.get("device", entities.get("device_type", "unknown"))
            action = entities.get("action", "unknown")
            location = entities.get("location")
        else:
            # Format liste: prendre le premier device
            device = devices[0]
            device_type = device.get("type", device.get("device_type", "unknown"))
            location = device.get("location")
            action = device.get("action", "unknown")

        # Normaliser l'action (LLM peut renvoyer des verbes FR)
        action = self._normalize_iot_action(action)
        
        # Si toujours unknown, retourner payload vide
        if device_type == "unknown" and action == "unknown":
            return {
                "device_id": "unknown",
                "device_type": "unknown",
                "action": "unknown",
                "location": None,
                "parameters": {}
            }
        
        # Trouver le device_id
        device_id = self._get_device_id(device_type, location)
        
        # Paramètres par défaut selon l'action
        parameters = {}
        if action == "turn_on" and device_type == "light":
            parameters["brightness"] = 100
        elif action == "turn_off":
            parameters["transition_time"] = 1
        
        return {
            "device_id": device_id,
            "device_type": device_type,
            "action": action,
            "location": location,
            "parameters": parameters
        }

    def _normalize_iot_action(self, action: str) -> str:
        """Normaliser les actions IoT vers les valeurs valides."""
        if not action:
            return "unknown"

        action_norm = str(action).strip().lower()

        action_map = {
            "allumer": "turn_on",
            "allume": "turn_on",
            "activer": "turn_on",
            "active": "turn_on",
            "mettre": "turn_on",
            "éteindre": "turn_off",
            "eteindre": "turn_off",
            "eteins": "turn_off",
            "éteins": "turn_off",
            "désactiver": "turn_off",
            "desactiver": "turn_off",
            "fermer": "close",
            "ferme": "close",
            "ouvrir": "open",
            "ouvre": "open",
            "toggle": "toggle",
            "switch": "toggle",
            "turn_on": "turn_on",
            "turn_off": "turn_off",
            "open": "open",
            "close": "close",
            "set_value": "set_value",
            "increase": "increase",
            "decrease": "decrease",
            "augmenter": "increase",
            "diminuer": "decrease"
        }

        return action_map.get(action_norm, action_norm)
    
    def _build_email_payload(self, entities: Dict) -> Dict:
        """
        Construire payload pour send_email avec résolution de contacts.
        
        LOGIQUE (Option 1 + 2):
        1. Essayer de résoudre le nom dans contacts.json
        2. Si trouvé → Utiliser email réel
        3. Si pas trouvé OU email fictif → REJETER avec erreur explicite
        
        Args:
            entities: Entités extraites par le LLM
            
        Returns:
            Payload email avec email réel validé
            
        Raises:
            ValidationError: Si contact inconnu ou email fictif
        """
        recipient_email = entities.get("recipient_email", entities.get("email", ""))
        recipient_name = entities.get("recipient", entities.get("recipient_name", ""))
        
        # Vérifier que nous avons au moins un nom
        if not recipient_name and not recipient_email:
            raise ValidationError(
                message="Aucun destinataire spécifié. Veuillez préciser à qui envoyer l'email.",
                code="MISSING_RECIPIENT",
                field="recipient"
            )
        
        # ÉTAPE 1: Résoudre le nom dans les contacts
        resolved_email = None
        if recipient_name:
            logger.info(f"🔍 [ActionBuilder] Recherche contact: '{recipient_name}'")
            resolved_email = contact_manager.get_email(recipient_name)
        
        # ÉTAPE 2: Choisir l'email à utiliser
        final_email = resolved_email or recipient_email
        
        # ÉTAPE 3: Validation stricte - Rejeter emails fictifs
        if not final_email or "@" not in final_email:
            raise ValidationError(
                message=f"Contact '{recipient_name}' introuvable. Ajoutez-le dans vos contacts ou précisez son adresse email complète.",
                code="CONTACT_NOT_FOUND",
                field="recipient_email",
                details={
                    "recipient_name": recipient_name,
                    "suggestion": "Dites 'ajoute contact' pour créer un nouveau contact"
                }
            )
        
        # ÉTAPE 4: Rejeter emails faux générés par le LLM
        if contact_manager.is_fake_email(final_email):
            raise ValidationError(
                message=f"Email invalide: {final_email}. Le contact '{recipient_name}' n'est pas dans votre liste. Ajoutez-le d'abord ou précisez son vrai email.",
                code="FAKE_EMAIL_REJECTED",
                field="recipient_email",
                details={
                    "recipient_name": recipient_name,
                    "fake_email_detected": final_email,
                    "available_contacts": contact_manager.list_contacts()
                }
            )
        
        logger.info(f"✅ [ActionBuilder] Email validé: {final_email} pour {recipient_name}")
        
        # Construire payload validé
        payload = {
            "recipient_name": recipient_name,
            "recipient": recipient_name,
            "recipient_email": final_email,
            "subject": entities.get("subject", "Message de l'assistant vocal"),
            "body": entities.get("body", entities.get("message", "")),
            "priority": entities.get("priority", "normal"),
            "attachments": []
        }
        
        return payload
    
    def _build_reminder_payload(self, entities: Dict) -> Dict:
        return {
            "title":             entities.get("title", entities.get("task", "Rappel")),
            "description":       entities.get("description", ""),
            # ← add reminder_datetime as alias so both keys work
            "reminder_datetime": entities.get("reminder_datetime",
                                entities.get("time",
                                entities.get("reminder_time", ""))),
            "reminder_time":     entities.get("reminder_datetime",
                                entities.get("time",
                                entities.get("reminder_time", ""))),
            "notification_channels": ["voice", "push"]
        }
    
    def _build_search_payload(self, entities: Dict) -> Dict:
        """Construire payload pour web_search."""
        query = entities.get("query", entities.get("search_query", ""))
        search_type = "general"
        
        # Détecter le type de recherche
        if any(word in query.lower() for word in ["météo", "weather", "température"]):
            search_type = "weather"
        
        return {
            "query": query,
            "search_type": search_type,
            "max_results": 3,
            "language": Config.DEFAULT_LANGUAGE
        }
    
    def _get_device_id(self, device_type: str, location: Optional[str]) -> str:
        """
        Obtenir le device_id à partir du type et de la location.
        
        Args:
            device_type: Type de device (light, shutter, etc.)
            location: Location (salon, cuisine, etc.)
            
        Returns:
            Device ID ou unknown si non trouvé
        """
        if not location:
            return f"{device_type}_default_001"
        
        location_normalized = location.lower()
        
        resolved_id = self.device_manager.get_device_id(device_type, location_normalized)
        if resolved_id:
            return resolved_id
        
        # Si pas trouvé, générer un ID générique
        return f"{device_type}_{location_normalized}_001"
