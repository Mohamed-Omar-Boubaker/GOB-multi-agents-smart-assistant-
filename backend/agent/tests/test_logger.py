"""
Tests pour le Logger
Responsable: Montassar
"""

import pytest
import json
import os
from pathlib import Path
from backend.agent.logger import Logger


class TestLogger:
    """Tests pour la classe Logger"""
    
    def setup_method(self):
        """Setup avant chaque test."""
        self.test_log_file = "logs/test_agent.log"
        # Nettoyer fichiers de test existants
        self._cleanup_test_logs()
    
    def teardown_method(self):
        """Cleanup après chaque test."""
        self._cleanup_test_logs()
    
    def _cleanup_test_logs(self):
        """Supprimer fichiers de log de test."""
        log_dir = Path("logs")
        if log_dir.exists():
            for log_file in log_dir.glob("test_*.log*"):
                try:
                    log_file.unlink()
                except:
                    pass
    
    def test_logger_creation(self):
        """Test 1: Création du logger"""
        logger = Logger(log_file=self.test_log_file, level="INFO")
        
        assert logger is not None
        assert "AgentIntelligent" in logger.logger.name
        assert len(logger.logger.handlers) == 2  # File + Console
        
        print("✅ Test 1 passed: Logger créé avec succès")
    
    def test_info_log(self):
        """Test 2: Log niveau INFO"""
        logger = Logger(log_file=self.test_log_file, level="INFO")
        
        logger.info("Test message INFO", request_id="req_001", user_id="user_test")
        
        # Vérifier que fichier log existe
        assert Path(self.test_log_file).exists()
        
        # Lire dernière ligne du log
        with open(self.test_log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            assert len(lines) > 0
            
            last_line = lines[-1]
            log_data = json.loads(last_line)
            
            assert log_data['level'] == 'INFO'
            assert log_data['message'] == 'Test message INFO'
            
            # Extra est déjà un dict (pas une string)
            extra = log_data['extra']
            assert extra['request_id'] == 'req_001'
            assert extra['user_id'] == 'user_test'
        
        print("✅ Test 2 passed: Log INFO enregistré correctement")
    
    def test_error_log(self):
        """Test 3: Log niveau ERROR"""
        logger = Logger(log_file=self.test_log_file, level="ERROR")
        
        logger.error("Test error message", action_id="act_001", error_code="E500")
        
        assert Path(self.test_log_file).exists()
        
        with open(self.test_log_file, 'r', encoding='utf-8') as f:
            last_line = f.readlines()[-1]
            log_data = json.loads(last_line)
            
            assert log_data['level'] == 'ERROR'
            assert log_data['message'] == 'Test error message'
            
            extra = log_data['extra']
            assert extra['action_id'] == 'act_001'
            assert extra['error_code'] == 'E500'
        
        print("✅ Test 3 passed: Log ERROR enregistré correctement")
    
    def test_debug_log(self):
        """Test 4: Log niveau DEBUG"""
        # Créer un fichier séparé pour ce test
        debug_log_file = "logs/test_debug.log"
        if Path(debug_log_file).exists():
            try:
                Path(debug_log_file).unlink()
            except:
                pass
        
        logger = Logger(log_file=debug_log_file, level="DEBUG")
        
        logger.debug("Debug info", component="classifier", step="analysis")
        
        assert Path(debug_log_file).exists()
        
        with open(debug_log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            assert len(lines) > 0
            # Lire premier log (le seul qu'on a créé)
            log_data = json.loads(lines[0])
            
            assert log_data['level'] == 'DEBUG'
            assert log_data['message'] == 'Debug info'
        
        # Nettoyer
        try:
            Path(debug_log_file).unlink()
        except:
            pass
        
        print("✅ Test 4 passed: Log DEBUG enregistré correctement")
    
    def test_log_conversation(self):
        """Test 5: Log conversation spécialisé"""
        logger = Logger(log_file=self.test_log_file, level="INFO")
        
        logger.log_conversation(
            user_id="user_123",
            input_text="Quelle heure est-il ?",
            response_text="Il est 14h30",
            request_id="req_conv_001"
        )
        
        assert Path(self.test_log_file).exists()
        
        with open(self.test_log_file, 'r', encoding='utf-8') as f:
            last_line = f.readlines()[-1]
            log_data = json.loads(last_line)
            
            assert log_data['level'] == 'INFO'
            assert 'Conversation' in log_data['message']
            
            extra = log_data['extra']
            assert extra['event_type'] == 'conversation'
            assert extra['user_id'] == 'user_123'
            assert extra['input'] == 'Quelle heure est-il ?'
            assert extra['response'] == 'Il est 14h30'
            assert extra['request_id'] == 'req_conv_001'
        
        print("✅ Test 5 passed: Log conversation enregistré avec métadonnées")
    
    def test_log_action_created(self):
        """Test 6: Log création action"""
        logger = Logger(log_file=self.test_log_file, level="INFO")
        
        action_json = {
            "action_id": "act_001",
            "intent": "control_iot",
            "state": "DRAFT",
            "payload": {"device": "lamp"}
        }
        
        logger.log_action_created(
            action_id="act_001",
            action_json=action_json,
            user_id="user_456"
        )
        
        assert Path(self.test_log_file).exists()
        
        with open(self.test_log_file, 'r', encoding='utf-8') as f:
            last_line = f.readlines()[-1]
            log_data = json.loads(last_line)
            
            assert log_data['level'] == 'INFO'
            assert 'Action created' in log_data['message']
            
            extra = log_data['extra']
            assert extra['event_type'] == 'action_created'
            assert extra['action_id'] == 'act_001'
            assert extra['intent'] == 'control_iot'
            assert extra['state'] == 'DRAFT'
        
        print("✅ Test 6 passed: Log action créée enregistré correctement")
    
    def test_log_action_state_change(self):
        """Test 7: Log changement d'état action"""
        logger = Logger(log_file=self.test_log_file, level="INFO")
        
        logger.log_action_state_change(
            action_id="act_002",
            old_state="DRAFT",
            new_state="CONFIRMED",
            reason="User confirmed action"
        )
        
        with open(self.test_log_file, 'r', encoding='utf-8') as f:
            last_line = f.readlines()[-1]
            log_data = json.loads(last_line)
            
            assert log_data['level'] == 'INFO'
            assert 'state changed' in log_data['message']
            
            extra = log_data['extra']
            assert extra['event_type'] == 'action_state_change'
            assert extra['action_id'] == 'act_002'
            assert extra['old_state'] == 'DRAFT'
            assert extra['new_state'] == 'CONFIRMED'
            assert extra['reason'] == 'User confirmed action'
        
        print("✅ Test 7 passed: Log changement état enregistré")
    
    def test_log_action_executed(self):
        """Test 8: Log exécution action"""
        logger = Logger(log_file=self.test_log_file, level="INFO")
        
        result = {"status": "completed", "device": "lamp", "value": "ON"}
        
        logger.log_action_executed(
            action_id="act_003",
            success=True,
            result=result
        )
        
        with open(self.test_log_file, 'r', encoding='utf-8') as f:
            last_line = f.readlines()[-1]
            log_data = json.loads(last_line)
            
            assert log_data['level'] == 'INFO'
            assert 'SUCCESS' in log_data['message']
            
            extra = log_data['extra']
            assert extra['event_type'] == 'action_executed'
            assert extra['action_id'] == 'act_003'
            assert extra['success'] is True
            assert extra['result'] == result
        
        print("✅ Test 8 passed: Log exécution action enregistré")
    
    def test_log_security_event(self):
        """Test 9: Log événement sécurité"""
        logger = Logger(log_file=self.test_log_file, level="WARNING")
        
        logger.log_security_event(
            event="signature_verified",
            user_id="user_789",
            action_id="act_004",
            details={"algorithm": "HMAC-SHA256", "valid": True}
        )
        
        with open(self.test_log_file, 'r', encoding='utf-8') as f:
            last_line = f.readlines()[-1]
            log_data = json.loads(last_line)
            
            assert log_data['level'] == 'WARNING'
            assert 'Security event' in log_data['message']
            
            extra = log_data['extra']
            assert extra['event_type'] == 'security'
            assert extra['security_event'] == 'signature_verified'
            assert extra['user_id'] == 'user_789'
        
        print("✅ Test 9 passed: Log sécurité enregistré")
    
    def test_multiple_logs(self):
        """Test 10: Multiple logs sequentiels"""
        # Utiliser un fichier séparé pour ce test
        multi_log_file = "logs/test_multi.log"
        if Path(multi_log_file).exists():
            try:
                Path(multi_log_file).unlink()
            except:
                pass
        
        logger = Logger(log_file=multi_log_file, level="INFO")
        
        logger.info("Log 1", step=1)
        logger.warning("Log 2", step=2)
        logger.error("Log 3", step=3)
        
        with open(multi_log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            assert len(lines) == 3, f"Expected 3 lines, got {len(lines)}"
            
            # Vérifier ordre
            log1 = json.loads(lines[0])
            log2 = json.loads(lines[1])
            log3 = json.loads(lines[2])
            
            assert log1['level'] == 'INFO'
            assert log2['level'] == 'WARNING'
            assert log3['level'] == 'ERROR'
        
        # Nettoyer
        try:
            Path(multi_log_file).unlink()
        except:
            pass
        
        print("✅ Test 10 passed: Multiple logs enregistrés dans l'ordre")


if __name__ == "__main__":
    # Exécuter les tests
    test = TestLogger()
    
    print("🧪 Démarrage des tests Logger...")
    print("=" * 60)
    
    test.setup_method()
    try:
        test.test_logger_creation()
        test.teardown_method()
        
        test.setup_method()
        test.test_info_log()
        test.teardown_method()
        
        test.setup_method()
        test.test_error_log()
        test.teardown_method()
        
        test.setup_method()
        test.test_debug_log()
        test.teardown_method()
        
        test.setup_method()
        test.test_log_conversation()
        test.teardown_method()
        
        test.setup_method()
        test.test_log_action_created()
        test.teardown_method()
        
        test.setup_method()
        test.test_log_action_state_change()
        test.teardown_method()
        
        test.setup_method()
        test.test_log_action_executed()
        test.teardown_method()
        
        test.setup_method()
        test.test_log_security_event()
        test.teardown_method()
        
        test.setup_method()
        test.test_multiple_logs()
        test.teardown_method()
        
        print("=" * 60)
        print("✅ TOUS LES TESTS LOGGER PASSÉS (10/10)")
        
    except AssertionError as e:
        print(f"❌ Test échoué: {e}")
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
