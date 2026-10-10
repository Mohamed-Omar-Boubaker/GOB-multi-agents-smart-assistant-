"""
Test extraction d'entités LLM
"""
import asyncio
import sys
import os

# Ajouter le chemin backend au PYTHONPATH
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from ai.llm_client import LLMClient
from config import Config

async def test_entity_extraction():
    print("=" * 60)
    print("TEST EXTRACTION ENTITES LLM")
    print("=" * 60)
    
    # Initialiser le client
    llm_client = LLMClient(
        api_url=Config.LLM_API_URL,
        api_key=Config.OPENROUTER_API_KEY,
        model=Config.LLM_MODEL,
        timeout=Config.LLM_TIMEOUT
    )
    
    # Test 1
    print("\nTest 1: 'Allume la lampe du salon'")
    print("-" * 60)
    result1 = await llm_client.analyze_intent(
        user_input="Allume la lampe du salon",
        language="fr"
    )
    print(f"Intent: {result1.get('primary_intent')}")
    print(f"Confidence: {result1.get('confidence')}")
    print(f"Entities: {result1.get('entities')}")
    
    # Test 2
    print("\n\nTest 2: 'Éteins la lumière de la cuisine'")
    print("-" * 60)
    result2 = await llm_client.analyze_intent(
        user_input="Éteins la lumière de la cuisine",
        language="fr"
    )
    print(f"Intent: {result2.get('primary_intent')}")
    print(f"Confidence: {result2.get('confidence')}")
    print(f"Entities: {result2.get('entities')}")
    
    # Test 3
    print("\n\nTest 3: 'Mets le thermostat à 22 degrés'")
    print("-" * 60)
    result3 = await llm_client.analyze_intent(
        user_input="Mets le thermostat à 22 degrés",
        language="fr"
    )
    print(f"Intent: {result3.get('primary_intent')}")
    print(f"Confidence: {result3.get('confidence')}")
    print(f"Entities: {result3.get('entities')}")
    
    print("\n" + "=" * 60)
    print("TESTS TERMINÉS")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_entity_extraction())
