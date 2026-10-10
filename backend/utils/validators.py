"""
Validators - Validation schémas JSON
Responsable: Équipe (utilisé par tous)

Rôle:
- Valider INPUT/OUTPUT JSON de chaque composant
- Vérifier champs obligatoires
- Vérifier types et valeurs
"""

import jsonschema
from jsonschema import validate, ValidationError as JSONSchemaError
from typing import Dict, Any, Optional
from backend.utils.exceptions import ValidationError


class JSONValidator:
    """
    Validateur de schémas JSON.
    """
    
    # Schémas de validation standards
    ACTION_JSON_SCHEMA = {
        "type": "object",
        "required": ["action_id", "user_id", "intent", "payload", "context"],
        "properties": {
            "action_id": {"type": "string"},
            "user_id": {"type": "string"},
            "request_id": {"type": "string"},
            "intent": {"type": "string"},
            "confirmed": {"type": "boolean"},
            "state": {"type": "string"},
            "payload": {"type": "object"},
            "context": {
                "type": "object",
                "required": ["language"],
                "properties": {
                    "language": {"type": "string"},
                    "original_command": {"type": "string"},
                    "source": {"type": "string"},
                    "confidence": {"type": "number"}
                },
                "additionalProperties": True
            },
            "security": {
                "type": "object",
                "properties": {
                    "signature": {"type": ["string", "null"]},
                    "auth_level": {"type": "integer"},
                    "user_token": {"type": ["string", "null"]},
                    "signature_algorithm": {"type": "string"}
                }
            },
            "timestamps": {
                "type": "object",
                "properties": {
                    "created_at": {"type": "string"},
                    "updated_at": {"type": "string"},
                    "confirmed_at": {"type": ["string", "null"]},
                    "executed_at": {"type": ["string", "null"]}
                }
            },
            "metadata": {"type": "object"}
        }
    }
    
    @staticmethod
    def validate_input(data: dict, schema: Optional[dict] = None) -> bool:
        """
        Valider un INPUT JSON.
        
        Args:
            data: Données à valider
            schema: Schéma de validation (optionnel)
            
        Returns:
            True si valide
            
        Raises:
            ValidationError si invalide
        """
        if schema is None:
            # Validation basique : vérifier que c'est un dict
            if not isinstance(data, dict):
                raise ValidationError("Input must be a dictionary")
            return True
        
        try:
            validate(instance=data, schema=schema)
            return True
        except JSONSchemaError as e:
            raise ValidationError(f"Invalid input JSON: {e.message}")
    
    @staticmethod
    def validate_output(data: dict, schema: Optional[dict] = None) -> bool:
        """
        Valider un OUTPUT JSON.
        
        Args:
            data: Données à valider
            schema: Schéma de validation (optionnel)
            
        Returns:
            True si valide
            
        Raises:
            ValidationError si invalide
        """
        if schema is None:
            if not isinstance(data, dict):
                raise ValidationError("Output must be a dictionary")
            return True
        
        try:
            validate(instance=data, schema=schema)
            return True
        except JSONSchemaError as e:
            raise ValidationError(f"Invalid output JSON: {e.message}")
    
    @staticmethod
    def validate_action_json(action_json: dict) -> bool:
        """
        Valider un ActionJSON complet.
        
        Args:
            action_json: ActionJSON à valider
            
        Returns:
            True si valide
            
        Raises:
            ValidationError si invalide
        """
        return JSONValidator.validate_input(
            action_json,
            JSONValidator.ACTION_JSON_SCHEMA
        )
    
    @staticmethod
    def validate_required_fields(data: dict, required_fields: list) -> bool:
        """
        Vérifier la présence de champs obligatoires.
        
        Args:
            data: Données à vérifier
            required_fields: Liste des champs requis
            
        Returns:
            True si tous les champs sont présents
            
        Raises:
            ValidationError si champs manquants
        """
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            raise ValidationError(
                f"Missing required fields: {', '.join(missing_fields)}"
            )
        
        return True
    
    @staticmethod
    def validate_classification_input(data: dict) -> bool:
        """
        Valider Flux 0 INPUT - Classification.
        Référence: 05_SPECIFICATIONS Section Classifier INPUT
        
        Args:
            data: Input JSON du classifier
            
        Returns:
            True si valide
            
        Raises:
            ValidationError si invalide
        """
        required_fields = ["request_id", "text", "user_id", "source", "language"]
        JSONValidator.validate_required_fields(data, required_fields)
        
        # Vérifier types
        if not isinstance(data["text"], str):
            raise ValidationError("text must be string")
        
        if data["source"] not in ["voice", "text"]:
            raise ValidationError("source must be 'voice' or 'text'")
        
        # Vérifier longueur texte
        if len(data["text"]) > 500:
            raise ValidationError("text too long (max 500 chars)")
        
        return True
    
    @staticmethod
    def validate_classification_output(data: dict) -> bool:
        """
        Valider Flux 0 OUTPUT - Classification.
        Référence: 05_SPECIFICATIONS Section Classifier OUTPUT
        
        Args:
            data: Output JSON du classifier
            
        Returns:
            True si valide
            
        Raises:
            ValidationError si invalide
        """
        required_fields = ["request_id", "classification", "confidence"]
        JSONValidator.validate_required_fields(data, required_fields)
        
        # Vérifier classification
        if data["classification"] not in ["conversation", "action"]:
            raise ValidationError(
                "classification must be 'conversation' or 'action'"
            )
        
        # Vérifier confidence
        if not isinstance(data["confidence"], (int, float)):
            raise ValidationError("confidence must be numeric")
        
        if not 0 <= data["confidence"] <= 1:
            raise ValidationError("confidence must be between 0 and 1")
        
        return True
    
    @staticmethod
    def validate_confirmation_request(data: dict) -> bool:
        """
        Valider demande de confirmation.
        Référence: 05_SPECIFICATIONS Section Confirmation Handler
        
        Args:
            data: Request JSON de confirmation
            
        Returns:
            True si valide
            
        Raises:
            ValidationError si invalide
        """
        required_fields = ["action_id", "confirmation_text", "action_summary"]
        JSONValidator.validate_required_fields(data, required_fields)
        
        if not isinstance(data["confirmation_text"], str):
            raise ValidationError("confirmation_text must be string")
        
        if not isinstance(data["action_summary"], dict):
            raise ValidationError("action_summary must be dict")
        
        return True
    
    @staticmethod
    def validate_confirmation_response(data: dict) -> bool:
        """
        Valider réponse de confirmation.
        Référence: 05_SPECIFICATIONS Section Confirmation Handler
        
        Args:
            data: Response JSON de confirmation
            
        Returns:
            True si valide
            
        Raises:
            ValidationError si invalide
        """
        required_fields = ["action_id", "user_response", "parsed_response"]
        JSONValidator.validate_required_fields(data, required_fields)
        
        # Vérifier parsed_response
        parsed = data["parsed_response"]
        if not isinstance(parsed, dict):
            raise ValidationError("parsed_response must be dict")
        
        if "intent" not in parsed:
            raise ValidationError("parsed_response must have 'intent' field")
        
        if parsed["intent"] not in ["confirm", "cancel", "modify"]:
            raise ValidationError(
                f"Invalid intent: {parsed['intent']}. Must be confirm/cancel/modify"
            )
        
        return True
    
    @staticmethod
    def validate_n8n_callback(data: dict) -> bool:
        """
        Valider callback n8n.
        Référence: 05_SPECIFICATIONS Section n8n Client
        
        Args:
            data: Callback JSON de n8n
            
        Returns:
            True si valide
            
        Raises:
            ValidationError si invalide
        """
        required_fields = ["action_id", "status", "result_data"]
        JSONValidator.validate_required_fields(data, required_fields)
        
        # Vérifier status
        valid_statuses = ["SUCCESS", "FAILED", "TIMEOUT", "PARTIAL"]
        if data["status"] not in valid_statuses:
            raise ValidationError(
                f"Invalid status: {data['status']}. Must be one of {valid_statuses}"
            )
        
        if not isinstance(data["result_data"], dict):
            raise ValidationError("result_data must be dict")
        
        return True
    
    @staticmethod
    def _validate_control_iot_payload(payload: dict) -> bool:
        """
        Valider payload control_iot.
        
        Args:
            payload: Payload de l'ActionJSON control_iot
            
        Returns:
            True si valide
            
        Raises:
            ValidationError si invalide
        """
        required = ["device_id", "action"]
        JSONValidator.validate_required_fields(payload, required)
        
        valid_actions = ["turn_on", "turn_off", "toggle", "set_value", "open", "close"]
        if payload["action"] not in valid_actions:
            raise ValidationError(
                f"Invalid iot action: {payload['action']}. Must be one of {valid_actions}"
            )
        
        # Si set_value, vérifier présence de 'value'
        if payload["action"] == "set_value" and "value" not in payload:
            raise ValidationError("control_iot with set_value must have 'value' field")
        
        return True
    
    @staticmethod
    def _validate_send_email_payload(payload: dict) -> bool:
        """
        Valider payload send_email.
        
        Args:
            payload: Payload de l'ActionJSON send_email
            
        Returns:
            True si valide
            
        Raises:
            ValidationError si invalide
        """
        # Vérifier présence destinataire
        if "recipient_email" not in payload and "recipient" not in payload:
            raise ValidationError(
                "send_email: need recipient_email or recipient field"
            )
        
        # Vérifier champs obligatoires
        required = ["subject", "body"]
        JSONValidator.validate_required_fields(payload, required)
        
        # Validation basique email si recipient_email présent
        if "recipient_email" in payload:
            email = payload["recipient_email"]
            if not isinstance(email, str) or "@" not in email:
                raise ValidationError(f"Invalid email format: {email}")
        
        return True
    
    @staticmethod
    def validate_action_json_complete(action_json: dict) -> bool:
        """
        Valider un ActionJSON complet avec validation du payload selon intent.
        
        Args:
            action_json: ActionJSON à valider
            
        Returns:
            True si valide
            
        Raises:
            ValidationError si invalide
        """
        # Validation de base
        JSONValidator.validate_action_json(action_json)
        
        # Vérifier intent valide
        valid_intents = ["control_iot", "send_email", "set_reminder", "web_search"]
        intent = action_json.get("intent")
        if intent not in valid_intents:
            raise ValidationError(
                f"Invalid intent: {intent}. Must be one of {valid_intents}"
            )
        
        # Validation spécifique par intent
        payload = action_json.get("payload", {})
        
        if intent == "control_iot":
            JSONValidator._validate_control_iot_payload(payload)
        elif intent == "send_email":
            JSONValidator._validate_send_email_payload(payload)
        
        return True
