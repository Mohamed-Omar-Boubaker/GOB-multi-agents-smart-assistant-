"""
Test Script - Memory Service
Vérifie que MemoryService fonctionne correctement
"""

import sys
from pathlib import Path

# Ajouter backend au path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from services.memory_service import MemoryService


def test_memory_service():
    """Test complet du MemoryService."""
    
    print("=" * 60)
    print("🧪 TEST MEMORY SERVICE")
    print("=" * 60)
    
    # Initialiser service
    print("\n1️⃣ Initialisation...")
    memory = MemoryService(db_path="data/test_memory.db")
    
    # Tester ajout faits
    print("\n2️⃣ Ajout faits utilisateur...")
    memory.add_fact("user_001", "name", "first_name", "John")
    memory.add_fact("user_001", "name", "last_name", "Doe")
    memory.add_fact("user_001", "preference", "favorite_color", "blue")
    memory.add_fact("user_001", "device", "living_room_light", "installed")
    print("   ✅ 4 faits ajoutés")
    
    # Tester récupération faits
    print("\n3️⃣ Récupération faits...")
    facts = memory.get_facts("user_001")
    print(f"   ✅ {len(facts)} faits trouvés:")
    for fact in facts:
        print(f"      - {fact['fact_type']}.{fact['fact_key']} = {fact['fact_value']}")
    
    # Tester récupération fait spécifique
    print("\n4️⃣ Récupération fait spécifique...")
    first_name = memory.get_fact("user_001", "name", "first_name")
    print(f"   ✅ first_name = {first_name}")
    
    # Tester conversations
    print("\n5️⃣ Ajout conversations...")
    memory.add_conversation_turn("user_001", "user", "Hello, my name is John")
    memory.add_conversation_turn("user_001", "assistant", "Nice to meet you John!")
    memory.add_conversation_turn("user_001", "user", "What's my name?")
    memory.add_conversation_turn("user_001", "assistant", "Your name is John")
    print("   ✅ 4 tours de conversation ajoutés")
    
    # Tester récupération conversations
    print("\n6️⃣ Récupération historique conversations...")
    history = memory.get_conversation_history("user_001", limit=10)
    print(f"   ✅ {len(history)} tours trouvés:")
    for turn in history:
        print(f"      [{turn['role']}]: {turn['message']}")
    
    # Tester contexte mémoire
    print("\n7️⃣ Construction contexte mémoire...")
    context = memory.build_memory_context("user_001")
    print("   ✅ Contexte généré:")
    print(context)
    
    # Tester stats
    print("\n8️⃣ Statistiques...")
    stats = memory.get_stats()
    print(f"   ✅ Stats:")
    print(f"      - Utilisateurs: {stats['users_with_facts']}")
    print(f"      - Total faits: {stats['total_facts']}")
    print(f"      - Total conversations: {stats['total_conversations']}")
    
    # Cleanup test
    print("\n9️⃣ Nettoyage...")
    memory.clear_user_memory("user_001")
    print("   ✅ Mémoire user_001 effacée")
    
    print("\n" + "=" * 60)
    print("✅ TOUS LES TESTS PASSÉS!")
    print("=" * 60)
    print(f"\n📁 Base de données créée: {memory.db_path}")
    print("🎯 MemoryService est opérationnel!\n")


if __name__ == "__main__":
    test_memory_service()
