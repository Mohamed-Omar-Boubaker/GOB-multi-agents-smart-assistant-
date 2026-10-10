"""Test rapide du Memory Extractor"""
import asyncio
from backend.ai.llm_client import LLMClient
from backend.services.memory_service import MemoryService
from backend.services.memory_extractor import MemoryExtractor

async def test():
    print("🔧 Initialisation...")
    
    # Init composants
    llm_client = LLMClient()
    memory_service = MemoryService(db_path="data/agent_memory.db")
    
    # Init Memory Extractor
    extractor = MemoryExtractor(
        llm_client=llm_client,
        memory_service=memory_service,
        enable_cache=True
    )
    
    print("✅ Memory Extractor créé\n")
    
    # Test extraction
    print("🧪 Test extraction avec : 'My name is Yamin' et 'I like pizza'")
    print("-" * 60)
    
    result = await extractor.extract_from_conversation(
        user_message="My name is Yamin. I like pizza and coffee.",
        user_id="test_user",
        assistant_response="Nice! I'll remember that!",
        store_results=True
    )
    
    print("\n📊 RÉSULTAT:")
    print(f"Entities: {result.get('entities', [])}")
    print(f"Emotion: {result.get('emotion')}")
    print(f"Intent: {result.get('intent')}")
    print(f"Summary: {result.get('summary')}")
    
    # Vérifier base de données
    print("\n" + "=" * 60)
    print("📝 Vérification base de données:")
    
    import sqlite3
    conn = sqlite3.connect("data/agent_memory.db")
    cursor = conn.execute("SELECT COUNT(*) FROM user_facts")
    count = cursor.fetchone()[0]
    print(f"Total faits stockés: {count}")
    
    if count > 0:
        cursor = conn.execute("SELECT user_id, fact_key, fact_value FROM user_facts ORDER BY id DESC LIMIT 5")
        for row in cursor:
            print(f"  ✅ {row[0]} | {row[1]} = {row[2]}")
    
    conn.close()

if __name__ == "__main__":
    asyncio.run(test())
