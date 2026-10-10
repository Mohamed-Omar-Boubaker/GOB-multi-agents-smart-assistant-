"""
Tests unitaires - State Manager
Responsable: Montassar
"""

import pytest
from backend.agent.state_manager import StateManager, ActionState


class TestStateManager:
    """Tests pour la classe StateManager"""
    
    def setup_method(self):
        """Setup avant chaque test."""
        self.state_manager = StateManager()
    
    def test_state_manager_creation(self):
        """Test 1: Création du state manager"""
        assert self.state_manager is not None
        assert isinstance(self.state_manager.actions, dict)
        assert isinstance(self.state_manager.state_history, dict)
        assert len(self.state_manager.actions) == 0
        
        print("✅ Test 1 passed: State manager créé avec succès")
    
    def test_create_action(self):
        """Test 2: Créer une action"""
        action_json = {
            "user_id": "user_001",
            "intent": "control_iot",
            "payload": {"device": "lamp", "action": "turn_on"}
        }
        
        result = self.state_manager.create_action(
            action_id="act_001",
            action_json=action_json,
            initial_state="DRAFT"
        )
        
        assert result["action_id"] == "act_001"
        assert result["current_state"] == "DRAFT"
        assert result["action_json"] == action_json
        assert len(result["state_history"]) == 1
        assert result["state_history"][0]["state"] == "DRAFT"
        assert "created_at" in result
        assert "updated_at" in result
        
        print("✅ Test 2 passed: Action créée en état DRAFT")
    
    def test_create_duplicate_action(self):
        """Test 3: Créer action avec ID déjà existant"""
        action_json = {"user_id": "user_001"}
        
        self.state_manager.create_action("act_002", action_json)
        
        # Tenter de créer avec même ID
        with pytest.raises(ValueError, match="already exists"):
            self.state_manager.create_action("act_002", action_json)
        
        print("✅ Test 3 passed: Erreur sur ID dupliqué")
    
    def test_get_action(self):
        """Test 4: Récupérer une action"""
        action_json = {"user_id": "user_003"}
        self.state_manager.create_action("act_003", action_json)
        
        result = self.state_manager.get_action("act_003")
        
        assert result["action_id"] == "act_003"
        assert result["action_json"]["user_id"] == "user_003"
        
        print("✅ Test 4 passed: Action récupérée avec succès")
    
    def test_get_nonexistent_action(self):
        """Test 5: Récupérer action inexistante"""
        with pytest.raises(ValueError, match="not found"):
            self.state_manager.get_action("act_nonexistent")
        
        print("✅ Test 5 passed: Erreur sur action inexistante")
    
    def test_valid_transition_draft_to_pending(self):
        """Test 6: Transition valide DRAFT → PENDING_CONFIRMATION"""
        action_json = {"user_id": "user_004"}
        self.state_manager.create_action("act_004", action_json, "DRAFT")
        
        result = self.state_manager.update_state(
            action_id="act_004",
            new_state="PENDING_CONFIRMATION",
            reason="User initiated confirmation"
        )
        
        assert result["current_state"] == "PENDING_CONFIRMATION"
        assert len(result["state_history"]) == 2
        assert result["state_history"][1]["state"] == "PENDING_CONFIRMATION"
        assert result["state_history"][1]["previous_state"] == "DRAFT"
        assert result["state_history"][1]["reason"] == "User initiated confirmation"
        
        print("✅ Test 6 passed: Transition DRAFT → PENDING_CONFIRMATION")
    
    def test_valid_transition_pending_to_confirmed(self):
        """Test 7: Transition valide PENDING_CONFIRMATION → CONFIRMED"""
        action_json = {"user_id": "user_005"}
        self.state_manager.create_action("act_005", action_json, "DRAFT")
        self.state_manager.update_state("act_005", "PENDING_CONFIRMATION")
        
        result = self.state_manager.update_state(
            action_id="act_005",
            new_state="CONFIRMED",
            reason="User confirmed action"
        )
        
        assert result["current_state"] == "CONFIRMED"
        assert len(result["state_history"]) == 3
        
        print("✅ Test 7 passed: Transition PENDING_CONFIRMATION → CONFIRMED")
    
    def test_valid_transition_confirmed_to_executing(self):
        """Test 8: Transition valide CONFIRMED → EXECUTING"""
        action_json = {"user_id": "user_006"}
        self.state_manager.create_action("act_006", action_json, "DRAFT")
        self.state_manager.update_state("act_006", "PENDING_CONFIRMATION")
        self.state_manager.update_state("act_006", "CONFIRMED")
        
        result = self.state_manager.update_state(
            action_id="act_006",
            new_state="EXECUTING",
            reason="Action sent to n8n"
        )
        
        assert result["current_state"] == "EXECUTING"
        assert len(result["state_history"]) == 4
        
        print("✅ Test 8 passed: Transition CONFIRMED → EXECUTING")
    
    def test_valid_transition_executing_to_completed(self):
        """Test 9: Transition valide EXECUTING → COMPLETED"""
        action_json = {"user_id": "user_007"}
        self.state_manager.create_action("act_007", action_json, "DRAFT")
        self.state_manager.update_state("act_007", "PENDING_CONFIRMATION")
        self.state_manager.update_state("act_007", "CONFIRMED")
        self.state_manager.update_state("act_007", "EXECUTING")
        
        result = self.state_manager.update_state(
            action_id="act_007",
            new_state="COMPLETED",
            reason="Action executed successfully"
        )
        
        assert result["current_state"] == "COMPLETED"
        assert len(result["state_history"]) == 5
        
        print("✅ Test 9 passed: Transition EXECUTING → COMPLETED")
    
    def test_invalid_transition_draft_to_executing(self):
        """Test 10: Transition invalide DRAFT → EXECUTING"""
        action_json = {"user_id": "user_008"}
        self.state_manager.create_action("act_008", action_json, "DRAFT")
        
        # DRAFT ne peut pas aller directement à EXECUTING
        with pytest.raises(ValueError, match="Invalid state transition"):
            self.state_manager.update_state("act_008", "EXECUTING")
        
        print("✅ Test 10 passed: Transition invalide bloquée")
    
    def test_invalid_transition_completed_to_executing(self):
        """Test 11: Transition invalide depuis état terminal"""
        action_json = {"user_id": "user_009"}
        self.state_manager.create_action("act_009", action_json, "DRAFT")
        self.state_manager.update_state("act_009", "PENDING_CONFIRMATION")
        self.state_manager.update_state("act_009", "CONFIRMED")
        self.state_manager.update_state("act_009", "EXECUTING")
        self.state_manager.update_state("act_009", "COMPLETED")
        
        # COMPLETED est terminal, aucune transition possible
        with pytest.raises(ValueError, match="Invalid state transition"):
            self.state_manager.update_state("act_009", "EXECUTING")
        
        print("✅ Test 11 passed: État terminal respecté")
    
    def test_transition_cancel_from_draft(self):
        """Test 12: Annulation depuis DRAFT"""
        action_json = {"user_id": "user_010"}
        self.state_manager.create_action("act_010", action_json, "DRAFT")
        
        result = self.state_manager.update_state(
            action_id="act_010",
            new_state="CANCELED",
            reason="User canceled action"
        )
        
        assert result["current_state"] == "CANCELED"
        
        print("✅ Test 12 passed: Annulation depuis DRAFT")
    
    def test_transition_failed_to_draft_retry(self):
        """Test 13: Réessai après échec (FAILED → DRAFT)"""
        action_json = {"user_id": "user_011"}
        self.state_manager.create_action("act_011", action_json, "DRAFT")
        self.state_manager.update_state("act_011", "PENDING_CONFIRMATION")
        self.state_manager.update_state("act_011", "CONFIRMED")
        self.state_manager.update_state("act_011", "EXECUTING")
        self.state_manager.update_state("act_011", "FAILED", reason="Network error")
        
        # FAILED permet de réessayer (retour à DRAFT)
        result = self.state_manager.update_state(
            action_id="act_011",
            new_state="DRAFT",
            reason="Retry action"
        )
        
        assert result["current_state"] == "DRAFT"
        assert len(result["state_history"]) == 6
        
        print("✅ Test 13 passed: Réessai après échec (FAILED → DRAFT)")
    
    def test_get_actions_by_state(self):
        """Test 14: Récupérer actions par état"""
        # Créer plusieurs actions
        self.state_manager.create_action("act_012", {"user_id": "u1"}, "DRAFT")
        self.state_manager.create_action("act_013", {"user_id": "u2"}, "DRAFT")
        self.state_manager.create_action("act_014", {"user_id": "u3"}, "DRAFT")
        
        self.state_manager.update_state("act_013", "PENDING_CONFIRMATION")
        self.state_manager.update_state("act_014", "PENDING_CONFIRMATION")
        self.state_manager.update_state("act_014", "CONFIRMED")
        
        draft_actions = self.state_manager.get_actions_by_state("DRAFT")
        pending_actions = self.state_manager.get_actions_by_state("PENDING_CONFIRMATION")
        confirmed_actions = self.state_manager.get_actions_by_state("CONFIRMED")
        
        assert len(draft_actions) == 1
        assert len(pending_actions) == 1
        assert len(confirmed_actions) == 1
        
        print("✅ Test 14 passed: Récupération actions par état")
    
    def test_get_user_actions(self):
        """Test 15: Récupérer actions d'un utilisateur"""
        self.state_manager.create_action("act_015", {"user_id": "user_target"})
        self.state_manager.create_action("act_016", {"user_id": "user_target"})
        self.state_manager.create_action("act_017", {"user_id": "user_other"})
        
        user_actions = self.state_manager.get_user_actions("user_target")
        
        assert len(user_actions) == 2
        assert all(a["action_json"]["user_id"] == "user_target" for a in user_actions)
        
        print("✅ Test 15 passed: Récupération actions utilisateur")
    
    def test_get_state_history(self):
        """Test 16: Récupérer historique complet"""
        action_json = {"user_id": "user_018"}
        self.state_manager.create_action("act_018", action_json, "DRAFT")
        self.state_manager.update_state("act_018", "PENDING_CONFIRMATION")
        self.state_manager.update_state("act_018", "CONFIRMED")
        
        history = self.state_manager.get_state_history("act_018")
        
        assert len(history) == 3
        assert history[0]["state"] == "DRAFT"
        assert history[1]["state"] == "PENDING_CONFIRMATION"
        assert history[2]["state"] == "CONFIRMED"
        assert "timestamp" in history[0]
        
        print("✅ Test 16 passed: Historique complet récupéré")
    
    def test_execute_create_operation(self):
        """Test 17: Opération create via execute()"""
        input_data = {
            "operation": "create",
            "action_id": "act_019",
            "action_json": {"user_id": "user_019"},
            "initial_state": "DRAFT"
        }
        
        result = self.state_manager.execute(input_data)
        
        assert result["action_id"] == "act_019"
        assert result["current_state"] == "DRAFT"
        
        print("✅ Test 17 passed: execute() operation create")
    
    def test_execute_update_state_operation(self):
        """Test 18: Opération update_state via execute()"""
        self.state_manager.create_action("act_020", {"user_id": "u20"}, "DRAFT")
        
        input_data = {
            "operation": "update_state",
            "action_id": "act_020",
            "new_state": "PENDING_CONFIRMATION",
            "reason": "Test reason"
        }
        
        result = self.state_manager.execute(input_data)
        
        assert result["current_state"] == "PENDING_CONFIRMATION"
        
        print("✅ Test 18 passed: execute() operation update_state")
    
    def test_execute_get_operation(self):
        """Test 19: Opération get via execute()"""
        self.state_manager.create_action("act_021", {"user_id": "u21"})
        
        input_data = {
            "operation": "get",
            "action_id": "act_021"
        }
        
        result = self.state_manager.execute(input_data)
        
        assert result["action_id"] == "act_021"
        
        print("✅ Test 19 passed: execute() operation get")
    
    def test_execute_get_by_state_operation(self):
        """Test 20: Opération get_by_state via execute()"""
        self.state_manager.create_action("act_022", {"user_id": "u22"}, "CONFIRMED")
        self.state_manager.create_action("act_023", {"user_id": "u23"}, "CONFIRMED")
        
        input_data = {
            "operation": "get_by_state",
            "state": "CONFIRMED"
        }
        
        result = self.state_manager.execute(input_data)
        
        assert result["state"] == "CONFIRMED"
        assert result["count"] >= 2
        assert isinstance(result["actions"], list)
        
        print("✅ Test 20 passed: execute() operation get_by_state")
    
    def test_get_statistics(self):
        """Test 21: Obtenir statistiques"""
        self.state_manager.create_action("act_024", {"u": "u24"}, "DRAFT")
        self.state_manager.create_action("act_025", {"u": "u25"}, "DRAFT")
        self.state_manager.create_action("act_026", {"u": "u26"}, "CONFIRMED")
        
        stats = self.state_manager.get_statistics()
        
        assert stats["total_actions"] >= 3
        assert "by_state" in stats
        assert stats["by_state"].get("DRAFT", 0) >= 2
        assert stats["by_state"].get("CONFIRMED", 0) >= 1
        
        print("✅ Test 21 passed: Statistiques récupérées")
    
    def test_delete_action(self):
        """Test 22: Supprimer une action"""
        self.state_manager.create_action("act_027", {"u": "u27"})
        
        deleted = self.state_manager.delete_action("act_027")
        assert deleted is True
        
        with pytest.raises(ValueError, match="not found"):
            self.state_manager.get_action("act_027")
        
        print("✅ Test 22 passed: Action supprimée")


if __name__ == "__main__":
    # Exécuter les tests
    test = TestStateManager()
    
    print("🧪 Démarrage des tests State Manager...")
    print("=" * 60)
    
    tests = [
        test.test_state_manager_creation,
        test.test_create_action,
        test.test_create_duplicate_action,
        test.test_get_action,
        test.test_get_nonexistent_action,
        test.test_valid_transition_draft_to_pending,
        test.test_valid_transition_pending_to_confirmed,
        test.test_valid_transition_confirmed_to_executing,
        test.test_valid_transition_executing_to_completed,
        test.test_invalid_transition_draft_to_executing,
        test.test_invalid_transition_completed_to_executing,
        test.test_transition_cancel_from_draft,
        test.test_transition_failed_to_draft_retry,
        test.test_get_actions_by_state,
        test.test_get_user_actions,
        test.test_get_state_history,
        test.test_execute_create_operation,
        test.test_execute_update_state_operation,
        test.test_execute_get_operation,
        test.test_execute_get_by_state_operation,
        test.test_get_statistics,
        test.test_delete_action
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        test.setup_method()
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"❌ Test échoué: {test_func.__name__} - {e}")
            failed += 1
        except Exception as e:
            print(f"❌ Erreur: {test_func.__name__} - {e}")
            failed += 1
    
    print("=" * 60)
    print(f"✅ TESTS STATE MANAGER: {passed} passés, {failed} échoués (total: {passed+failed})")
