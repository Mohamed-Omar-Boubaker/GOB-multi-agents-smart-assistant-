"""
Test intégration validation - ActionBuilder
"""
import sys
import asyncio
sys.path.insert(0, '.')

from backend.actions.action_builder import ActionBuilder

async def test_action_builder():
    print("\n" + "=" * 70)
    print("🧪 TEST INTÉGRATION - ActionBuilder avec Validation")
    print("=" * 70)
    
    builder = ActionBuilder()
    
    # Test 1: Données valides
    print("\n📦 Test 1: ActionJSON valide")
    input_valid = {
        "request_id": "req_test_001",
        "user_id": "user_montassar",
        "intent": "control_iot",
        "entities": {
            "devices": [{
                "type": "light",
                "location": "salon",
                "action": "turn_on"
            }]
        },
        "original_text": "Allume la lampe du salon",
        "confidence": 0.95,
        "language": "fr"
    }
    
    try:
        result = builder.build(input_valid)
        print(f"✅ ActionJSON créé et validé: {result['action_id']}")
        print(f"   Intent: {result['intent']}")
        print(f"   Device: {result['payload']['device_id']}")
        print(f"   State: {result['state']}")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    # Test 2: Données invalides (devrait échouer)
    print("\n📦 Test 2: ActionJSON invalide (intent manquant)")
    input_invalid = {
        "user_id": "user_test",
        # intent manquant
        "entities": {}
    }
    
    try:
        result = builder.build(input_invalid)
        print(f"❌ ERREUR: Devrait avoir échoué mais a réussi!")
    except ValueError as e:
        print(f"✅ Validation a correctement échoué: {e}")
    except Exception as e:
        print(f"✅ Exception levée (comportement attendu): {type(e).__name__}")
    
    # Test 3: Async build_action
    print("\n📦 Test 3: build_action() async avec validation")
    llm_analysis = {
        "request_id": "req_async_001",
        "primary_intent": "send_email",
        "confidence": 0.89,
        "entities": {
            "recipient": "Amine",
            "recipient_email": "amine@ensi.tn",
            "subject": "Test validation",
            "body": "Message de test"
        }
    }
    
    try:
        result = await builder.build_action(
            llm_analysis=llm_analysis,
            user_id="user_montassar",
            original_text="Envoie un email à Amine",
            language="fr"
        )
        print(f"✅ ActionJSON async créé et validé: {result['action_id']}")
        print(f"   Intent: {result['intent']}")
        print(f"   Recipient: {result['payload']['recipient_email']}")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    print("\n" + "=" * 70)
    print("✅ TESTS TERMINÉS")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(test_action_builder())
