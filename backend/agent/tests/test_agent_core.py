"""
Tests unitaires - Agent Core
Responsable: Montassar
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, Mock, patch
from backend.agent.agent_core import AgentCore


# ==================== Fixtures ====================

@pytest.fixture
def mock_stt_engine():
    """Mock STT Engine."""
    stt = AsyncMock()
    stt.transcribe = AsyncMock(return_value={
        "transcription": "Bonjour comment allez-vous",
        "confidence": 0.92
    })
    return stt


@pytest.fixture
def mock_tts_engine():
    """Mock TTS Engine."""
    tts = AsyncMock()
    tts.synthesize = AsyncMock(return_value={
        "audio_data": "BASE64_AUDIO_DATA",
        "audio_format": "wav"
    })
    return tts


@pytest.fixture
def mock_llm_client():
    """Mock LLM Client."""
    llm = AsyncMock()
    llm.generate_conversation_response = AsyncMock(return_value={
        "response": "Bonjour ! Je vais très bien, merci de demander.",
        "model_used": "mistral-7b"
    })
    llm.analyze_intent = AsyncMock(return_value={
        "intent": "control_iot",
        "entities": {
            "devices": [{
                "type": "light",
                "location": "salon",
                "action": "turn_on"
            }]
        },
        "confidence": 0.95
    })
    return llm


@pytest.fixture
def mock_classifier():
    """Mock Intent Classifier."""
    classifier = AsyncMock()
    classifier.classify = AsyncMock(return_value={
        "classification": "conversation",
        "confidence": 0.89,
        "method": "hybrid"
    })
    return classifier


@pytest.fixture
def mock_action_builder():
    """Mock Action Builder."""
    builder = AsyncMock()
    builder.build_action = AsyncMock(return_value={
        "action_id": "act_test123",
        "user_id": "user_test",
        "intent": "control_iot",
        "confirmed": False,
        "state": "DRAFT",
        "payload": {
            "device_id": "lamp_salon_001",
            "device_type": "light",
            "action": "turn_on",
            "location": "salon"
        },
        "timestamps": {
            "created_at": "2026-02-10T10:00:00Z"
        }
    })
    return builder


@pytest.fixture
def mock_confirmation_handler():
    """Mock Confirmation Handler."""
    handler = AsyncMock()
    handler.generate_confirmation = AsyncMock(
        return_value="Voulez-vous vraiment allumer la lampe du salon ?"
    )
    handler.parse_response = Mock(return_value={"parsed_response": {"intent": "confirm"}})
    return handler


@pytest.fixture
def mock_n8n_client():
    """Mock n8n Client."""
    n8n = AsyncMock()
    n8n.send_action = AsyncMock(return_value={
        "status": "success",
        "workflow_id": "wf_123"
    })
    return n8n


@pytest.fixture
def agent_core_conversation(mock_stt_engine, mock_tts_engine, mock_llm_client, mock_classifier):
    """Agent Core configuré pour tests Conversation."""
    return AgentCore(
        stt_engine=mock_stt_engine,
        tts_engine=mock_tts_engine,
        llm_client=mock_llm_client,
        classifier=mock_classifier
    )


@pytest.fixture
def agent_core_action(
    mock_stt_engine, mock_tts_engine, mock_llm_client, mock_classifier,
    mock_action_builder, mock_confirmation_handler, mock_n8n_client
):
    """Agent Core configuré pour tests Action."""
    return AgentCore(
        stt_engine=mock_stt_engine,
        tts_engine=mock_tts_engine,
        llm_client=mock_llm_client,
        classifier=mock_classifier,
        action_builder=mock_action_builder,
        confirmation_handler=mock_confirmation_handler,
        n8n_client=mock_n8n_client
    )


# ==================== Tests Pipeline Conversation ====================

@pytest.mark.asyncio
async def test_process_text_conversation(agent_core_conversation, mock_classifier, mock_llm_client, mock_tts_engine):
    """Test traitement commande texte conversation."""
    # Configurer classifier pour retourner "conversation"
    mock_classifier.classify = AsyncMock(return_value={
        "classification": "conversation",
        "confidence": 0.89,
        "method": "hybrid"
    })
    
    input_data = {
        "command_type": "text",
        "user_id": "user_test",
        "text": "Bonjour, comment allez-vous ?",
        "language": "fr"
    }
    
    result = await agent_core_conversation.process(input_data)
    
    # Vérifications
    assert result["classification"] == "conversation"
    assert result["user_id"] == "user_test"
    assert "request_id" in result
    assert "response" in result
    assert result["response"] == "Bonjour ! Je vais très bien, merci de demander."
    assert "processing_time_ms" in result
    
    # Vérifier appels
    mock_classifier.classify.assert_called_once()
    mock_llm_client.generate_conversation_response.assert_called_once()
    mock_tts_engine.synthesize.assert_called_once()
    
    print(f"✅ Test conversation passed: {result['response']}")


@pytest.mark.asyncio
async def test_process_audio_conversation(agent_core_conversation, mock_stt_engine, mock_classifier):
    """Test traitement commande audio conversation."""
    # Configurer classifier pour conversation
    mock_classifier.classify = AsyncMock(return_value={
        "classification": "conversation",
        "confidence": 0.85
    })
    
    input_data = {
        "command_type": "audio",
        "user_id": "user_test",
        "audio_data": "BASE64_AUDIO_INPUT",
        "audio_format": "wav",
        "language": "fr"
    }
    
    result = await agent_core_conversation.process(input_data)
    
    # Vérifications
    assert result["classification"] == "conversation"
    assert "transcription" in result
    assert result["transcription"] == "Bonjour comment allez-vous"
    assert "response" in result
    
    # Vérifier STT appelé
    mock_stt_engine.transcribe.assert_called_once()
    
    print(f"✅ Test audio conversation passed: transcription={result['transcription']}")


@pytest.mark.asyncio
async def test_conversation_without_llm():
    """Test conversation sans LLM (fallback)."""
    agent = AgentCore(
        llm_client=None,  # Pas de LLM
        classifier=None    # Pas de classifier
    )
    
    input_data = {
        "command_type": "text",
        "user_id": "user_test",
        "text": "Salut",
        "language": "fr"
    }
    
    result = await agent.process(input_data)
    
    # Devrait utiliser fallback
    assert "response" in result
    assert "développement" in result["response"].lower()
    
    print(f"✅ Test fallback passed: {result['response']}")


@pytest.mark.asyncio
async def test_conversation_save_name_deterministic():
    """Le nom doit être sauvegardé de manière déterministe sans dépendre du LLM."""
    memory_service = Mock()
    memory_service.build_memory_context = Mock(return_value="")
    memory_service.add_fact = Mock(return_value=True)
    memory_service.get_fact = Mock(return_value=None)
    memory_service.add_conversation_turn = Mock(return_value=True)

    agent = AgentCore(
        llm_client=None,
        tts_engine=None,
        memory_service=memory_service,
    )

    result = await agent._handle_conversation(
        text="My name is Montasar. Save it.",
        user_id="user_test",
        language="en",
        request_id="req_name_save",
    )

    assert result["status"] == "completed"
    assert "montasar" in result["response"].lower()
    assert memory_service.add_fact.call_count >= 1


@pytest.mark.asyncio
async def test_conversation_recall_name_deterministic():
    """La question 'What is my name?' doit répondre depuis la mémoire structurée."""
    memory_service = Mock()
    memory_service.build_memory_context = Mock(return_value="")
    memory_service.add_fact = Mock(return_value=True)
    memory_service.add_conversation_turn = Mock(return_value=True)

    def get_fact_side_effect(user_id, fact_type, fact_key):
        if fact_type == "name" and fact_key == "preferred_name":
            return "Montasar"
        return None

    memory_service.get_fact = Mock(side_effect=get_fact_side_effect)

    agent = AgentCore(
        llm_client=None,
        tts_engine=None,
        memory_service=memory_service,
    )

    result = await agent._handle_conversation(
        text="What is my name?",
        user_id="user_test",
        language="en",
        request_id="req_name_query",
    )

    assert result["status"] == "completed"
    assert result["response"] == "Your name is Montasar."


# ==================== Tests Pipeline Action ====================

@pytest.mark.asyncio
async def test_process_text_action(agent_core_action, mock_classifier, mock_action_builder, mock_confirmation_handler):
    """Test traitement commande texte action."""
    # Configurer classifier pour retourner "action"
    mock_classifier.classify = AsyncMock(return_value={
        "classification": "action",
        "confidence": 0.92,
        "intent": "control_iot"
    })
    
    input_data = {
        "command_type": "text",
        "user_id": "user_test",
        "text": "Allume la lampe du salon",
        "language": "fr"
    }
    
    result = await agent_core_action.process(input_data)
    
    # Vérifications
    assert result["classification"] == "action"
    assert result["type"] == "action"
    assert "action_id" in result
    assert result["status"] == "awaiting_confirmation"
    assert result["state"] == "PENDING_CONFIRMATION"
    assert "message" in result
    assert "lampe" in result["message"].lower()
    
    # Vérifier appels
    mock_action_builder.build_action.assert_called_once()
    mock_confirmation_handler.generate_confirmation.assert_called_once()
    
    print(f"✅ Test action passed: action_id={result['action_id']}, message={result['message']}")


@pytest.mark.asyncio
async def test_process_audio_action(agent_core_action, mock_stt_engine, mock_classifier):
    """Test traitement commande audio action."""
    # Configurer STT et classifier
    mock_stt_engine.transcribe = AsyncMock(return_value={
        "transcription": "Allume la lampe du salon"
    })
    
    mock_classifier.classify = AsyncMock(return_value={
        "classification": "action",
        "confidence": 0.94
    })
    
    input_data = {
        "command_type": "audio",
        "user_id": "user_test",
        "audio_data": "BASE64_AUDIO_ACTION",
        "audio_format": "wav",
        "language": "fr"
    }
    
    result = await agent_core_action.process(input_data)
    
    # Vérifications
    assert result["classification"] == "action"
    assert "transcription" in result
    assert result["transcription"] == "Allume la lampe du salon"
    assert result["status"] == "awaiting_confirmation"
    
    print(f"✅ Test audio action passed: transcription={result['transcription']}")


@pytest.mark.asyncio
async def test_action_low_confidence(agent_core_action, mock_classifier, mock_llm_client):
    """Test action avec confiance basse → rejet."""
    # Configurer classifier pour retourner "action"
    mock_classifier.classify = AsyncMock(return_value={
        "classification": "action",
        "confidence": 0.85,
        "intent": "control_iot"
    })
    
    # Configurer LLM pour retourner faible confiance
    mock_llm_client.analyze_intent = AsyncMock(return_value={
        "intent": "unknown",
        "confidence": 0.3,  # Sous le seuil de 0.7
        "entities": {}
    })
    
    input_data = {
        "command_type": "text",
        "user_id": "user_test",
        "text": "Fais quelque chose",
        "language": "fr"
    }
    
    result = await agent_core_action.process(input_data)
    
    # Vérifications
    assert result["status"] == "low_confidence"
    assert "reformuler" in result["response"].lower() or "compris" in result["response"].lower()
    
    print(f"✅ Test low confidence passed: {result['response']}")


# ==================== Tests Confirmation Action ====================

@pytest.mark.asyncio
async def test_confirm_action_accept(agent_core_action, mock_confirmation_handler, mock_n8n_client):
    """Test confirmation action avec acceptation."""
    # Configurer parse_response pour retourner "confirm"
    mock_confirmation_handler.parse_response = Mock(return_value={"parsed_response": {"intent": "confirm"}})
    
    # Créer action d'abord
    action_id = "act_test_confirm"
    agent_core_action.state_manager.create_action(
        action_id=action_id,
        action_json={
            "action_id": action_id,
            "user_id": "user_test",
            "intent": "control_iot"
        },
        initial_state="PENDING_CONFIRMATION"
    )
    
    # Confirmer
    result = await agent_core_action.confirm_action(action_id, "oui")
    
    # Vérifications
    assert result["status"] == "executing"
    assert result["action_id"] == action_id
    assert result["state"] == "EXECUTING"
    
    # Vérifier n8n appelé
    mock_n8n_client.send_action.assert_called_once()
    
    # Vérifier état dans StateManager
    action_state = agent_core_action.state_manager.get_action(action_id)
    assert action_state["current_state"] == "EXECUTING"
    
    print(f"✅ Test confirm accept passed: state={result['state']}")


@pytest.mark.asyncio
async def test_confirm_action_accept_english_response(agent_core_action):
    """La réponse d'exécution doit respecter la langue de l'action (EN)."""
    action_id = "act_test_confirm_en"
    agent_core_action.state_manager.create_action(
        action_id=action_id,
        action_json={
            "action_id": action_id,
            "user_id": "user_test",
            "intent": "send_email",
            "language": "en",
            "context": {"language": "en"}
        },
        initial_state="PENDING_CONFIRMATION"
    )

    result = await agent_core_action.confirm_action(action_id, "yes")

    assert result["status"] == "executing"
    assert result["response"] == "Action is being executed..."


@pytest.mark.asyncio
async def test_confirm_action_cancel(agent_core_action, mock_confirmation_handler):
    """Test confirmation action avec annulation."""
    # Configurer parse_response pour retourner "cancel"
    mock_confirmation_handler.parse_response = Mock(return_value={"parsed_response": {"intent": "cancel"}})
    
    # Créer action
    action_id = "act_test_cancel"
    agent_core_action.state_manager.create_action(
        action_id=action_id,
        action_json={"action_id": action_id, "user_id": "user_test"},
        initial_state="PENDING_CONFIRMATION"
    )
    
    # Annuler
    result = await agent_core_action.confirm_action(action_id, "non")
    
    # Vérifications
    assert result["status"] == "canceled"
    assert result["action_id"] == action_id
    assert "annulée" in result["response"].lower()
    
    # Vérifier état CANCELED
    action_state = agent_core_action.state_manager.get_action(action_id)
    assert action_state["current_state"] == "CANCELED"
    
    print(f"✅ Test confirm cancel passed")


@pytest.mark.asyncio
async def test_confirm_action_correction(agent_core_action, mock_confirmation_handler):
    """Test confirmation action avec demande correction."""
    # Configurer parse_response pour retourner "correction"
    mock_confirmation_handler.parse_response = Mock(return_value={"parsed_response": {"intent": "correction"}})
    
    # Créer action
    action_id = "act_test_correction"
    agent_core_action.state_manager.create_action(
        action_id=action_id,
        action_json={"action_id": action_id, "user_id": "user_test"},
        initial_state="PENDING_CONFIRMATION"
    )
    
    # Demander correction
    result = await agent_core_action.confirm_action(action_id, "modifier")
    
    # Vérifications
    assert result["status"] == "correction_needed"
    assert result["action_id"] == action_id
    assert "correction" in result["response"].lower()
    
    # Vérifier retour à DRAFT
    action_state = agent_core_action.state_manager.get_action(action_id)
    assert action_state["current_state"] == "DRAFT"
    
    print(f"✅ Test confirm correction passed")


# ==================== Tests Gestion Erreurs ====================

@pytest.mark.asyncio
async def test_missing_command_type():
    """Test erreur si command_type manquant."""
    agent = AgentCore()
    
    input_data = {
        "user_id": "user_test",
        "text": "Bonjour"
        # Manque command_type
    }
    
    result = await agent.process(input_data)
    
    assert result["status"] == "error"
    assert "command_type" in result["error"]
    
    print(f"✅ Test missing command_type passed")


@pytest.mark.asyncio
async def test_missing_user_id():
    """Test erreur si user_id manquant."""
    agent = AgentCore()
    
    input_data = {
        "command_type": "text",
        "text": "Bonjour"
        # Manque user_id
    }
    
    result = await agent.process(input_data)
    
    assert result["status"] == "error"
    assert "user_id" in result["error"]
    
    print(f"✅ Test missing user_id passed")


@pytest.mark.asyncio
async def test_stt_not_configured():
    """Test erreur si STT manquant pour audio."""
    agent = AgentCore(stt_engine=None)  # Pas de STT
    
    input_data = {
        "command_type": "audio",
        "user_id": "user_test",
        "audio_data": "BASE64",
        "language": "fr"
    }
    
    result = await agent.process(input_data)
    
    assert result["status"] == "error"
    assert "STT" in result["error"]
    
    print(f"✅ Test STT not configured passed")


@pytest.mark.asyncio
async def test_empty_audio_transcription(mock_stt_engine):
    """Test gestion transcription vide."""
    # Configurer STT pour retourner texte vide
    mock_stt_engine.transcribe = AsyncMock(return_value={
        "transcription": ""
    })
    
    agent = AgentCore(stt_engine=mock_stt_engine)
    
    input_data = {
        "command_type": "audio",
        "user_id": "user_test",
        "audio_data": "BASE64_SILENCE",
        "audio_format": "wav",
        "language": "fr"
    }
    
    result = await agent.process(input_data)
    
    assert result["status"] == "error"
    assert result["error"] == "empty_transcription"
    assert "répéter" in result["response"].lower()
    
    print(f"✅ Test empty transcription passed")


# ==================== Tests Utilitaires ====================

def test_get_action_status(agent_core_action):
    """Test récupération statut action."""
    # Créer action
    action_id = "act_test_status"
    agent_core_action.state_manager.create_action(
        action_id=action_id,
        action_json={"action_id": action_id, "user_id": "user_test"},
        initial_state="DRAFT"
    )
    
    # Récupérer statut
    result = agent_core_action.get_action_status(action_id)
    
    assert result["status"] == "found"
    assert "action" in result
    assert result["action"]["action_id"] == action_id
    
    print(f"✅ Test get_action_status passed")


def test_get_action_status_not_found(agent_core_action):
    """Test récupération action inexistante."""
    result = agent_core_action.get_action_status("act_nonexistent")
    
    assert result["status"] == "not_found"
    assert "error" in result
    
    print(f"✅ Test get_action_status not found passed")


@pytest.mark.asyncio
async def test_handle_execution_result_success(agent_core_action):
    """Test gestion résultat exécution réussi."""
    # Créer action en EXECUTING
    action_id = "act_test_exec"
    agent_core_action.state_manager.create_action(
        action_id=action_id,
        action_json={"action_id": action_id},
        initial_state="EXECUTING"
    )
    
    # Simuler résultat success
    result_data = {
        "action_id": action_id,
        "status": "success",
        "result": {"device_state": "on"}
    }
    
    result = await agent_core_action.handle_execution_result(result_data)
    
    assert result["status"] == "completed"
    assert result["action_id"] == action_id
    
    # Vérifier état COMPLETED
    action_state = agent_core_action.state_manager.get_action(action_id)
    assert action_state["current_state"] == "COMPLETED"
    
    print(f"✅ Test handle_execution_result success passed")


@pytest.mark.asyncio
async def test_handle_execution_result_failed(agent_core_action):
    """Test gestion résultat exécution échoué."""
    # Créer action en EXECUTING
    action_id = "act_test_fail"
    agent_core_action.state_manager.create_action(
        action_id=action_id,
        action_json={"action_id": action_id},
        initial_state="EXECUTING"
    )
    
    # Simuler résultat failed
    result_data = {
        "action_id": action_id,
        "status": "failed",
        "error": "Device not responding"
    }
    
    result = await agent_core_action.handle_execution_result(result_data)
    
    assert result["status"] == "failed"
    assert result["action_id"] == action_id
    assert "error" in result
    
    # Vérifier état FAILED
    action_state = agent_core_action.state_manager.get_action(action_id)
    assert action_state["current_state"] == "FAILED"
    
    print(f"✅ Test handle_execution_result failed passed")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
