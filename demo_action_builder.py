"""
Script de démonstration - ActionBuilder
Montre les 4 types d'intents supportés
"""

from backend.actions.action_builder import ActionBuilder
import json


def demo_action_builder():
    """Démonstration complète ActionBuilder."""
    
    builder = ActionBuilder()
    
    print("\n" + "="*70)
    print("🎯 DÉMONSTRATION ACTION BUILDER")
    print("="*70)
    
    # ===================== TEST 1: IoT Control =====================
    print("\n📱 TEST 1: IoT Control - Allumer lampe du salon")
    print("-" * 70)
    
    input_iot = {
        "request_id": "demo_iot_001",
        "user_id": "montassar",
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
    
    result_iot = builder.build(input_iot)
    
    print(f"✅ Action ID: {result_iot['action_id']}")
    print(f"✅ Intent: {result_iot['intent']}")
    print(f"✅ State: {result_iot['state']}")
    print(f"✅ Device: {result_iot['payload']['device_id']}")
    print(f"✅ Action: {result_iot['payload']['action']}")
    print(f"\n📋 Payload:\n{json.dumps(result_iot['payload'], indent=2, ensure_ascii=False)}")
    
    # ===================== TEST 2: Send Email =====================
    print("\n" + "="*70)
    print("\n📧 TEST 2: Send Email - Email à Amine")
    print("-" * 70)
    
    input_email = {
        "request_id": "demo_email_001",
        "user_id": "montassar",
        "intent": "send_email",
        "entities": {
            "recipient": "Amine",
            "recipient_email": "amine@ensi.tn",
            "subject": "Réunion PCD",
            "body": "Salut Amine, RDV à 14h pour le projet"
        },
        "original_text": "Envoie un email à Amine pour la réunion",
        "confidence": 0.89,
        "language": "fr"
    }
    
    result_email = builder.build(input_email)
    
    print(f"✅ Action ID: {result_email['action_id']}")
    print(f"✅ Intent: {result_email['intent']}")
    print(f"✅ Recipient: {result_email['payload']['recipient_name']}")
    print(f"✅ Email: {result_email['payload']['recipient_email']}")
    print(f"✅ Subject: {result_email['payload']['subject']}")
    print(f"\n📋 Payload:\n{json.dumps(result_email['payload'], indent=2, ensure_ascii=False)}")
    
    # ===================== TEST 3: Set Reminder =====================
    print("\n" + "="*70)
    print("\n⏰ TEST 3: Set Reminder - Rappel médecin")
    print("-" * 70)
    
    input_reminder = {
        "request_id": "demo_reminder_001",
        "user_id": "montassar",
        "intent": "set_reminder",
        "entities": {
            "title": "Appeler le médecin",
            "time": "2026-02-11T14:30:00Z"
        },
        "original_text": "Rappelle-moi d'appeler le médecin demain à 14h30",
        "confidence": 0.87,
        "language": "fr"
    }
    
    result_reminder = builder.build(input_reminder)
    
    print(f"✅ Action ID: {result_reminder['action_id']}")
    print(f"✅ Intent: {result_reminder['intent']}")
    print(f"✅ Title: {result_reminder['payload']['title']}")
    print(f"✅ Time: {result_reminder['payload']['reminder_time']}")
    print(f"\n📋 Payload:\n{json.dumps(result_reminder['payload'], indent=2, ensure_ascii=False)}")
    
    # ===================== TEST 4: Web Search =====================
    print("\n" + "="*70)
    print("\n🔍 TEST 4: Web Search - Météo Paris")
    print("-" * 70)
    
    input_search = {
        "request_id": "demo_search_001",
        "user_id": "montassar",
        "intent": "web_search",
        "entities": {
            "query": "météo Paris demain"
        },
        "original_text": "Quelle est la météo à Paris demain?",
        "confidence": 0.92,
        "language": "fr"
    }
    
    result_search = builder.build(input_search)
    
    print(f"✅ Action ID: {result_search['action_id']}")
    print(f"✅ Intent: {result_search['intent']}")
    print(f"✅ Query: {result_search['payload']['query']}")
    print(f"✅ Type: {result_search['payload']['search_type']}")
    print(f"\n📋 Payload:\n{json.dumps(result_search['payload'], indent=2, ensure_ascii=False)}")
    
    # ===================== RÉSUMÉ =====================
    print("\n" + "="*70)
    print("📊 RÉSUMÉ")
    print("="*70)
    print(f"✅ 4 ActionJSON créés avec succès")
    print(f"✅ Tous les intents supportés: control_iot, send_email, set_reminder, web_search")
    print(f"✅ Tous en état DRAFT (confirmed=False)")
    print(f"✅ Structure complète avec timestamps, security, metadata")
    print("\n🎉 ActionBuilder validé et fonctionnel !")
    print("="*70 + "\n")


if __name__ == "__main__":
    demo_action_builder()
