"""
Memory Viewer - Voir et Gérer la Mémoire SQLite
Date: 12 Février 2026

Usage:
    python view_memory.py                    # Voir statistiques
    python view_memory.py list               # Liste tous les users
    python view_memory.py view USER_ID       # Voir mémoire d'un user
    python view_memory.py clear USER_ID      # Effacer mémoire d'un user
    python view_memory.py export USER_ID     # Exporter en JSON
"""

import sys
import json
from pathlib import Path
from services.memory_service import MemoryService


def print_banner():
    """Affiche banner."""
    print("=" * 70)
    print("🧠 MEMORY VIEWER - Agent Intelligent")
    print("=" * 70)


def show_stats(memory: MemoryService):
    """Affiche statistiques globales."""
    print("\n📊 STATISTIQUES GLOBALES\n")
    stats = memory.get_stats()
    print(f"  📁 Database: {stats['database_path']}")
    print(f"  👥 Utilisateurs avec faits: {stats['users_with_facts']}")
    print(f"  📝 Total faits stockés: {stats['total_facts']}")
    print(f"  💬 Total conversations: {stats['total_conversations']}")
    print()


def list_users(memory: MemoryService):
    """Liste tous les utilisateurs."""
    print("\n👥 LISTE DES UTILISATEURS\n")
    
    # Query SQLite directement pour avoir la liste unique des users
    import sqlite3
    conn = sqlite3.connect(memory.db_path)
    cursor = conn.cursor()
    
    # Users avec faits
    cursor.execute("SELECT DISTINCT user_id FROM user_facts")
    users_facts = [row[0] for row in cursor.fetchall()]
    
    # Users avec conversations
    cursor.execute("SELECT DISTINCT user_id FROM conversations")
    users_convs = [row[0] for row in cursor.fetchall()]
    
    conn.close()
    
    all_users = set(users_facts + users_convs)
    
    if not all_users:
        print("  ℹ️  Aucun utilisateur trouvé")
        return
    
    for user_id in sorted(all_users):
        facts_count = len(memory.get_facts(user_id))
        history = memory.get_conversation_history(user_id, limit=1000)
        conv_count = len(history)
        print(f"  • {user_id}")
        print(f"      Facts: {facts_count} | Conversations: {conv_count} tours")
    print()


def view_user_memory(memory: MemoryService, user_id: str):
    """Affiche toute la mémoire d'un utilisateur."""
    print(f"\n🔍 MÉMOIRE DE: {user_id}\n")
    
    # 1. Faits utilisateur
    facts = memory.get_facts(user_id)
    if facts:
        print("📌 FAITS UTILISATEUR:")
        for fact in facts:
            print(f"  • {fact['fact_type']}.{fact['fact_key']} = {fact['fact_value']}")
            print(f"    Confidence: {fact['confidence']:.2f} | Updated: {fact['updated_at'][:19]}")
        print()
    else:
        print("  ℹ️  Aucun fait stocké\n")
    
    # 2. Historique conversations
    history = memory.get_conversation_history(user_id, limit=100)
    if history:
        print(f"💬 HISTORIQUE CONVERSATIONS ({len(history)} derniers tours):")
        for i, turn in enumerate(history[-20:], 1):  # Afficher derniers 20 tours
            role_emoji = "👤" if turn['role'] == "user" else "🤖"
            timestamp = turn['timestamp'][:19] if 'timestamp' in turn else "N/A"
            print(f"  {i}. {role_emoji} [{timestamp}] {turn['message']}")
        print()
    else:
        print("  ℹ️  Aucune conversation\n")
    
    # 3. Contexte mémoire (comme vu par le LLM)
    context = memory.build_memory_context(user_id)
    if context:
        print("🧠 CONTEXTE MÉMOIRE (vu par le LLM):")
        print("-" * 70)
        print(context)
        print("-" * 70)
        print()


def clear_user_memory(memory: MemoryService, user_id: str):
    """Efface la mémoire d'un utilisateur."""
    print(f"\n⚠️  EFFACEMENT MÉMOIRE DE: {user_id}\n")
    
    response = input("  Êtes-vous sûr? (oui/non): ").lower().strip()
    
    if response in ["oui", "yes", "y"]:
        success = memory.clear_user_memory(user_id)
        if success:
            print(f"  ✅ Mémoire de {user_id} effacée avec succès\n")
        else:
            print(f"  ❌ Erreur lors de l'effacement\n")
    else:
        print("  ℹ️  Opération annulée\n")


def export_user_memory(memory: MemoryService, user_id: str):
    """Exporte la mémoire en JSON."""
    print(f"\n📤 EXPORT MÉMOIRE DE: {user_id}\n")
    
    data = {
        "user_id": user_id,
        "facts": memory.get_facts(user_id),
        "conversations": memory.get_conversation_history(user_id, limit=1000)
    }
    
    filename = f"memory_export_{user_id}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"  ✅ Exporté vers: {filename}")
    print(f"  📊 {len(data['facts'])} faits | {len(data['conversations'])} conversations\n")


def main():
    """Point d'entrée principal."""
    print_banner()
    
    # Initialiser MemoryService with correct path
    # Use parent directory if running from backend/
    db_path = Path(__file__).parent.parent / "data" / "agent_memory.db"
    memory = MemoryService(db_path=str(db_path))
    
    # Parser arguments
    if len(sys.argv) == 1:
        # Pas d'arguments → Afficher stats
        show_stats(memory)
        print("💡 Usage:")
        print("  python view_memory.py list              # Liste utilisateurs")
        print("  python view_memory.py view USER_ID      # Voir mémoire utilisateur")
        print("  python view_memory.py clear USER_ID     # Effacer mémoire")
        print("  python view_memory.py export USER_ID    # Exporter JSON")
        print()
    
    elif sys.argv[1] == "list":
        show_stats(memory)
        list_users(memory)
    
    elif sys.argv[1] == "view":
        if len(sys.argv) < 3:
            print("❌ Usage: python view_memory.py view USER_ID\n")
            sys.exit(1)
        user_id = sys.argv[2]
        view_user_memory(memory, user_id)
    
    elif sys.argv[1] == "clear":
        if len(sys.argv) < 3:
            print("❌ Usage: python view_memory.py clear USER_ID\n")
            sys.exit(1)
        user_id = sys.argv[2]
        clear_user_memory(memory, user_id)
    
    elif sys.argv[1] == "export":
        if len(sys.argv) < 3:
            print("❌ Usage: python view_memory.py export USER_ID\n")
            sys.exit(1)
        user_id = sys.argv[2]
        export_user_memory(memory, user_id)
    
    else:
        print(f"❌ Commande inconnue: {sys.argv[1]}\n")
        print("Commandes disponibles: list, view, clear, export\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
