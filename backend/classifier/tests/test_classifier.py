"""
Tests unitaires - Intent Classifier
Responsable: Montassar
Date: 2026-02-10
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from backend.classifier.intent_classifier import IntentClassifier


@pytest.fixture
def classifier_rules():
    """Classifier avec méthode rules uniquement."""
    return IntentClassifier(method="rules", threshold=0.8)


@pytest.fixture
def classifier_hybrid():
    """Classifier avec méthode hybrid (sans LLM)."""
    return IntentClassifier(method="hybrid", llm_client=None, threshold=0.8)


@pytest.fixture
def classifier_with_llm():
    """Classifier avec LLM client mocké."""
    mock_llm = AsyncMock()
    return IntentClassifier(method="hybrid", llm_client=mock_llm, threshold=0.8)


@pytest.mark.asyncio
async def test_classification_conversation_greeting(classifier_rules):
    """Test classification conversation - salutation."""
    result = await classifier_rules.classify("Bonjour, comment vas-tu ?")
    
    assert result["classification"] == "conversation"
    assert result["confidence"] > 0.7
    assert result["method"] == "rules"
    assert "reasoning" in result


@pytest.mark.asyncio
async def test_classification_conversation_identity(classifier_rules):
    """Test classification conversation - question identité."""
    result = await classifier_rules.classify("Qui es-tu ?")
    
    assert result["classification"] == "conversation"
    assert result["confidence"] > 0.7
    assert result["method"] == "rules"


@pytest.mark.asyncio
async def test_classification_conversation_thanks(classifier_rules):
    """Test classification conversation - remerciement."""
    result = await classifier_rules.classify("Merci beaucoup !")
    
    assert result["classification"] == "conversation"
    assert result["confidence"] > 0.7


@pytest.mark.asyncio
async def test_classification_action_iot_light(classifier_rules):
    """Test classification action IoT - lumière."""
    result = await classifier_rules.classify("Allume la lampe du salon")
    
    assert result["classification"] == "action"
    assert result["confidence"] > 0.6
    assert result["method"] == "rules"
    assert result["reasoning"]["action_keywords"] > 0


@pytest.mark.asyncio
async def test_classification_action_iot_door(classifier_rules):
    """Test classification action IoT - porte."""
    result = await classifier_rules.classify("Ouvre la porte d'entrée")
    
    assert result["classification"] == "action"
    assert result["confidence"] > 0.6


@pytest.mark.asyncio
async def test_classification_action_email(classifier_rules):
    """Test classification action - email."""
    result = await classifier_rules.classify("Envoie un email à Alice")
    
    assert result["classification"] == "action"
    assert result["confidence"] > 0.6


@pytest.mark.asyncio
async def test_classification_action_search(classifier_rules):
    """Test classification action - recherche."""
    result = await classifier_rules.classify("Cherche la météo de demain")
    
    assert result["classification"] == "action"
    assert result["confidence"] > 0.6


@pytest.mark.asyncio
async def test_classification_empty_text(classifier_rules):
    """Test avec texte vide."""
    result = await classifier_rules.classify("")
    
    assert result["classification"] == "conversation"
    assert result["confidence"] == 0.0
    assert result["method"] == "empty_input"


@pytest.mark.asyncio
async def test_classification_whitespace_only(classifier_rules):
    """Test avec seulement espaces."""
    result = await classifier_rules.classify("   ")
    
    assert result["classification"] == "conversation"
    assert result["confidence"] == 0.0


@pytest.mark.asyncio
async def test_hybrid_with_action_verb(classifier_hybrid):
    """Test hybrid - détection verbe d'action."""
    result = await classifier_hybrid.classify("Je veux allumer la télévision")
    
    assert result["classification"] == "action"
    assert result["confidence"] > 0.7
    assert "action_verbs" in result["reasoning"]
    assert len(result["reasoning"]["action_verbs"]) > 0


@pytest.mark.asyncio
async def test_hybrid_multiple_action_verbs(classifier_hybrid):
    """Test hybrid - plusieurs verbes d'action."""
    result = await classifier_hybrid.classify("Allume la lumière et ouvre la fenêtre")
    
    assert result["classification"] == "action"
    assert result["confidence"] > 0.8


@pytest.mark.asyncio
async def test_confidence_levels_high(classifier_rules):
    """Test niveau de confiance élevé."""
    result = await classifier_rules.classify("Allume éteins contrôle active")
    
    assert result["classification"] == "action"
    assert result["confidence"] > 0.75


@pytest.mark.asyncio
async def test_confidence_levels_medium(classifier_rules):
    """Test niveau de confiance moyen."""
    result = await classifier_rules.classify("Allume quelque chose")
    
    assert result["classification"] == "action"
    assert 0.6 <= result["confidence"] <= 0.85


@pytest.mark.asyncio
async def test_ambiguous_text(classifier_rules):
    """Test texte ambigu sans mots-clés clairs."""
    result = await classifier_rules.classify("C'est bien")
    
    # Devrait classer comme conversation par défaut
    assert result["classification"] == "conversation"
    assert result["confidence"] < 0.8


@pytest.mark.asyncio
async def test_llm_fallback_triggered(classifier_with_llm):
    """Test que le fallback LLM est déclenché pour faible confiance."""
    # Mock LLM response
    classifier_with_llm.llm_client.generate_conversation_response = AsyncMock(
        return_value={"response": "action"}
    )
    classifier_with_llm.llm_client.clear_conversation = Mock()
    
    # Modifier threshold pour forcer fallback
    classifier_with_llm.threshold = 0.95
    
    result = await classifier_with_llm.classify("Fais quelque chose")
    
    # Vérifier que LLM a été appelé
    classifier_with_llm.llm_client.generate_conversation_response.assert_called_once()


@pytest.mark.asyncio
async def test_llm_classification_action(classifier_with_llm):
    """Test classification directe via LLM - action."""
    classifier_with_llm.method = "llm"
    
    # Mock LLM response
    classifier_with_llm.llm_client.generate_conversation_response = AsyncMock(
        return_value={"response": "action"}
    )
    classifier_with_llm.llm_client.clear_conversation = Mock()
    classifier_with_llm.llm_client.model = "test-model"
    
    result = await classifier_with_llm.classify("Allume la lampe")
    
    assert result["classification"] == "action"
    assert result["method"] == "llm"
    assert result["confidence"] == 0.90


@pytest.mark.asyncio
async def test_llm_classification_conversation(classifier_with_llm):
    """Test classification directe via LLM - conversation."""
    classifier_with_llm.method = "llm"
    
    # Mock LLM response
    classifier_with_llm.llm_client.generate_conversation_response = AsyncMock(
        return_value={"response": "conversation"}
    )
    classifier_with_llm.llm_client.clear_conversation = Mock()
    classifier_with_llm.llm_client.model = "test-model"
    
    result = await classifier_with_llm.classify("Bonjour")
    
    assert result["classification"] == "conversation"
    assert result["method"] == "llm"


@pytest.mark.asyncio
async def test_llm_error_handling(classifier_with_llm):
    """Test gestion erreur LLM - fallback sur règles."""
    classifier_with_llm.method = "hybrid"
    classifier_with_llm.threshold = 0.95
    
    # Mock LLM error
    classifier_with_llm.llm_client.generate_conversation_response = AsyncMock(
        side_effect=Exception("LLM API error")
    )
    
    result = await classifier_with_llm.classify("Allume la lumière")
    
    # Devrait avoir un résultat même avec erreur LLM
    assert result["classification"] in ["conversation", "action"]
    assert "llm_fallback_error" in result["reasoning"]


@pytest.mark.asyncio
async def test_pattern_matching_question(classifier_rules):
    """Test détection pattern question conversationnelle."""
    test_questions = [
        "Comment tu t'appelles ?",
        "Qui es-tu ?",
        "Pourquoi tu fais ça ?",
        "Quelle est ta fonction ?"
    ]
    
    for question in test_questions:
        result = await classifier_rules.classify(question)
        assert result["classification"] == "conversation"


@pytest.mark.asyncio
async def test_multiple_classifications_consistency(classifier_rules):
    """Test cohérence sur classifications multiples."""
    text = "Allume la lampe"
    
    results = []
    for _ in range(5):
        result = await classifier_rules.classify(text)
        results.append(result["classification"])
    
    # Toutes les classifications doivent être identiques
    assert len(set(results)) == 1
    assert results[0] == "action"


@pytest.mark.asyncio
async def test_case_insensitivity(classifier_rules):
    """Test insensibilité à la casse."""
    texts = [
        "ALLUME LA LAMPE",
        "allume la lampe",
        "Allume La Lampe",
        "AlLuMe lA lAmPe"
    ]
    
    results = []
    for text in texts:
        result = await classifier_rules.classify(text)
        results.append(result["classification"])
    
    # Tous doivent être classés pareil
    assert len(set(results)) == 1
    assert results[0] == "action"


@pytest.mark.asyncio
async def test_french_accents(classifier_rules):
    """Test gestion accents français."""
    result = await classifier_rules.classify("Éteins la lumière")
    
    assert result["classification"] == "action"


@pytest.mark.asyncio
async def test_reasoning_details(classifier_rules):
    """Test que reasoning contient détails utiles."""
    result = await classifier_rules.classify("Allume la lampe et merci")
    
    reasoning = result["reasoning"]
    assert "action_keywords" in reasoning
    assert "conversation_keywords" in reasoning
    assert "decision" in reasoning
    assert isinstance(reasoning["action_keywords"], int)
    assert isinstance(reasoning["conversation_keywords"], int)


def test_get_stats(classifier_rules):
    """Test méthode get_stats."""
    stats = classifier_rules.get_stats()
    
    assert "method" in stats
    assert "threshold" in stats
    assert "has_llm" in stats
    assert "conversation_keywords_count" in stats
    assert "action_keywords_count" in stats
    assert "action_verbs_count" in stats
    assert stats["method"] == "rules"
    assert stats["conversation_keywords_count"] > 0
    assert stats["action_keywords_count"] > 0


@pytest.mark.asyncio
async def test_request_id_generation(classifier_rules):
    """Test génération automatique request_id."""
    result = await classifier_rules.classify("Bonjour")
    
    assert "request_id" in result
    assert result["request_id"].startswith("clf_")


@pytest.mark.asyncio
async def test_timestamp_present(classifier_rules):
    """Test présence timestamp dans résultat."""
    result = await classifier_rules.classify("Bonjour")
    
    assert "timestamp" in result
    assert "T" in result["timestamp"]  # Format ISO


# ========== TESTS ANGLAIS ==========

@pytest.mark.asyncio
async def test_classification_conversation_english_greeting(classifier_rules):
    """Test classification conversation anglais - salutation."""
    result = await classifier_rules.classify("Hello, how are you?")
    
    assert result["classification"] == "conversation"
    assert result["confidence"] > 0.7


@pytest.mark.asyncio
async def test_classification_action_english_light(classifier_rules):
    """Test classification action anglais - lumière."""
    result = await classifier_rules.classify("Turn on the living room light")
    
    assert result["classification"] == "action"
    assert result["confidence"] > 0.6


@pytest.mark.asyncio
async def test_classification_action_english_email(classifier_rules):
    """Test classification action anglais - email."""
    result = await classifier_rules.classify("Send an email to Alice")
    
    assert result["classification"] == "action"
    assert result["confidence"] > 0.6


@pytest.mark.asyncio
async def test_classification_english_thanks(classifier_rules):
    """Test classification conversation anglais - remerciement."""
    result = await classifier_rules.classify("Thank you very much!")
    
    assert result["classification"] == "conversation"
    assert result["confidence"] > 0.7


@pytest.mark.asyncio
async def test_bilingual_mixed(classifier_rules):
    """Test texte mélangé français-anglais."""
    result = await classifier_rules.classify("Please allume la light")
    
    assert result["classification"] == "action"
    assert result["confidence"] > 0.6
