"""
Test Memory Extractor - Démonstration extraction d'entités
Date: 13 Février 2026
Responsable: Montassar

Ce script teste le Memory Extractor avec différents scénarios.
"""

import asyncio
import sys
import os

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.services.memory_extractor import MemoryExtractor
from backend.ai.llm_client import LLMClient
from backend.services.memory_service import MemoryService
from backend.config import Config


# Scénarios de test
TEST_SCENARIOS = [
    {
        "user_message": "J'ai envie de pizza ce soir",
        "description": "Demande de nourriture"
    },
    {
        "user_message": "Allume la lampe du salon s'il te plaît",
        "description": "Contrôle d'appareil IoT"
    },
    {
        "user_message": "Est-ce qu'il y a un café près d'ici?",
        "description": "Demande d'information avec lieu"
    },
    {
        "user_message": "Merci beaucoup, c'est parfait!",
        "description": "Expression de satisfaction"
    },
    {
        "user_message": "Ça ne marche pas du tout, je suis énervé",
        "description": "Plainte avec émotion négative"
    },
    {
        "user_message": "Peux-tu m'aider avec la télé?",
        "description": "Demande d'aide sur un appareil"
    }
]


async def test_memory_extractor():
    """Test complet du Memory Extractor."""
    
    print("=" * 70)
    print("🧪 TEST MEMORY EXTRACTOR")
    print("=" * 70)
    print()
    
    # 1. Initialisation des composants
    print("📦 Initialisation des composants...")
    try:
        llm_client = LLMClient()
        memory_service = MemoryService(db_path="data/test_memory.db")
        memory_extractor = MemoryExtractor(
            llm_client=llm_client,
            memory_service=memory_service,
            enable_cache=True
        )
        print("✅ Composants initialisés avec succès\n")
    except Exception as e:
        print(f"❌ Erreur d'initialisation: {e}")
        return
    
    # 2. Tests des scénarios
    test_user_id = "test_user_001"
    
    for i, scenario in enumerate(TEST_SCENARIOS, 1):
        print("-" * 70)
        print(f"TEST {i}/{len(TEST_SCENARIOS)}: {scenario['description']}")
        print("-" * 70)
        print(f"💬 Message: \"{scenario['user_message']}\"")
        print()
        
        try:
            # Extraction
            result = await memory_extractor.extract_from_conversation(
                user_message=scenario['user_message'],
                user_id=test_user_id,
                store_results=True
            )
            
            # Affichage résultats
            print("📊 RÉSULTATS:")
            print(f"   🎯 Intent: {result.get('intent')}")
            print(f"   😊 Emotion: {result.get('emotion')}")
            print(f"   📝 Summary: {result.get('summary')}")
            
            entities = result.get('entities', [])
            if entities:
                print(f"   🔖 Entités ({len(entities)}):")
                for entity in entities:
                    print(f"      • {entity['type'].upper()}: \"{entity['name']}\" "
                          f"(confiance: {entity.get('confidence', 0.0):.0%})")
            else:
                print("   🔖 Entités: Aucune")
            
            print()
            
        except Exception as e:
            print(f"❌ Erreur pendant l'extraction: {e}\n")
    
    # 3. Récupération entités stockées
    print("-" * 70)
    print("📚 ENTITÉS STOCKÉES POUR L'UTILISATEUR")
    print("-" * 70)
    
    for entity_type in ["food", "device", "location"]:
        entities = memory_extractor.get_user_entities(test_user_id, entity_type=entity_type)
        if entities:
            print(f"\n🏷️  Type: {entity_type.upper()}")
            for entity in entities:
                print(f"   • {entity['name']} (confiance: {entity.get('confidence', 0.0):.0%})")
    
    print("\n" + "=" * 70)
    print("✅ TESTS TERMINÉS")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_memory_extractor())
