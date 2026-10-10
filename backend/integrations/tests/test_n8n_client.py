"""
Tests unitaires - N8N Client
Responsable: Omar

Tests du N8NClient - Version simplifiée fonctionnelle
"""

import pytest
import asyncio
import sys
import os

# Ajouter backend au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

# Import du client
try:
    from backend.integrations.n8n_client import N8NClient
    N8N_AVAILABLE = True
except Exception as e:
    N8N_AVAILABLE = False
    print(f"⚠️  N8NClient import error: {e}")


@pytest.mark.skipif(not N8N_AVAILABLE, reason="N8NClient non disponible")
class TestN8NClientBasic:
    """Tests basiques du N8N Client"""
    
    def test_n8n_client_class_exists(self):
        """Test que la classe N8NClient existe"""
        assert N8NClient is not None
        print("✅ Test N8NClient class exists: OK")
    
    def test_n8n_has_send_action_method(self):
        """Test que send_action() existe"""
        assert hasattr(N8NClient, 'send_action')
        print("✅ Test send_action() method exists: OK")
    
    def test_n8n_has_check_health_method(self):
        """Test que check_health() existe"""
        assert hasattr(N8NClient, 'check_health')
        print("✅ Test check_health() method exists: OK")


def test_n8n_interface_complete():
    """Test que l'interface complète est présente"""
    if not N8N_AVAILABLE:
        pytest.skip("N8NClient non disponible")
    
    required_methods = ['send_action', 'check_health']
    
    for method in required_methods:
        assert hasattr(N8NClient, method), f"Méthode {method} manquante"
    
    print(f"✅ Test interface complète: {len(required_methods)} méthodes présentes")


if __name__ == "__main__":
    """Exécuter tests directement"""
    print("\n" + "=" * 70)
    print("🧪 TESTS N8N CLIENT")
    print("=" * 70)
    
    if not N8N_AVAILABLE:
        print("\n❌ N8NClient non disponible - Impossible de tester")
        exit(1)
    
    # Tests basiques
    print("\n📦 Tests Basiques:")
    test = TestN8NClientBasic()
    test.test_n8n_client_class_exists()
    test.test_n8n_has_send_action_method()
    test.test_n8n_has_check_health_method()
    
    # Test interface
    print("\n📋 Test Interface:")
    test_n8n_interface_complete()
    
    print("\n" + "=" * 70)
    print("✅ TOUS LES TESTS N8N CLIENT PASSENT ! (4/4)")
    print("=" * 70)
    
    print("\n💡 Note:")
    print("   • Tests basiques: vérification méthodes")
    print("   • Pour tests réels: installer n8n")
    print("   • Activer: set ENABLE_N8N_INTEGRATION=true")
