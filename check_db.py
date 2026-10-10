"""Script rapide pour voir le contenu de la base de données"""
import sqlite3
from pathlib import Path

db_path = Path("data/agent_memory.db")

print(f"📁 Database: {db_path}")
print("=" * 70)

conn = sqlite3.connect(db_path)

# Conversations
print("\n🗨️  DERNIÈRES CONVERSATIONS:")
print("-" * 70)
cursor = conn.execute("""
    SELECT user_id, role, message, timestamp 
    FROM conversations 
    ORDER BY id DESC 
    LIMIT 5
""")
for row in cursor:
    user_id, role, message, timestamp = row
    emoji = "👤" if role == "user" else "🤖"
    print(f"{emoji} [{timestamp[:19]}] {user_id}")
    print(f"   {message[:80]}...")
    print()

# User Facts
print("\n📝 USER FACTS (Données extraites):")
print("-" * 70)
cursor = conn.execute("SELECT COUNT(*) FROM user_facts")
count = cursor.fetchone()[0]
print(f"Total: {count} faits stockés\n")

if count > 0:
    cursor = conn.execute("""
        SELECT user_id, fact_key, fact_value, confidence, timestamp 
        FROM user_facts 
        ORDER BY id DESC 
        LIMIT 20
    """)
    for row in cursor:
        user_id, key, value, confidence, timestamp = row
        print(f"✅ {user_id} | {key}: {value} (confiance: {confidence})")
        print(f"   Timestamp: {timestamp}")
        print()
else:
    print("❌ Aucun fait extrait trouvé!")
    print("   → Le Memory Extractor n'a pas encore sauvegardé de données")

conn.close()

print("=" * 70)
print("💡 Les données devraient apparaître ici si le Memory Extractor fonctionne")
