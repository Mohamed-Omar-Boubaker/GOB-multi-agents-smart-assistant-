"""
Test de nettoyage d'emojis dans le TTS
Vérifie que les emojis sont bien supprimés avant synthèse vocale
"""

import sys
import os

# Ajouter le chemin parent pour importer depuis backend
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.ai.tts_engine import TTSEngine


def test_emoji_cleaning():
    """Test de la fonction _clean_text_for_tts"""
    
    print("=" * 70)
    print("TEST: Nettoyage des emojis dans le TTS")
    print("=" * 70)
    print()
    
    # Créer une instance TTS
    tts = TTSEngine()
    
    # Cas de test avec différents types d'emojis
    test_cases = [
        {
            "input": "Bonjour ! 😊 Comment vas-tu ?",
            "expected": "Bonjour ! Comment vas-tu ?"
        },
        {
            "input": "C'est super ! 🎉🎊🎈",
            "expected": "C'est super !"
        },
        {
            "input": "Je suis content 😄👍",
            "expected": "Je suis content"
        },
        {
            "input": "Météo: ☀️🌤️⛅🌦️🌧️",
            "expected": "Météo:"
        },
        {
            "input": "🔥🔥🔥 Incroyable ! 🚀",
            "expected": "Incroyable !"
        },
        {
            "input": "Hello world! 🌍 Let's go 🚗",
            "expected": "Hello world! Let's go"
        },
        {
            "input": "مرحبا 👋 كيف حالك ؟ 😊",
            "expected": "مرحبا كيف حالك ؟"
        },
        {
            "input": "😊😊😊",  # Que des emojis
            "expected": ""
        },
        {
            "input": "Texte normal sans emoji",
            "expected": "Texte normal sans emoji"
        }
    ]
    
    # Exécuter les tests
    passed = 0
    failed = 0
    
    for i, test in enumerate(test_cases, 1):
        input_text = test["input"]
        expected = test["expected"]
        
        print(f"Test {i}:")
        print(f"  Input:    '{input_text}'")
        
        # Appeler la fonction de nettoyage
        result = tts._clean_text_for_tts(input_text)
        
        print(f"  Output:   '{result}'")
        print(f"  Expected: '{expected}'")
        
        # Vérifier le résultat
        if result == expected:
            print("  ✅ PASS")
            passed += 1
        else:
            print("  ❌ FAIL")
            failed += 1
        
        print()
    
    # Résumé
    print("=" * 70)
    print(f"RÉSULTAT: {passed} tests réussis, {failed} tests échoués")
    print("=" * 70)
    
    if failed == 0:
        print("✅ Tous les tests sont passés!")
        return True
    else:
        print("❌ Certains tests ont échoué")
        return False


if __name__ == "__main__":
    success = test_emoji_cleaning()
    sys.exit(0 if success else 1)
