"""
Tests unitaires - ConfirmationHandler
"""

import pytest
from backend.actions.confirmation_handler import ConfirmationHandler


@pytest.fixture
def confirmation_handler():
    """Fixture pour ConfirmationHandler."""
    return ConfirmationHandler()


def test_generate_iot_confirmation(confirmation_handler):
    """Test génération demande confirmation IoT."""
    input_data = {
        "action_json": {
            "action_id": "test_act_001",
            "user_id": "user_test",
            "intent": "control_iot",
            "payload": {
                "device_id": "lamp_salon_001",
                "device_type": "light",
                "action": "turn_on",
                "location": "salon"
            },
            "state": "DRAFT",
            "context": {
                "language": "fr"
            }
        },
        "language": "fr"
    }
    
    output = confirmation_handler.generate_request(input_data)
    
    assert output["action_id"] == "test_act_001"
    assert "allumer" in output["confirmation_text"].lower() or "allume" in output["confirmation_text"].lower()
    assert "lampe" in output["confirmation_text"].lower()
    assert "salon" in output["confirmation_text"].lower()
    assert len(output["options"]) >= 2
    assert output["timeout_seconds"] == 30
    
    # Vérifier les options
    option_actions = [opt["action"] for opt in output["options"]]
    assert "confirm" in option_actions
    assert "cancel" in option_actions
    
    print(f"✅ Test IoT confirmation generated: '{output['confirmation_text']}'")


def test_generate_email_confirmation(confirmation_handler):
    """Test génération demande confirmation Email."""
    input_data = {
        "action_json": {
            "action_id": "test_act_002",
            "user_id": "user_test",
            "intent": "send_email",
            "payload": {
                "recipient_name": "Jean",
                "recipient_email": "jean@example.com",
                "subject": "Réunion demain",
                "body": "Confirmez votre présence"
            },
            "state": "DRAFT",
            "context": {
                "language": "fr"
            }
        },
        "language": "fr"
    }
    
    output = confirmation_handler.generate_request(input_data)
    
    assert "email" in output["confirmation_text"].lower()
    assert "Jean" in output["confirmation_text"]
    
    # Vérifier action_summary
    assert output["action_summary"]["intent"] == "send_email"
    assert output["action_summary"]["recipient"] == "Jean"
    assert output["action_summary"]["subject"] == "Réunion demain"
    
    print(f"✅ Test email confirmation generated: '{output['confirmation_text']}'")


def test_generate_reminder_confirmation(confirmation_handler):
    """Test génération demande confirmation Rappel."""
    input_data = {
        "action_json": {
            "action_id": "test_act_003",
            "user_id": "user_test",
            "intent": "set_reminder",
            "payload": {
                "title": "Appeler le médecin",
                "reminder_time": "2026-02-11T14:30:00Z"
            },
            "state": "DRAFT",
            "context": {
                "language": "fr"
            }
        },
        "language": "fr"
    }
    
    output = confirmation_handler.generate_request(input_data)
    
    assert "rappel" in output["confirmation_text"].lower()
    assert "Appeler le médecin" in output["confirmation_text"]
    
    print(f"✅ Test reminder confirmation generated: '{output['confirmation_text']}'")


def test_parse_response_confirm_oui(confirmation_handler):
    """Test parse réponse 'oui' → CONFIRMED."""
    input_data = {
        "action_id": "test_act_004",
        "user_response": "oui",
        "user_id": "user_test"
    }
    
    output = confirmation_handler.parse_response(input_data)
    
    assert output["action_id"] == "test_act_004"
    assert output["parsed_response"]["intent"] == "confirm"
    assert output["parsed_response"]["confidence"] >= 0.95
    assert output["new_state"] == "CONFIRMED"
    
    print(f"✅ Test 'oui' → CONFIRMED passed")


def test_parse_response_confirm_yes(confirmation_handler):
    """Test parse réponse 'yes' → CONFIRMED."""
    input_data = {
        "action_id": "test_act_005",
        "user_response": "yes",
        "user_id": "user_test"
    }
    
    output = confirmation_handler.parse_response(input_data)
    
    assert output["parsed_response"]["intent"] == "confirm"
    assert output["new_state"] == "CONFIRMED"
    
    print(f"✅ Test 'yes' → CONFIRMED passed")


def test_parse_response_confirm_ok(confirmation_handler):
    """Test parse réponse 'ok' → CONFIRMED."""
    input_data = {
        "action_id": "test_act_006",
        "user_response": "ok d'accord",
        "user_id": "user_test"
    }
    
    output = confirmation_handler.parse_response(input_data)
    
    assert output["parsed_response"]["intent"] == "confirm"
    assert output["new_state"] == "CONFIRMED"
    
    print(f"✅ Test 'ok d'accord' → CONFIRMED passed")


def test_parse_response_cancel_non(confirmation_handler):
    """Test parse réponse 'non' → CANCELED."""
    input_data = {
        "action_id": "test_act_007",
        "user_response": "non",
        "user_id": "user_test"
    }
    
    output = confirmation_handler.parse_response(input_data)
    
    assert output["parsed_response"]["intent"] == "cancel"
    assert output["parsed_response"]["confidence"] >= 0.95
    assert output["new_state"] == "CANCELED"
    
    print(f"✅ Test 'non' → CANCELED passed")


def test_parse_response_cancel_no(confirmation_handler):
    """Test parse réponse 'no' → CANCELED."""
    input_data = {
        "action_id": "test_act_008",
        "user_response": "no, stop",
        "user_id": "user_test"
    }
    
    output = confirmation_handler.parse_response(input_data)
    
    assert output["parsed_response"]["intent"] == "cancel"
    assert output["new_state"] == "CANCELED"
    
    print(f"✅ Test 'no, stop' → CANCELED passed")


def test_parse_response_modify(confirmation_handler):
    """Test parse réponse 'modifier' → DRAFT."""
    input_data = {
        "action_id": "test_act_009",
        "user_response": "modifier",
        "user_id": "user_test"
    }
    
    output = confirmation_handler.parse_response(input_data)
    
    assert output["parsed_response"]["intent"] == "modify"
    assert output["parsed_response"]["confidence"] >= 0.90
    assert output["new_state"] == "DRAFT"
    
    print(f"✅ Test 'modifier' → DRAFT passed")


def test_parse_response_modify_change(confirmation_handler):
    """Test parse réponse 'change' → DRAFT."""
    input_data = {
        "action_id": "test_act_010",
        "user_response": "I want to change something",
        "user_id": "user_test"
    }
    
    output = confirmation_handler.parse_response(input_data)
    
    assert output["parsed_response"]["intent"] == "modify"
    assert output["new_state"] == "DRAFT"
    
    print(f"✅ Test 'change' → DRAFT passed")


def test_parse_response_unknown(confirmation_handler):
    """Test parse réponse inconnue → DRAFT par sécurité."""
    input_data = {
        "action_id": "test_act_011",
        "user_response": "peut-être demain",
        "user_id": "user_test"
    }
    
    output = confirmation_handler.parse_response(input_data)
    
    assert output["parsed_response"]["intent"] == "unknown"
    assert output["parsed_response"]["confidence"] < 0.5
    assert output["new_state"] == "DRAFT"  # Reste DRAFT par sécurité
    
    print(f"✅ Test unknown response → DRAFT passed")


def test_parse_response_could_not_transcribe_not_cancel(confirmation_handler):
    """Régression: ne pas annuler quand la phrase contient 'not'."""
    input_data = {
        "action_id": "test_act_not_001",
        "user_response": "Could not transcribe",
        "user_id": "user_test"
    }

    output = confirmation_handler.parse_response(input_data)

    assert output["parsed_response"]["intent"] == "unknown"
    assert output["new_state"] == "DRAFT"


def test_parse_response_case_insensitive(confirmation_handler):
    """Test parsing insensible à la casse."""
    test_cases = [
        ("OUI", "confirm"),
        ("NON", "cancel"),
        ("Yes", "confirm"),
        ("NO", "cancel"),
        ("MODIFIER", "modify")
    ]
    
    for user_response, expected_intent in test_cases:
        input_data = {
            "action_id": "test_case",
            "user_response": user_response,
            "user_id": "user_test"
        }
        
        output = confirmation_handler.parse_response(input_data)
        assert output["parsed_response"]["intent"] == expected_intent
    
    print(f"✅ Test case insensitive passed ({len(test_cases)} cases)")


@pytest.mark.asyncio
async def test_generate_confirmation_async(confirmation_handler):
    """Test méthode async generate_confirmation."""
    action_json = {
        "action_id": "test_async_001",
        "intent": "control_iot",
        "payload": {
            "device_type": "shutter",
            "action": "close",
            "location": "chambre"
        },
        "context": {
            "language": "fr"
        }
    }
    
    confirmation_text = await confirmation_handler.generate_confirmation(action_json)
    
    assert isinstance(confirmation_text, str)
    assert len(confirmation_text) > 10
    assert "?" in confirmation_text  # Question
    
    print(f"✅ Test async generate_confirmation passed: '{confirmation_text}'")


@pytest.mark.asyncio
async def test_parse_response_async(confirmation_handler):
    """Test méthode parse_response dans contexte async."""
    input_data = {
        "action_id": "test_async_parse",
        "user_response": "oui vas-y",
        "user_id": "user_test"
    }
    
    # parse_response est synchrone mais peut être appelé depuis contexte async
    result = confirmation_handler.parse_response(input_data)
    
    assert result["parsed_response"]["intent"] == "confirm"
    assert result["parsed_response"]["confidence"] > 0.9
    
    print(f"✅ Test parse_response in async context passed")


def test_generate_iot_without_location(confirmation_handler):
    """Test génération confirmation IoT sans location."""
    input_data = {
        "action_json": {
            "action_id": "test_no_loc",
            "intent": "control_iot",
            "payload": {
                "device_type": "light",
                "action": "turn_off",
                "location": None
            },
            "context": {"language": "fr"}
        },
        "language": "fr"
    }
    
    output = confirmation_handler.generate_request(input_data)
    
    # Devrait générer texte sans location
    assert "lampe" in output["confirmation_text"].lower()
    assert output["confirmation_text"].count("?") == 1  # Une question
    
    print(f"✅ Test IoT without location passed")


def test_bilingual_keywords(confirmation_handler):
    """Test support mots-clés bilingues FR + EN."""
    french_confirms = ["oui", "d'accord", "ok", "valide", "confirme"]
    english_confirms = ["yes", "yeah", "yep", "correct"]
    
    for keyword in french_confirms + english_confirms:
        input_data = {
            "action_id": "test_bilingual",
            "user_response": keyword,
            "user_id": "user_test"
        }
        
        output = confirmation_handler.parse_response(input_data)
        assert output["parsed_response"]["intent"] == "confirm", f"Failed for keyword: {keyword}"
    
    print(f"✅ Test bilingual keywords passed ({len(french_confirms + english_confirms)} keywords)")


def test_action_summary_structure(confirmation_handler):
    """Test structure action_summary dans output."""
    input_data = {
        "action_json": {
            "action_id": "test_summary",
            "intent": "control_iot",
            "payload": {
                "device_type": "temperature",
                "action": "set",
                "location": "salon"
            },
            "context": {"language": "fr"}
        },
        "language": "fr"
    }
    
    output = confirmation_handler.generate_request(input_data)
    
    # Vérifier structure action_summary
    assert "action_summary" in output
    assert output["action_summary"]["intent"] == "control_iot"
    assert "target" in output["action_summary"]
    assert "action" in output["action_summary"]
    
    print(f"✅ Test action_summary structure passed")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
