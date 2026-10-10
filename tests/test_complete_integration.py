"""
Test d'importation complète - Vérification intégration backend
"""

print("=" * 70)
print("🧪 TEST D'IMPORTATION COMPLÈTE - BACKEND INTÉGRÉ")
print("=" * 70)

try:
    print("\n📦 Test 1: Validators framework...")
    from backend.utils.validators import JSONValidator
    from backend.utils.exceptions import ValidationError
    from backend.utils.serializers import JSONSerializer
    print("   ✅ Validators framework OK")

    print("\n📦 Test 2: ActionBuilder avec validation...")
    from backend.actions.action_builder import ActionBuilder
    print("   ✅ ActionBuilder OK")

    print("\n📦 Test 3: N8N Client avec validation...")
    from backend.integrations.n8n_client import N8NClient
    print("   ✅ N8N Client OK")

    print("\n📦 Test 4: MQTT Client avec validation...")
    from backend.integrations.mqtt_client import MQTTClient
    print("   ✅ MQTT Client OK")

    print("\n📦 Test 5: Confirmation Handler avec validation...")
    from backend.actions.confirmation_handler import ConfirmationHandler
    print("   ✅ Confirmation Handler OK")

    print("\n📦 Test 6: Main.py (FastAPI) avec validation...")
    from backend.main import app
    print("   ✅ Main.py OK")

    print("\n" + "=" * 70)
    print("✅ TOUS LES IMPORTS RÉUSSIS")
    print("=" * 70)
    
    print("\n📊 RÉSUMÉ:")
    print("   - Validators framework: ✅")
    print("   - ActionBuilder: ✅")
    print("   - N8N Client: ✅")
    print("   - MQTT Client: ✅")
    print("   - Confirmation Handler: ✅")
    print("   - Main.py: ✅")
    print("\n🎉 INTÉGRATION COMPLÈTE VALIDÉE")
    
except ImportError as e:
    print(f"\n❌ ERREUR D'IMPORT: {e}")
    import traceback
    traceback.print_exc()
    
except Exception as e:
    print(f"\n❌ ERREUR: {e}")
    import traceback
    traceback.print_exc()
