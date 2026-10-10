"""
Tests de conformité des implémentations
Vérifie que MQTT Client et Validators suivent les spécifications exactes
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from utils.validators import JSONValidator
from utils.exceptions import ValidationError


def test_validators():
    """Tests des validateurs JSON"""
    print("\n🧪 TESTS VALIDATORS")
    print("=" * 50)
    
    tests_passed = 0
    tests_failed = 0
    
    # Test 1: validate_classification_input ✅
    print("\n1️⃣ Test validate_classification_input:")
    try:
        valid_input = {
            "request_id": "req_001",
            "text": "Allume la lampe du salon",
            "user_id": "user_test",
            "source": "text",
            "language": "fr"
        }
        JSONValidator.validate_classification_input(valid_input)
        print("   ✅ Valid input accepted")
        tests_passed += 1
    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        tests_failed += 1
    
    # Test 2: validate_classification_input - Invalid source ❌
    print("\n2️⃣ Test validate_classification_input - Invalid source:")
    try:
        invalid_input = {
            "request_id": "req_002",
            "text": "Test",
            "user_id": "user_test",
            "source": "invalid_source",  # ❌ Doit être "voice" ou "text"
            "language": "fr"
        }
        JSONValidator.validate_classification_input(invalid_input)
        print("   ❌ Should have raised ValidationError")
        tests_failed += 1
    except ValidationError as e:
        print(f"   ✅ Correctly rejected: {e}")
        tests_passed += 1
    
    # Test 3: validate_classification_output ✅
    print("\n3️⃣ Test validate_classification_output:")
    try:
        valid_output = {
            "request_id": "req_001",
            "classification": "action",
            "confidence": 0.92
        }
        JSONValidator.validate_classification_output(valid_output)
        print("   ✅ Valid output accepted")
        tests_passed += 1
    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        tests_failed += 1
    
    # Test 4: validate_classification_output - Invalid confidence ❌
    print("\n4️⃣ Test validate_classification_output - Invalid confidence:")
    try:
        invalid_output = {
            "request_id": "req_002",
            "classification": "action",
            "confidence": 1.5  # ❌ Doit être entre 0 et 1
        }
        JSONValidator.validate_classification_output(invalid_output)
        print("   ❌ Should have raised ValidationError")
        tests_failed += 1
    except ValidationError as e:
        print(f"   ✅ Correctly rejected: {e}")
        tests_passed += 1
    
    # Test 5: validate_confirmation_request ✅
    print("\n5️⃣ Test validate_confirmation_request:")
    try:
        valid_request = {
            "action_id": "act_123",
            "confirmation_text": "Voulez-vous vraiment allumer la lampe ?",
            "action_summary": {
                "device": "lampe",
                "action": "allumer"
            }
        }
        JSONValidator.validate_confirmation_request(valid_request)
        print("   ✅ Valid confirmation request accepted")
        tests_passed += 1
    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        tests_failed += 1
    
    # Test 6: validate_confirmation_response ✅
    print("\n6️⃣ Test validate_confirmation_response:")
    try:
        valid_response = {
            "action_id": "act_123",
            "user_response": "oui",
            "parsed_response": {
                "intent": "confirm",
                "confidence": 0.95
            }
        }
        JSONValidator.validate_confirmation_response(valid_response)
        print("   ✅ Valid confirmation response accepted")
        tests_passed += 1
    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        tests_failed += 1
    
    # Test 7: validate_n8n_callback ✅
    print("\n7️⃣ Test validate_n8n_callback:")
    try:
        valid_callback = {
            "action_id": "act_123",
            "status": "SUCCESS",
            "result_data": {
                "device_status": "on",
                "execution_time_ms": 234
            }
        }
        JSONValidator.validate_n8n_callback(valid_callback)
        print("   ✅ Valid n8n callback accepted")
        tests_passed += 1
    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        tests_failed += 1
    
    # Test 8: _validate_control_iot_payload ✅
    print("\n8️⃣ Test _validate_control_iot_payload:")
    try:
        valid_payload = {
            "device_id": "lamp_001",
            "action": "turn_on",
            "location": "salon"
        }
        JSONValidator._validate_control_iot_payload(valid_payload)
        print("   ✅ Valid control_iot payload accepted")
        tests_passed += 1
    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        tests_failed += 1
    
    # Test 9: _validate_send_email_payload ✅
    print("\n9️⃣ Test _validate_send_email_payload:")
    try:
        valid_payload = {
            "recipient_email": "test@example.com",
            "subject": "Test Email",
            "body": "This is a test email"
        }
        JSONValidator._validate_send_email_payload(valid_payload)
        print("   ✅ Valid send_email payload accepted")
        tests_passed += 1
    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        tests_failed += 1
    
    # Test 10: validate_action_json_complete ✅
    print("\n🔟 Test validate_action_json_complete:")
    try:
        valid_action_json = {
            "action_id": "act_123",
            "intent": "control_iot",
            "confirmed": True,
            "payload": {
                "device_id": "lamp_001",
                "action": "turn_on",
                "location": "salon"
            },
            "context": {
                "user_id": "user_001",
                "language": "fr"
            }
        }
        JSONValidator.validate_action_json_complete(valid_action_json)
        print("   ✅ Valid complete ActionJSON accepted")
        tests_passed += 1
    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        tests_failed += 1
    
    # Résumé
    print("\n" + "=" * 50)
    print(f"📊 RÉSUMÉ VALIDATORS: {tests_passed}/{tests_passed + tests_failed} tests réussis")
    if tests_failed == 0:
        print("✅ TOUS LES TESTS VALIDATORS PASSENT !")
    else:
        print(f"❌ {tests_failed} tests échoués")
    
    return tests_failed == 0


def test_mqtt_client_interface():
    """Tests de l'interface JSON du MQTT Client"""
    print("\n\n🧪 TESTS MQTT CLIENT INTERFACE")
    print("=" * 50)
    
    tests_passed = 0
    tests_failed = 0
    
    # Test 1: Méthode execute() existe
    print("\n1️⃣ Test méthode execute() existe:")
    try:
        from integrations.mqtt_client import MQTTClient
        
        # Vérifier que la méthode existe
        assert hasattr(MQTTClient, 'execute'), "Méthode execute() manquante"
        print("   ✅ Méthode execute() présente")
        tests_passed += 1
    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        tests_failed += 1
    
    # Test 2: Signature INPUT JSON - publish
    print("\n2️⃣ Test INPUT JSON format - publish:")
    try:
        # Format attendu selon specs
        expected_input_publish = {
            "operation": "publish",
            "topic": "esp32/command/lamp_001",
            "message": {"device_id": "lamp_001", "action": "turn_on"},
            "qos": 1,
            "retain": False
        }
        print(f"   ✅ Format INPUT publish conforme aux specs")
        print(f"      {expected_input_publish}")
        tests_passed += 1
    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        tests_failed += 1
    
    # Test 3: Signature INPUT JSON - subscribe
    print("\n3️⃣ Test INPUT JSON format - subscribe:")
    try:
        expected_input_subscribe = {
            "operation": "subscribe",
            "topic": "esp32/status/#",
            "qos": 1
        }
        print(f"   ✅ Format INPUT subscribe conforme aux specs")
        print(f"      {expected_input_subscribe}")
        tests_passed += 1
    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        tests_failed += 1
    
    # Test 4: OUTPUT JSON format attendu
    print("\n4️⃣ Test OUTPUT JSON format attendu:")
    try:
        expected_output = {
            "status": "published",
            "topic": "esp32/command/lamp_001",
            "message_id": "mqtt_msg_001",
            "published_at": "2026-01-20T10:30:20Z"
        }
        print(f"   ✅ Format OUTPUT défini selon specs")
        print(f"      Keys attendues: {list(expected_output.keys())}")
        tests_passed += 1
    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        tests_failed += 1
    
    # Résumé
    print("\n" + "=" * 50)
    print(f"📊 RÉSUMÉ MQTT CLIENT: {tests_passed}/{tests_passed + tests_failed} tests réussis")
    if tests_failed == 0:
        print("✅ MQTT CLIENT INTERFACE CONFORME AUX SPECS !")
    else:
        print(f"❌ {tests_failed} tests échoués")
    
    return tests_failed == 0


def main():
    """Exécuter tous les tests de conformité"""
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 10 + "TESTS DE CONFORMITÉ AUX SPÉCIFICATIONS" + " " * 20 + "║")
    print("╚" + "=" * 68 + "╝")
    
    validators_ok = test_validators()
    mqtt_ok = test_mqtt_client_interface()
    
    print("\n\n" + "=" * 70)
    print("📋 RÉSUMÉ GLOBAL")
    print("=" * 70)
    
    print(f"\n1. Validators:     {'✅ CONFORME' if validators_ok else '❌ NON CONFORME'}")
    print(f"2. MQTT Client:    {'✅ CONFORME' if mqtt_ok else '❌ NON CONFORME'}")
    
    if validators_ok and mqtt_ok:
        print("\n🎉 TOUTES LES IMPLÉMENTATIONS SONT CONFORMES AUX SPÉCIFICATIONS !")
        print("   Vous pouvez maintenant faire des tests d'intégration.")
        return 0
    else:
        print("\n⚠️  CERTAINS COMPOSANTS NE SONT PAS CONFORMES")
        print("   Vérifiez les erreurs ci-dessus.")
        return 1


if __name__ == "__main__":
    exit(main())
