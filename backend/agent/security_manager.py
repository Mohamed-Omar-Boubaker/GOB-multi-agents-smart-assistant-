"""
Security Manager - Signatures HMAC et JWT
Responsable: Montassar
Priorité: 🟠 HAUTE
Temps estimé: 10h

INPUT JSON (Signer):
{
  "operation": "sign",
  "action_json": {...},
  "algorithm": "HMAC-SHA256"
}

OUTPUT JSON (Sign):
{
  "action_id": "act_abc123xyz",
  "signature": "a3f5d9b2c1e4f7a8...",
  "algorithm": "HMAC-SHA256",
  "signed_at": "2026-01-20T10:30:17Z"
}

INPUT JSON (Vérifier):
{
  "operation": "verify",
  "action_json": {...},
  "signature": "a3f5d9b2c1e4..."
}

OUTPUT JSON (Verify):
{
  "valid": true,
  "action_id": "act_abc123xyz",
  "message": "Signature verified successfully"
}

Algorithme: HMAC-SHA256 avec clé secrète
"""

import hmac
import hashlib
import json
from datetime import datetime, timedelta, UTC
from typing import Dict, Optional


class SecurityManager:
    """
    Gestionnaire de sécurité : signatures HMAC-SHA256, tokens JWT, validation.
    """
    
    def __init__(self, secret_key: str = "dev_secret_key_change_in_production"):
        """
        Initialiser le security manager.
        
        Args:
            secret_key: Clé secrète pour HMAC (doit être en variable d'env en prod)
        """
        self.secret_key = secret_key.encode('utf-8') if isinstance(secret_key, str) else secret_key
        self.algorithm = "HMAC-SHA256"
    
    def execute(self, input_data: dict) -> dict:
        """
        Exécuter une opération de sécurité.
        
        Args:
            input_data: {
                "operation": "sign" ou "verify",
                "action_json": {...},
                "signature": "..." (pour verify)
            }
            
        Returns:
            Résultat selon l'opération
        """
        operation = input_data.get("operation")
        
        if operation == "sign":
            action_json = input_data.get("action_json")
            if not action_json:
                raise ValueError("Missing required parameter: action_json")
            
            result = self.sign_action(action_json)
            return result
        
        elif operation == "verify":
            action_json = input_data.get("action_json")
            signature = input_data.get("signature")
            
            if not action_json or not signature:
                raise ValueError("Missing required parameters: action_json and signature")
            
            is_valid = self.verify_signature(action_json, signature)
            
            return {
                "valid": is_valid,
                "action_id": action_json.get("action_id", "unknown"),
                "message": "Signature verified successfully" if is_valid else "Invalid signature"
            }
        
        else:
            raise ValueError(f"Unknown operation: {operation}")
    
    def sign_action(self, action_json: Dict) -> Dict:
        """
        Signer une action avec HMAC-SHA256.
        
        Args:
            action_json: Action à signer
            
        Returns:
            {
                "action_id": str,
                "signature": str,
                "algorithm": "HMAC-SHA256",
                "signed_at": str
            }
        """
        # Créer une copie pour ne pas modifier l'original
        action_copy = action_json.copy()
        
        # Retirer signature/signed_at si déjà présents
        action_copy.pop("signature", None)
        action_copy.pop("signed_at", None)
        
        # Sérialiser JSON de manière déterministe
        message = json.dumps(action_copy, sort_keys=True).encode('utf-8')
        
        # Calculer signature HMAC-SHA256
        signature = hmac.new(
            self.secret_key,
            message,
            hashlib.sha256
        ).hexdigest()
        
        signed_at = datetime.now(UTC).isoformat()
        
        return {
            "action_id": action_json.get("action_id", "unknown"),
            "signature": signature,
            "algorithm": self.algorithm,
            "signed_at": signed_at,
            "action_json_signed": {
                **action_copy,
                "signature": signature,
                "signed_at": signed_at
            }
        }
    
    def verify_signature(self, action_json: Dict, provided_signature: str) -> bool:
        """
        Vérifier la signature HMAC d'une action.
        
        Args:
            action_json: Action signée
            provided_signature: Signature à vérifier
            
        Returns:
            True si signature valide
        """
        # Créer copie sans signature pour vérification
        action_copy = action_json.copy()
        action_copy.pop("signature", None)
        action_copy.pop("signed_at", None)
        
        # Recalculer signature attendue
        message = json.dumps(action_copy, sort_keys=True).encode('utf-8')
        expected_signature = hmac.new(
            self.secret_key,
            message,
            hashlib.sha256
        ).hexdigest()
        
        # Comparaison sécurisée (timing-attack safe)
        return hmac.compare_digest(provided_signature, expected_signature)
    
    async def sign_action_async(self, action_json: Dict) -> Dict:
        """Version async de sign_action (pour compatibilité avec Agent Core)"""
        return self.sign_action(action_json)
    
    async def verify_signature_async(self, action_json: Dict, signature: str) -> bool:
        """Version async de verify_signature (pour compatibilité avec Agent Core)"""
        return self.verify_signature(action_json, signature)
    
    def create_jwt_token(self, user_id: str, additional_claims: Optional[Dict] = None, expiration_hours: int = 24) -> str:
        """
        Créer un token JWT pour un utilisateur (future implémentation).
        
        Args:
            user_id: ID utilisateur
            additional_claims: Claims additionnels
            expiration_hours: Durée de validité en heures
            
        Returns:
            Token JWT (pour l'instant retourne un placeholder)
        """
        # TODO: Implémenter JWT avec pyjwt
        # Placeholder pour l'instant
        payload = {
            "user_id": user_id,
            "iat": datetime.now(UTC).isoformat(),
            "exp": (datetime.now(UTC) + timedelta(hours=expiration_hours)).isoformat()
        }
        
        if additional_claims:
            payload.update(additional_claims)
        
        # En prod : utiliser jwt.encode(payload, self.secret_key, algorithm="HS256")
        return f"JWT_PLACEHOLDER_{user_id}"
    
    def verify_jwt_token(self, token: str) -> Optional[Dict]:
        """
        Vérifier et décoder un token JWT (future implémentation).
        
        Args:
            token: Token JWT à vérifier
            
        Returns:
            Payload décodé si valide, None sinon
        """
        # TODO: Implémenter avec pyjwt
        # Placeholder pour l'instant
        if token.startswith("JWT_PLACEHOLDER_"):
            return {"user_id": token.replace("JWT_PLACEHOLDER_", ""), "valid": True}
        return None
    
    def check_permission(self, user_id: str, action_type: str) -> bool:
        """
        Vérifier si un utilisateur a la permission pour une action.
        
        Args:
            user_id: ID utilisateur
            action_type: Type d'action
            
        Returns:
            True si autorisé
        """
        # TODO: Implémenter logique de permissions basée sur rôles/utilisateurs
        # Pour l'instant, tous les utilisateurs ont toutes les permissions
        return True
    
    def hash_password(self, password: str) -> str:
        """
        Hasher un mot de passe (future implémentation).
        
        Args:
            password: Mot de passe en clair
            
        Returns:
            Hash du mot de passe
        """
        # TODO: Utiliser bcrypt ou argon2
        return hashlib.sha256(password.encode('utf-8')).hexdigest()
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """
        Vérifier un mot de passe (future implémentation).
        
        Args:
            password: Mot de passe en clair
            password_hash: Hash stocké
            
        Returns:
            True si correspondance
        """
        # TODO: Utiliser bcrypt ou argon2
        return self.hash_password(password) == password_hash
