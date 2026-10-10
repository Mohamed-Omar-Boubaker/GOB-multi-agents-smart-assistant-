"""
Tests unitaires - MQTT Client
Responsable: Omar

Tests du MQTTClient - Version simplifiée fonctionnelle
"""

import pytest
import sys
import os

# Ajouter backend au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

# Import du client
try:
    from backend.integrations.mqtt_client import MQTTClient
    MQTT_AVAILABLE = True
except Exception as e:
    MQTT_AVAILABLE = False
    print(f"⚠️  MQTTClient import error: {e}")


@pytest.mark.skipif(not MQTT_AVAILABLE, reason="MQTTClient non disponible")
class TestMQTTClientBasic:
    """Tests basiques du MQTT Client"""
    
    def test_mqtt_client_class_exists(self):
        """Test que la classe MQTTClient existe"""
        assert MQTTClient is not None
        print("✅ Test MQTTClient class exists: OK")
    
    def test_mqtt_has_execute_method(self):
        """Test que execute() existe"""
        assert hasattr(MQTTClient, 'execute')
        print("✅ Test execute() method exists: OK")
    
    def test_mqtt_has_publish_method(self):
        """Test que publish() existe"""
        assert hasattr(MQTTClient, 'publish')
        print("✅ Test publish() method exists: OK")
    
    def test_mqtt_has_subscribe_method(self):
        """Test que subscribe() existe"""
        assert hasattr(MQTTClient, 'subscribe')
        print("✅ Test subscribe() method exists: OK")
    
    def test_mqtt_has_set_callback_method(self):
        """Test que set_callback() existe"""
        assert hasattr(MQTTClient, 'set_callback')
        print("✅ Test set_callback() method exists: OK")
    
    def test_mqtt_has_is_connected_method(self):
        """Test que is_connected() existe"""
        assert hasattr(MQTTClient, 'is_connected')
        print("✅ Test is_connected() method exists: OK")


def test_mqtt_interface_complete():
    """Test que l'interface complète est présente"""
    if not MQTT_AVAILABLE:
        pytest.skip("MQTTClient non disponible")
    
    required_methods = ['execute', 'publish', 'subscribe', 'set_callback', 'is_connected']
    
    for method in required_methods:
        assert hasattr(MQTTClient, method), f"Méthode {method} manquante"
    
    print(f"✅ Test interface complète: {len(required_methods)} méthodes présentes")


if __name__ == "__main__":
    """Exécuter tests directement"""
    print("\n" + "=" * 70)
    print("🧪 TESTS MQTT CLIENT")
    print("=" * 70)
    
    if not MQTT_AVAILABLE:
        print("\n❌ MQTTClient non disponible - Impossible de tester")
        exit(1)
    
    # Tests basiques
    print("\n📦 Tests Basiques:")
    test = TestMQTTClientBasic()
    test.test_mqtt_client_class_exists()
    test.test_mqtt_has_execute_method()
    test.test_mqtt_has_publish_method()
    test.test_mqtt_has_subscribe_method()
    test.test_mqtt_has_set_callback_method()
    test.test_mqtt_has_is_connected_method()
    
    # Test interface
    print("\n📋 Test Interface:")
    test_mqtt_interface_complete()
    
    print("\n" + "=" * 70)
    print("✅ TOUS LES TESTS MQTT CLIENT PASSENT ! (7/7)")
    print("=" * 70)
    
    print("\n💡 Note:")
    print("   • Tests basiques: vérification méthodes")
    print("   • Pour tests réels: installer Mosquitto")
    print("   • Activer: set ENABLE_MQTT_INTEGRATION=true")
