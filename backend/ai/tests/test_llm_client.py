"""
Tests unitaires - LLM Client
Responsable: Montassar
Date: 2026-02-10
"""

import pytest
import os
from unittest.mock import Mock, patch, AsyncMock
from backend.ai.llm_client import LLMClient


@pytest.fixture
def llm_client():
    """Fixture pour créer un LLMClient avec API key de test."""
    # Utiliser une fake API key pour tests
    return LLMClient(api_key="sk-test-fake-key-for-testing")


@pytest.fixture
def mock_llm_response():
    """Mock de réponse API OpenRouter."""
    return {
        "choices": [
            {
                "message": {
                    "content": "Bonjour ! Comment puis-je vous aider ?"
                }
            }
        ],
        "usage": {
            "total_tokens": 25
        }
    }


@pytest.fixture
def mock_intent_response():
    """Mock de réponse analyse d'intention."""
    return {
        "choices": [
            {
                "message": {
                    "content": '{"intent": "control_iot", "confidence": 0.95, "device": "light", "action": "turn_on", "location": "salon", "value": null}'
                }
            }
        ],
        "usage": {
            "total_tokens": 30
        }
    }


@pytest.mark.asyncio
async def test_conversation_mode(llm_client, mock_llm_response):
    """Test génération de réponse conversationnelle."""
    with patch.object(llm_client.client, 'post', new_callable=AsyncMock) as mock_post:
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = mock_llm_response
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        result = await llm_client.generate_conversation_response(
            user_input="Bonjour",
            user_id="user_001",
            language="fr"
        )
        
        # Vérifications
        assert result is not None
        assert isinstance(result, dict)
        assert "response" in result
        assert "model_used" in result
        assert "tokens_used" in result
        assert result["mode"] == "conversation"
        assert result["response"] == "Bonjour ! Comment puis-je vous aider ?"
        assert result["model_used"] == "mistralai/mistral-7b-instruct"
        assert result["tokens_used"] == 25


@pytest.mark.asyncio
async def test_conversation_memory(llm_client, mock_llm_response):
    """Test que la mémoire de conversation fonctionne."""
    with patch.object(llm_client.client, 'post', new_callable=AsyncMock) as mock_post:
        mock_response = Mock()
        mock_response.json.return_value = mock_llm_response
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        # Premier message
        await llm_client.generate_conversation_response(
            user_input="Je m'appelle Alice",
            user_id="user_001",
            language="fr"
        )
        
        # Deuxième message
        await llm_client.generate_conversation_response(
            user_input="Quel est mon nom ?",
            user_id="user_001",
            language="fr"
        )
        
        # Vérifier que l'historique contient les messages
        history = llm_client._get_conversation_history("user_001")
        assert len(history) > 2  # System + user1 + assistant1 + user2
        assert any("Alice" in msg.get("content", "") for msg in history)


@pytest.mark.asyncio
async def test_conversation_empty_input(llm_client):
    """Test avec input vide."""
    with pytest.raises(ValueError) as exc_info:
        await llm_client.generate_conversation_response(
            user_input="",
            user_id="user_001"
        )
    
    assert "user_input cannot be empty" in str(exc_info.value)


@pytest.mark.asyncio
async def test_conversation_whitespace_input(llm_client):
    """Test avec seulement espaces."""
    with pytest.raises(ValueError) as exc_info:
        await llm_client.generate_conversation_response(
            user_input="   ",
            user_id="user_001"
        )
    
    assert "user_input cannot be empty" in str(exc_info.value)


@pytest.mark.asyncio
async def test_intent_analysis_iot(llm_client, mock_intent_response):
    """Test analyse intent IoT."""
    with patch.object(llm_client.client, 'post', new_callable=AsyncMock) as mock_post:
        mock_response = Mock()
        mock_response.json.return_value = mock_intent_response
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        result = await llm_client.analyze_intent(
            user_input="Allume la lampe du salon",
            language="fr"
        )
        
        # Vérifications
        assert result is not None
        assert result["mode"] == "intent_analysis"
        assert result["primary_intent"] == "control_iot"
        assert result["confidence"] == 0.95
        assert result["entities"]["device"] == "light"
        assert result["entities"]["action"] == "turn_on"
        assert result["entities"]["location"] == "salon"


@pytest.mark.asyncio
async def test_intent_analysis_empty_input(llm_client):
    """Test analyse avec input vide."""
    with pytest.raises(ValueError) as exc_info:
        await llm_client.analyze_intent(user_input="", language="fr")
    
    assert "user_input cannot be empty" in str(exc_info.value)


@pytest.mark.asyncio
async def test_api_error_handling(llm_client):
    """Test gestion erreur API."""
    with patch.object(llm_client.client, 'post', new_callable=AsyncMock) as mock_post:
        # Simuler erreur HTTP
        import httpx
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_post.side_effect = httpx.HTTPStatusError(
            "Unauthorized", 
            request=Mock(), 
            response=mock_response
        )
        
        with pytest.raises(RuntimeError) as exc_info:
            await llm_client.generate_conversation_response(
                user_input="Test",
                user_id="user_001"
            )
        
        assert "LLM API error" in str(exc_info.value)
        assert "401" in str(exc_info.value)


@pytest.mark.asyncio
async def test_api_timeout(llm_client):
    """Test timeout API."""
    with patch.object(llm_client.client, 'post', new_callable=AsyncMock) as mock_post:
        import httpx
        mock_post.side_effect = httpx.TimeoutException("Timeout")
        
        with pytest.raises(RuntimeError) as exc_info:
            await llm_client.generate_conversation_response(
                user_input="Test",
                user_id="user_001"
            )
        
        assert "timeout" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_clear_conversation(llm_client, mock_llm_response):
    """Test effacement historique conversation."""
    with patch.object(llm_client.client, 'post', new_callable=AsyncMock) as mock_post:
        mock_response = Mock()
        mock_response.json.return_value = mock_llm_response
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        # Créer historique
        await llm_client.generate_conversation_response(
            user_input="Bonjour",
            user_id="user_001"
        )
        
        # Vérifier historique existe
        assert "user_001" in llm_client.conversations
        
        # Effacer
        llm_client.clear_conversation("user_001")
        
        # Vérifier effacé
        assert "user_001" not in llm_client.conversations


@pytest.mark.asyncio
async def test_multiple_users(llm_client, mock_llm_response):
    """Test gestion multi-utilisateurs."""
    with patch.object(llm_client.client, 'post', new_callable=AsyncMock) as mock_post:
        mock_response = Mock()
        mock_response.json.return_value = mock_llm_response
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        # User 1
        await llm_client.generate_conversation_response(
            user_input="Je suis Alice",
            user_id="user_001"
        )
        
        # User 2
        await llm_client.generate_conversation_response(
            user_input="Je suis Bob",
            user_id="user_002"
        )
        
        # Vérifier deux historiques distincts
        history1 = llm_client._get_conversation_history("user_001")
        history2 = llm_client._get_conversation_history("user_002")
        
        assert any("Alice" in msg.get("content", "") for msg in history1)
        assert any("Bob" in msg.get("content", "") for msg in history2)


def test_filter_memory_context_keeps_only_relevant_lines(llm_client):
    """Le contexte mémoire injecté ne doit garder que les lignes pertinentes."""
    memory_context = """# User Memory
- preference.topic: Newton theories and speed of light
- profile.city: Tunis
- preference.food: pizza"""

    filtered = llm_client._filter_memory_context_for_input(
        memory_context,
        "Tell me about pizza recipes"
    )

    assert "pizza" in filtered.lower()
    assert "newton" not in filtered.lower()
    assert "tunis" not in filtered.lower()


def test_topic_shift_detection_for_unrelated_inputs(llm_client):
    """Un changement net de sujet doit déclencher reset de l'historique transitoire."""
    llm_client.conversations["user_001"] = [
        {"role": "system", "content": "system"},
        {"role": "user", "content": "Tell me about Newton theories"},
        {"role": "assistant", "content": "Newton explained classical mechanics."}
    ]

    assert llm_client._should_reset_conversation_history(
        "user_001",
        "I want pizza ideas for dinner"
    ) is True


@pytest.mark.asyncio
async def test_intent_analysis_email_subject_fallback_from_user_text(llm_client):
    """Le subject est extrait depuis le texte si le LLM l'oublie."""
    llm_without_subject = {
        "choices": [
            {
                "message": {
                    "content": '{"intent":"send_email","confidence":0.91,"entities":{"recipient":"me"}}'
                }
            }
        ],
        "usage": {
            "total_tokens": 20
        }
    }

    with patch.object(llm_client.client, 'post', new_callable=AsyncMock) as mock_post:
        mock_response = Mock()
        mock_response.json.return_value = llm_without_subject
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        result = await llm_client.analyze_intent(
            user_input="Send email to me with subject football.",
            language="en"
        )

        assert result["primary_intent"] == "send_email"
        assert result["entities"]["recipient"] == "me"
        assert result["entities"]["subject"] == "football"


@pytest.mark.asyncio
async def test_intent_analysis_email_subject_fallback_after_subject_punctuation(llm_client):
    """Le subject est extrait même avec ponctuation après le mot-clé subject."""
    llm_without_subject = {
        "choices": [
            {
                "message": {
                    "content": '{"intent":"send_email","confidence":0.91,"entities":{"recipient":"me"}}'
                }
            }
        ],
        "usage": {
            "total_tokens": 20
        }
    }

    with patch.object(llm_client.client, 'post', new_callable=AsyncMock) as mock_post:
        mock_response = Mock()
        mock_response.json.return_value = llm_without_subject
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        result = await llm_client.analyze_intent(
            user_input="Send email to me with subject. Remember.",
            language="en"
        )

        assert result["primary_intent"] == "send_email"
        assert result["entities"]["recipient"] == "me"
        assert result["entities"]["subject"] == "Remember"


@pytest.mark.asyncio
async def test_intent_analysis_email_subject_inferred_without_keyword(llm_client):
    """Le subject est déduit même sans le mot-clé 'subject'."""
    llm_without_subject = {
        "choices": [
            {
                "message": {
                    "content": '{"intent":"send_email","confidence":0.91,"entities":{"recipient":"me"}}'
                }
            }
        ],
        "usage": {
            "total_tokens": 20
        }
    }

    with patch.object(llm_client.client, 'post', new_callable=AsyncMock) as mock_post:
        mock_response = Mock()
        mock_response.json.return_value = llm_without_subject
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        result = await llm_client.analyze_intent(
            user_input="Send email to me. Remember.",
            language="en"
        )

        assert result["primary_intent"] == "send_email"
        assert result["entities"]["recipient"] == "me"
        assert result["entities"]["subject"] == "Remember"


@pytest.mark.asyncio
async def test_conversation_history_limit(llm_client, mock_llm_response):
    """Test limite de l'historique de conversation."""
    with patch.object(llm_client.client, 'post', new_callable=AsyncMock) as mock_post:
        mock_response = Mock()
        mock_response.json.return_value = mock_llm_response
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        # Envoyer plus de messages que la limite
        for i in range(15):
            await llm_client.generate_conversation_response(
                user_input=f"Message {i}",
                user_id="user_001"
            )
        
        # Vérifier limite respectée (system + max_conversation_history)
        history = llm_client._get_conversation_history("user_001")
        assert len(history) <= llm_client.max_conversation_history + 1


def test_init_without_api_key():
    """Test initialisation sans API key."""
    # Vider variable d'environnement si existe
    old_key = os.environ.get("OPENROUTER_API_KEY")
    if "OPENROUTER_API_KEY" in os.environ:
        del os.environ["OPENROUTER_API_KEY"]
    
    try:
        with pytest.raises(ValueError) as exc_info:
            LLMClient()
        
        assert "API key required" in str(exc_info.value)
    finally:
        # Restaurer
        if old_key:
            os.environ["OPENROUTER_API_KEY"] = old_key


def test_init_with_env_variable():
    """Test initialisation avec variable d'environnement."""
    old_key = os.environ.get("OPENROUTER_API_KEY")
    os.environ["OPENROUTER_API_KEY"] = "sk-test-env-key"
    
    try:
        client = LLMClient()
        assert client.api_key == "sk-test-env-key"
    finally:
        if old_key:
            os.environ["OPENROUTER_API_KEY"] = old_key
        else:
            del os.environ["OPENROUTER_API_KEY"]


@pytest.mark.asyncio
async def test_health_check_success(llm_client):
    """Test health check quand API accessible."""
    with patch.object(llm_client.client, 'get', new_callable=AsyncMock) as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        result = await llm_client.health_check()
        assert result is True


@pytest.mark.asyncio
async def test_health_check_failure(llm_client):
    """Test health check quand API inaccessible."""
    with patch.object(llm_client.client, 'get', new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = Exception("Connection error")
        
        result = await llm_client.health_check()
        assert result is False
