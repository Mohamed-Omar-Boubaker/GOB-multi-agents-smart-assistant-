"""
Tests unitaires - ActionBuilder
"""

import pytest
from backend.actions.action_builder import ActionBuilder


@pytest.fixture
def action_builder():
    """Fixture pour ActionBuilder."""
    return ActionBuilder()


def test_build_iot_action_light(action_builder):
    """Test construction ActionJSON pour IoT - Allumer lampe."""
    input_data = {
        "request_id": "test_build_001",
        "user_id": "user_test",
        "intent": "control_iot",
        "entities": {
            "devices": [
                {
                    "type": "light",
                    "name": "lampe",
                    "location": "salon",
                    "action": "turn_on"
                }
            ]
        },
        "original_text": "Allume la lampe du salon",
        "confidence": 0.94,
        "language": "fr"
    }
    
    output = action_builder.build(input_data)
    
    # Vérifications structure
    assert output["action_id"].startswith("act_")
    assert output["user_id"] == "user_test"
    assert output["intent"] == "control_iot"
    assert output["confirmed"] == False
    assert output["state"] == "DRAFT"
    
    # Vérifications payload
    assert "device_id" in output["payload"]
    assert output["payload"]["action"] == "turn_on"
    assert output["payload"]["device_type"] == "light"
    assert output["payload"]["location"] == "salon"
    assert output["payload"]["device_id"] == "lamp_salon_001"
    
    # Vérifications timestamps
    assert "created_at" in output["timestamps"]
    assert "updated_at" in output["timestamps"]
    assert output["timestamps"]["confirmed_at"] is None
    
    # Vérifications security
    assert output["security"]["signature"] is None
    assert output["security"]["signature_algorithm"] == "HMAC-SHA256"
    
    print(f"✅ Test IoT light passed: action_id={output['action_id']}")


def test_build_email_action(action_builder):
    """Test construction ActionJSON pour Email."""
    input_data = {
        "request_id": "test_build_002",
        "user_id": "user_test",
        "intent": "send_email",
        "entities": {
            "recipient": "Jean",
            "recipient_email": "jean@example.com",
            "subject": "Réunion",
            "body": "On se voit à 15h"
        },
        "original_text": "Envoie un email à Jean pour la réunion",
        "confidence": 0.89,
        "language": "fr"
    }
    
    output = action_builder.build(input_data)
    
    assert output["intent"] == "send_email"
    assert output["payload"]["recipient_email"] == "jean@example.com"
    assert output["payload"]["recipient_name"] == "Jean"
    assert output["payload"]["subject"] == "Réunion"
    assert output["payload"]["body"] == "On se voit à 15h"
    assert output["confirmed"] == False
    
    print(f"✅ Test email passed: action_id={output['action_id']}")


def test_build_reminder_action(action_builder):
    """Test construction ActionJSON pour Rappel."""
    input_data = {
        "request_id": "test_build_003",
        "user_id": "user_test",
        "intent": "set_reminder",
        "entities": {
            "title": "Appeler le médecin",
            "time": "2026-02-11T14:30:00Z"
        },
        "original_text": "Rappelle-moi d'appeler le médecin demain à 14h30",
        "confidence": 0.87,
        "language": "fr"
    }
    
    output = action_builder.build(input_data)
    
    assert output["intent"] == "set_reminder"
    assert output["payload"]["title"] == "Appeler le médecin"
    assert output["payload"]["reminder_time"] == "2026-02-11T14:30:00Z"
    assert "notification_channels" in output["payload"]
    
    print(f"✅ Test reminder passed: action_id={output['action_id']}")


def test_build_search_action(action_builder):
    """Test construction ActionJSON pour Web Search."""
    input_data = {
        "request_id": "test_build_004",
        "user_id": "user_test",
        "intent": "web_search",
        "entities": {
            "query": "météo Paris demain"
        },
        "original_text": "Quelle est la météo à Paris demain?",
        "confidence": 0.92,
        "language": "fr"
    }
    
    output = action_builder.build(input_data)
    
    assert output["intent"] == "web_search"
    assert output["payload"]["query"] == "météo Paris demain"
    assert output["payload"]["search_type"] == "weather"
    assert output["payload"]["language"] == "fr"
    
    print(f"✅ Test search passed: action_id={output['action_id']}")


def test_build_structure_validation(action_builder):
    """Test validation structure complète ActionJSON."""
    input_data = {
        "request_id": "test_build_005",
        "user_id": "user_test",
        "intent": "control_iot",
        "entities": {
            "devices": [
                {
                    "type": "shutter",
                    "location": "chambre",
                    "action": "close"
                }
            ]
        },
        "original_text": "Ferme les volets de la chambre",
        "confidence": 0.91
    }
    
    output = action_builder.build(input_data)
    
    # Vérifier tous les champs obligatoires
    required_fields = [
        "action_id", "user_id", "request_id", "intent", 
        "confirmed", "state", "payload", "context", 
        "security", "timestamps", "metadata"
    ]
    
    for field in required_fields:
        assert field in output, f"Missing required field: {field}"
    
    # Vérifier structure timestamps
    timestamp_fields = ["created_at", "updated_at", "confirmed_at", "executed_at"]
    for field in timestamp_fields:
        assert field in output["timestamps"]
    
    # Vérifier structure security
    security_fields = ["user_token", "signature", "signature_algorithm"]
    for field in security_fields:
        assert field in output["security"]
    
    # Vérifier structure metadata
    metadata_fields = ["priority", "timeout_seconds", "retry_count", "max_retries"]
    for field in metadata_fields:
        assert field in output["metadata"]
    
    print(f"✅ Test structure validation passed")


def test_build_multiple_devices(action_builder):
    """Test avec plusieurs devices (prend le premier)."""
    input_data = {
        "request_id": "test_build_006",
        "user_id": "user_test",
        "intent": "control_iot",
        "entities": {
            "devices": [
                {
                    "type": "light",
                    "location": "salon",
                    "action": "turn_on"
                },
                {
                    "type": "shutter",
                    "location": "salon",
                    "action": "close"
                }
            ]
        },
        "original_text": "Allume la lampe et ferme les volets du salon"
    }
    
    output = action_builder.build(input_data)
    
    # Devrait prendre le premier device
    assert output["payload"]["device_type"] == "light"
    assert output["payload"]["action"] == "turn_on"
    
    print(f"✅ Test multiple devices passed")


def test_build_unknown_location(action_builder):
    """Test avec location inconnue."""
    input_data = {
        "request_id": "test_build_007",
        "user_id": "user_test",
        "intent": "control_iot",
        "entities": {
            "devices": [
                {
                    "type": "light",
                    "location": "garage",  # Location non mappée
                    "action": "turn_off"
                }
            ]
        },
        "original_text": "Éteins la lampe du garage"
    }
    
    output = action_builder.build(input_data)
    
    # Devrait générer un device_id générique
    assert output["payload"]["device_id"] == "light_garage_001"
    assert output["payload"]["location"] == "garage"
    
    print(f"✅ Test unknown location passed")


@pytest.mark.asyncio
async def test_build_action_async(action_builder):
    """Test méthode async build_action."""
    llm_analysis = {
        "request_id": "test_async_001",
        "primary_intent": "control_iot",
        "confidence": 0.95,
        "entities": {
            "devices": [
                {
                    "type": "temperature",
                    "location": "salon",
                    "action": "set"
                }
            ]
        }
    }
    
    output = await action_builder.build_action(
        llm_analysis=llm_analysis,
        user_id="user_async",
        original_text="Règle le thermostat du salon à 22 degrés",
        language="fr"
    )
    
    assert output["intent"] == "control_iot"
    assert output["user_id"] == "user_async"
    assert output["payload"]["device_type"] == "temperature"
    assert output["payload"]["device_id"] == "thermostat_salon_001"
    
    print(f"✅ Test async build_action passed")


def test_build_empty_entities(action_builder):
    """Test avec entités vides."""
    input_data = {
        "request_id": "test_build_008",
        "user_id": "user_test",
        "intent": "control_iot",
        "entities": {},  # Vide
        "original_text": "Fais quelque chose"
    }
    
    output = action_builder.build(input_data)
    
    # Devrait créer un payload avec unknown
    assert output["payload"]["device_id"] == "unknown"
    assert output["payload"]["device_type"] == "unknown"
    
    print(f"✅ Test empty entities passed")


def test_action_id_uniqueness(action_builder):
    """Test unicité des action_id générés."""
    input_data = {
        "request_id": "test_unique",
        "user_id": "user_test",
        "intent": "control_iot",
        "entities": {
            "devices": [{"type": "light", "action": "turn_on"}]
        },
        "original_text": "Test"
    }
    
    # Générer 10 actions
    action_ids = set()
    for i in range(10):
        output = action_builder.build(input_data)
        action_ids.add(output["action_id"])
    
    # Tous doivent être uniques
    assert len(action_ids) == 10
    
    # Tous doivent commencer par "act_"
    for action_id in action_ids:
        assert action_id.startswith("act_")
        assert len(action_id) == 16  # act_ + 12 caractères hex
    
    print(f"✅ Test action_id uniqueness passed: {len(action_ids)} unique IDs")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
