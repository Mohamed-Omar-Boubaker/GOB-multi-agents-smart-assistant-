import pytest
from unittest.mock import AsyncMock

from backend.agent.agent_core import AgentCore


@pytest.mark.asyncio
async def test_pending_confirmation_maps_yes_to_confirm_token():
    agent = AgentCore(tts_engine=AsyncMock())
    agent.confirm_action = AsyncMock(return_value={"status": "executing", "action_id": "act_1"})

    result = await agent._handle_pending_confirmation(
        text="yes",
        user_id="user_test",
        language="en",
        pending_action={"action_id": "act_1"},
        request_id="req_1",
    )

    assert result["status"] == "executing"
    agent.confirm_action.assert_awaited_once_with("act_1", "confirm")


@pytest.mark.asyncio
async def test_pending_confirmation_reprompts_when_transcription_failed():
    tts = AsyncMock()
    tts.synthesize = AsyncMock(return_value={"audio_data": "BASE64", "audio_format": "wav"})

    agent = AgentCore(tts_engine=tts)
    agent.confirm_action = AsyncMock()

    result = await agent._handle_pending_confirmation(
        text="Could not transcribe",
        user_id="user_test",
        language="en",
        pending_action={"action_id": "act_1"},
        request_id="req_1",
    )

    assert result["status"] == "awaiting_confirmation"
    assert "yes" in result["response"].lower()
    agent.confirm_action.assert_not_awaited()
