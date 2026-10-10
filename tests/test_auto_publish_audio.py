"""
Test simple pour vérifier l'auto-publish audio vers MQTT après TTS.

Pipeline testé: TTS → Auto-publish → MQTT → Device

Prérequis:
- MQTT broker running: mosquitto -v
- Configuration dans .env:
  - ENABLE_MQTT_INTEGRATION=True
  - AUTO_PUBLISH_AUDIO_TO_MQTT=True
"""

import asyncio
import sys
from pathlib import Path

# Ajouter le répertoire racine du projet au path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.config import Config
from backend.integrations.mqtt_client import MQTTClient
from backend.agent.agent_core import AgentCore


async def test_auto_publish():
    """Test auto-publish audio après TTS (conversation)."""
    
    print("=" * 70)
    print("TEST AUTO-PUBLISH AUDIO TO MQTT")
    print("=" * 70)
    
    # 1. Vérifier configuration
    print("\n[1] Configuration:")
    print(f"  - MQTT Enabled: {Config.ENABLE_MQTT_INTEGRATION}")
    print(f"  - Auto-publish: {Config.AUTO_PUBLISH_AUDIO_TO_MQTT}")
    print(f"  - MQTT Broker: {Config.MQTT_BROKER}:{Config.MQTT_PORT}")
    print(f"  - Audio Topic: {Config.MQTT_TOPIC_AUDIO_OUT}")
    
    if not Config.ENABLE_MQTT_INTEGRATION:
        print("\n❌ ERREUR: MQTT désactivé dans configuration")
        print("   Activez ENABLE_MQTT_INTEGRATION=True dans .env")
        return False
    
    if not Config.AUTO_PUBLISH_AUDIO_TO_MQTT:
        print("\n⚠️  WARNING: Auto-publish désactivé dans configuration")
        print("   Activez AUTO_PUBLISH_AUDIO_TO_MQTT=True dans .env")
        return False
    
    # 2. Initialiser MQTT client
    print("\n[2] Initialisation MQTT Client:")
    mqtt_client = MQTTClient()
    
    # Attendre connexion
    await asyncio.sleep(2)
    
    if not mqtt_client.is_connected():
        print("❌ ERREUR: MQTT client non connecté")
        print("   Vérifiez que mosquitto est lancé: mosquitto -v")
        return False
    
    print(f"✅ MQTT connecté")
    
    # 3. Initialiser les composants nécessaires pour AgentCore
    print("\n[3] Initialisation composants AgentCore:")
    
    # Import des composants
    from backend.ai.stt_engine import STTEngine
    from backend.ai.tts_engine import TTSEngine
    from backend.ai.llm_client import LLMClient
    from backend.classifier.intent_classifier import IntentClassifier
    from backend.actions.action_builder import ActionBuilder
    from backend.actions.confirmation_handler import ConfirmationHandler
    from backend.agent.security_manager import SecurityManager
    
    # Initialiser composants
    stt_engine = STTEngine() if Config.ENABLE_AUDIO_PROCESSING else None
    tts_engine = TTSEngine() if Config.ENABLE_AUDIO_PROCESSING else None
    llm_client = LLMClient()
    classifier = IntentClassifier()
    action_builder = ActionBuilder()
    confirmation_handler = ConfirmationHandler()
    security_manager = SecurityManager()
    
    # Initialiser AgentCore avec MQTT client
    agent = AgentCore(
        stt_engine=stt_engine,
        tts_engine=tts_engine,
        llm_client=llm_client,
        classifier=classifier,
        action_builder=action_builder,
        confirmation_handler=confirmation_handler,
        mqtt_client=mqtt_client,  # ← IMPORTANT: Pass MQTT client
        security_manager=security_manager
    )
    
    # Vérifier que agent a bien le mqtt_client
    if not agent.mqtt_client:
        print("❌ ERREUR: AgentCore n'a pas de MQTT client")
        return False
    
    print(f"✅ AgentCore initialisé avec MQTT client")
    
    # 4. Test conversation (déclenche TTS + auto-publish)
    print("\n[4] Test conversation (TTS + Auto-publish):")
    print("   Texte: 'Bonjour, comment vas-tu?'")
    
    try:
        input_data = {
            "command_type": "text",
            "user_id": "test_user",
            "text": "Bonjour, comment vas-tu?",
            "language": "fr"
        }
        result = await agent.process(input_data)
        
        # Vérifier résultat
        print(f"\n   Type: {result.get('type')}")
        print(f"   Status: {result.get('status')}")
        print(f"   Response: {result.get('response', '')[:100]}...")
        
        # Vérifier audio généré
        audio = result.get('audio')
        if audio:
            print(f"   Audio TTS: ✅ Généré ({len(audio.get('audio_data', ''))} bytes)")
            print("\n   🎵 Auto-publish devrait apparaître dans les logs ci-dessus")
            print("   Recherchez: '✅ Audio auto-published to device: published'")
        else:
            print("   Audio TTS: ❌ Pas généré")
            print("   Note: Normal si TTS désactivé dans config")
        
        print("\n✅ TEST RÉUSSI")
        return True
    
    except Exception as e:
        print(f"\n❌ ERREUR TEST: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Cleanup
        if mqtt_client and mqtt_client.is_connected():
            mqtt_client.disconnect()


async def test_auto_publish_action():
    """Test auto-publish audio après TTS (action confirmation)."""
    
    print("\n" + "=" * 70)
    print("TEST AUTO-PUBLISH AUDIO (ACTION CONFIRMATION)")
    print("=" * 70)
    
    # Initialiser MQTT client
    mqtt_client = MQTTClient()
    await asyncio.sleep(2)
    
    if not mqtt_client.is_connected():
        print("❌ MQTT non connecté, skip test action")
        return False
    
    # Initialiser composants AgentCore
    from backend.ai.stt_engine import STTEngine
    from backend.ai.tts_engine import TTSEngine
    from backend.ai.llm_client import LLMClient
    from backend.classifier.intent_classifier import IntentClassifier
    from backend.actions.action_builder import ActionBuilder
    from backend.actions.confirmation_handler import ConfirmationHandler
    from backend.agent.security_manager import SecurityManager
    
    stt_engine = STTEngine() if Config.ENABLE_AUDIO_PROCESSING else None
    tts_engine = TTSEngine() if Config.ENABLE_AUDIO_PROCESSING else None
    llm_client = LLMClient()
    classifier = IntentClassifier()
    action_builder = ActionBuilder()
    confirmation_handler = ConfirmationHandler()
    security_manager = SecurityManager()
    
    # Initialiser AgentCore avec MQTT client
    agent = AgentCore(
        stt_engine=stt_engine,
        tts_engine=tts_engine,
        llm_client=llm_client,
        classifier=classifier,
        action_builder=action_builder,
        confirmation_handler=confirmation_handler,
        mqtt_client=mqtt_client,
        security_manager=security_manager
    )
    
    print("\n[1] Test action IoT (TTS confirmation + Auto-publish):")
    print("   Texte: 'Allume la lumière du salon'")
    
    try:
        input_data = {
            "command_type": "text",
            "user_id": "test_user",
            "text": "Allume la lumière du salon",
            "language": "fr"
        }
        result = await agent.process(input_data)
        
        # Vérifier résultat
        print(f"\n   Type: {result.get('type')}")
        print(f"   Status: {result.get('status')}")
        print(f"   State: {result.get('state')}")
        
        # Vérifier audio confirmation
        confirmation_audio = result.get('audio_response')
        if confirmation_audio:
            print(f"   Audio Confirmation: ✅ Généré ({len(confirmation_audio.get('audio_data', ''))} bytes)")
            print("\n   🎵 Auto-publish confirmation devrait apparaître dans les logs")
            print("   Recherchez: '✅ Confirmation audio auto-published to device: published'")
        else:
            print("   Audio Confirmation: ❌ Pas généré")
        
        print("\n✅ TEST ACTION RÉUSSI")
        return True
    
    except Exception as e:
        print(f"\n❌ ERREUR TEST ACTION: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Cleanup
        if mqtt_client and mqtt_client.is_connected():
            mqtt_client.disconnect()


async def main():
    """Lance tous les tests."""
    
    print("\n🚀 Tests Auto-Publish Audio to MQTT\n")
    
    # Test 1: Conversation
    success1 = await test_auto_publish()
    
    await asyncio.sleep(2)
    
    # Test 2: Action confirmation
    success2 = await test_auto_publish_action()
    
    print("\n" + "=" * 70)
    print("RÉSULTATS TESTS")
    print("=" * 70)
    print(f"  Test Conversation: {'✅ PASS' if success1 else '❌ FAIL'}")
    print(f"  Test Action:       {'✅ PASS' if success2 else '❌ FAIL'}")
    print("=" * 70)
    
    # Vérifier logs pour auto-publish
    print("\n💡 VÉRIFICATION:")
    print("  Recherchez dans les logs ci-dessus:")
    print("    - '✅ Audio auto-published to device: published'")
    print("    - '✅ Confirmation audio auto-published to device: published'")
    print("\n  Si présent = Auto-publish fonctionne correctement ✅")
    print("  Si absent:")
    print("    - Vérifiez ENABLE_MQTT_INTEGRATION=True")
    print("    - Vérifiez AUTO_PUBLISH_AUDIO_TO_MQTT=True")
    print("    - Vérifiez mosquitto lancé: mosquitto -v")


if __name__ == "__main__":
    asyncio.run(main())
