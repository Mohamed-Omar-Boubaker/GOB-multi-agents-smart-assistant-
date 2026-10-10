"""
State Manager - Gestion états des actions
Responsable: Montassar
Priorité: 🟠 HAUTE
Temps estimé: 12h

États possibles:
- IDLE: Aucune action
- DRAFT: Action créée, pas confirmée
- PENDING_CONFIRMATION: En attente confirmation
- CONFIRMED: Confirmée, prête exécution
- EXECUTING: En cours d'exécution
- COMPLETED: Exécutée avec succès
- FAILED: Échec
- CANCELED: Annulée

Transitions valides:
DRAFT → PENDING_CONFIRMATION → CONFIRMED/CANCELED
CONFIRMED → EXECUTING → COMPLETED/FAILED

INPUT JSON (Créer):
{
  "operation": "create",
  "action_json": {...}
}

INPUT JSON (Mettre à jour état):
{
  "operation": "update_state",
  "action_id": "act_abc123xyz",
  "new_state": "CONFIRMED",
  "reason": "User confirmed"
}

OUTPUT JSON:
{
  "action_id": "act_abc123xyz",
  "current_state": "CONFIRMED",
  "action_json": {...},
  "state_history": [...]
}
"""

from typing import Dict, Optional, List
from datetime import datetime, UTC
from enum import Enum


class ActionState(Enum):
    """États possibles d'une action."""
    IDLE = "IDLE"
    DRAFT = "DRAFT"
    PENDING_CONFIRMATION = "PENDING_CONFIRMATION"
    CONFIRMED = "CONFIRMED"
    EXECUTING = "EXECUTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELED = "CANCELED"


class StateManager:
    """
    Gestionnaire d'états des actions.
    Gère le cycle de vie complet d'une action avec validation des transitions.
    """
    
    def __init__(self):
        """Initialiser le state manager."""
        # Base de données en mémoire (remplacer par DB réelle en production)
        self.actions: Dict[str, Dict] = {}
        self.state_history: Dict[str, List[Dict]] = {}
        
        # Transitions valides entre états
        self.valid_transitions = {
            "IDLE": ["DRAFT"],
            "DRAFT": ["PENDING_CONFIRMATION", "CANCELED"],
            "PENDING_CONFIRMATION": ["CONFIRMED", "CANCELED", "DRAFT"],
            "CONFIRMED": ["EXECUTING", "CANCELED"],
            "EXECUTING": ["COMPLETED", "FAILED"],
            "COMPLETED": [],  # État terminal
            "FAILED": ["DRAFT"],  # Permet de réessayer
            "CANCELED": []  # État terminal
        }
    
    def execute(self, input_data: dict) -> dict:
        """
        Exécuter une opération sur les états.
        
        Args:
            input_data: Dict avec operation, action_id, new_state, etc.
            
        Returns:
            Dict avec action_id, current_state, action_json, history
        """
        operation = input_data.get("operation")
        
        if operation == "create":
            action_id = input_data.get("action_id")
            action_json = input_data.get("action_json")
            if not action_id or not action_json:
                raise ValueError("Missing required parameters: action_id and action_json")
            return self.create_action(
                action_id=action_id,
                action_json=action_json,
                initial_state=input_data.get("initial_state", "DRAFT")
            )
        
        elif operation == "update_state":
            action_id = input_data.get("action_id")
            new_state = input_data.get("new_state")
            if not action_id or not new_state:
                raise ValueError("Missing required parameters: action_id and new_state")
            return self.update_state(
                action_id=action_id,
                new_state=new_state,
                reason=input_data.get("reason", "")
            )
        
        elif operation == "get":
            action_id = input_data.get("action_id")
            if not action_id:
                raise ValueError("Missing required parameter: action_id")
            return self.get_action(action_id)
        
        elif operation == "get_by_state":
            state = input_data.get("state")
            if not state:
                raise ValueError("Missing required parameter: state")
            actions = self.get_actions_by_state(state)
            return {
                "state": state,
                "count": len(actions),
                "actions": actions
            }
        
        elif operation == "get_history":
            action_id = input_data.get("action_id")
            if not action_id:
                raise ValueError("Missing required parameter: action_id")
            history = self.get_state_history(action_id)
            return {
                "action_id": action_id,
                "history": history
            }
        
        else:
            raise ValueError(f"Unknown operation: {operation}")
    
    def create_action(
        self,
        action_id: str,
        action_json: Dict,
        initial_state: str = "DRAFT"
    ) -> Dict:
        """
        Créer une nouvelle action avec son état initial.
        
        Args:
            action_id: ID unique de l'action
            action_json: JSON complet de l'action
            initial_state: État initial (défaut: DRAFT)
        
        Returns:
            Action créée avec métadonnées
        """
        if action_id in self.actions:
            raise ValueError(f"Action {action_id} already exists")
        
        # Valider que l'état initial est valide
        if initial_state not in [state.value for state in ActionState]:
            raise ValueError(f"Invalid initial state: {initial_state}")
        
        timestamp = datetime.now(UTC).isoformat()
        
        # Créer historique initial
        history_entry = {
            "state": initial_state,
            "timestamp": timestamp,
            "reason": "Action created"
        }
        
        # Créer action
        action_data = {
            "action_id": action_id,
            "current_state": initial_state,
            "action_json": action_json,
            "state_history": [history_entry],
            "created_at": timestamp,
            "updated_at": timestamp
        }
        
        # Stocker
        self.actions[action_id] = action_data
        self.state_history[action_id] = action_data["state_history"]
        
        return action_data
    
    def get_action(self, action_id: str) -> Dict:
        """
        Récupérer une action par son ID.
        
        Args:
            action_id: ID de l'action
        
        Returns:
            Données de l'action
        
        Raises:
            ValueError: Si action non trouvée
        """
        if action_id not in self.actions:
            raise ValueError(f"Action {action_id} not found")
        
        return self.actions[action_id]
    
    def update_state(
        self,
        action_id: str,
        new_state: str,
        reason: str = ""
    ) -> Dict:
        """
        Mettre à jour l'état d'une action.
        
        Args:
            action_id: ID de l'action
            new_state: Nouvel état
            reason: Raison du changement d'état
        
        Returns:
            Action mise à jour
        
        Raises:
            ValueError: Si action non trouvée ou transition invalide
        """
        if action_id not in self.actions:
            raise ValueError(f"Action {action_id} not found")
        
        action = self.actions[action_id]
        old_state = action["current_state"]
        
        # Validation de la transition d'état
        if not self._is_valid_transition(old_state, new_state):
            raise ValueError(
                f"Invalid state transition: {old_state} → {new_state}"
            )
        
        timestamp = datetime.now(UTC).isoformat()
        
        # Mise à jour de l'état
        action["current_state"] = new_state
        action["updated_at"] = timestamp
        
        # Ajout dans l'historique
        history_entry = {
            "state": new_state,
            "previous_state": old_state,
            "timestamp": timestamp,
            "reason": reason or f"State changed from {old_state} to {new_state}"
        }
        
        # Ajouter seulement une fois (action["state_history"] et self.state_history[action_id] sont la même référence)
        action["state_history"].append(history_entry)
        
        return action
    
    def _is_valid_transition(self, old_state: str, new_state: str) -> bool:
        """
        Valider si une transition d'état est autorisée.
        
        Args:
            old_state: État actuel
            new_state: État cible
        
        Returns:
            True si la transition est valide, False sinon
        """
        valid_next_states = self.valid_transitions.get(old_state, [])
        return new_state in valid_next_states
    
    def get_actions_by_state(self, state: str) -> List[Dict]:
        """
        Récupérer toutes les actions dans un état donné.
        
        Args:
            state: État recherché
        
        Returns:
            Liste des actions dans cet état
        """
        return [
            action for action in self.actions.values()
            if action["current_state"] == state
        ]
    
    def get_user_actions(self, user_id: str) -> List[Dict]:
        """
        Récupérer toutes les actions d'un utilisateur.
        
        Args:
            user_id: ID utilisateur
        
        Returns:
            Liste des actions de l'utilisateur
        """
        return [
            action for action in self.actions.values()
            if action["action_json"].get("user_id") == user_id
        ]
    
    def get_pending_action(self, user_id: str) -> Optional[Dict]:
        """
        Récupérer l'action en attente de confirmation pour un utilisateur.
        
        Args:
            user_id: ID utilisateur
        
        Returns:
            Action en PENDING_CONFIRMATION ou None
        """
        # Chercher action en PENDING_CONFIRMATION pour cet utilisateur
        for action in self.actions.values():
            if (action["action_json"].get("user_id") == user_id and
                action["current_state"] == "PENDING_CONFIRMATION"):
                return action
        return None
    
    def get_state_history(self, action_id: str) -> List[Dict]:
        """
        Récupérer l'historique complet des états d'une action.
        
        Args:
            action_id: ID de l'action
        
        Returns:
            Historique des états
        
        Raises:
            ValueError: Si action non trouvée
        """
        if action_id not in self.state_history:
            raise ValueError(f"No history found for action {action_id}")
        
        return self.state_history[action_id]
    
    def get_all_actions(self) -> List[Dict]:
        """
        Récupérer toutes les actions.
        
        Returns:
            Liste de toutes les actions
        """
        return list(self.actions.values())
    
    def delete_action(self, action_id: str) -> bool:
        """
        Supprimer une action.
        
        Args:
            action_id: ID de l'action
        
        Returns:
            True si supprimée, False sinon
        """
        if action_id in self.actions:
            del self.actions[action_id]
            if action_id in self.state_history:
                del self.state_history[action_id]
            return True
        return False
    
    def get_statistics(self) -> Dict:
        """
        Obtenir des statistiques sur les actions.
        
        Returns:
            Dict avec statistiques (total, par état, etc.)
        """
        stats = {
            "total_actions": len(self.actions),
            "by_state": {}
        }
        
        # Compter par état
        for state in ActionState:
            count = len(self.get_actions_by_state(state.value))
            if count > 0:
                stats["by_state"][state.value] = count
        
        return stats
