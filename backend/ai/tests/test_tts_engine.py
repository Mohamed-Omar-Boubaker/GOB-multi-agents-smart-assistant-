"""
Tests unitaires - TTS Engine
Responsable: Omar
Date: 2026-02-10
"""

import pytest
import asyncio
import base64
import wave
import io
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from backend.ai.tts_engine import TTSEngine
from wyoming.audio import AudioChunk, AudioStop
from wyoming.event import Event


@pytest.fixture
def tts_engine():
    """Fixture pour créer une instance de TTSEngine."""
    return TTSEngine(host="127.0.0.1", port=5002)


@pytest.fixture
def mock_audio_data():
    """Génère des données audio WAV valides pour tests."""
    # Créer un WAV minimal en mémoire
    buffer = io.BytesIO()
    with wave.open(buffer, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(21470)
        # Quelques frames de silence
        wf.writeframes(b'\x00' * 1000)
    
    return buffer.getvalue()


@pytest.mark.asyncio
async def test_synthesize_text_french(tts_engine):
    """Test synthèse texte français."""
    with patch('asyncio.open_connection') as mock_connect:
        # Mock reader/writer
        mock_reader = AsyncMock()
        mock_writer = AsyncMock()
        mock_connect.return_value = (mock_reader, mock_writer)
        
        # Mock audio chunks
        audio_data = b'\x00' * 1000  # Données audio simulées
        
        # Mock événements
        chunk_event = Mock()
        chunk_event.type = "audio-chunk"
        AudioChunk.is_type = lambda t: t == "audio-chunk"
        
        stop_event = Mock()
        stop_event.type = "audio-stop"
        AudioStop.is_type = lambda t: t == "audio-stop"
        
        # Mock chunk
        mock_chunk = Mock()
        mock_chunk.audio = audio_data
        AudioChunk.from_event = lambda e: mock_chunk
        
        # Séquence d'événements : chunk puis stop
        mock_reader.read = AsyncMock(side_effect=[chunk_event, stop_event])
        
        # Mock async_read_event pour retourner chunk puis stop
        async def mock_read_event(reader):
            if not hasattr(mock_read_event, 'call_count'):
                mock_read_event.call_count = 0
            mock_read_event.call_count += 1
            
            if mock_read_event.call_count == 1:
                return chunk_event
            elif mock_read_event.call_count == 2:
                return stop_event
            return None
        
        with patch('backend.ai.tts_engine.async_read_event', side_effect=mock_read_event):
            with patch('backend.ai.tts_engine.async_write_event', new_callable=AsyncMock):
                result = await tts_engine.synthesize("Bonjour", "fr")
        
        # Vérifications
        assert result is not None
        assert isinstance(result, dict)
        assert "audio_data" in result
        assert "audio_format" in result
        assert result["audio_format"] == "wav"
        assert "processing_time_ms" in result
        assert "audio_metadata" in result
        assert result["audio_metadata"]["sample_rate"] == 21470
        assert "timestamp" in result


@pytest.mark.asyncio
async def test_synthesize_text_long(tts_engine):
    """Test synthèse texte long."""
    long_text = "Ceci est un texte très long. " * 20
    
    with patch('asyncio.open_connection') as mock_connect:
        mock_reader = AsyncMock()
        mock_writer = AsyncMock()
        mock_connect.return_value = (mock_reader, mock_writer)
        
        # Mock audio chunks multiples
        audio_data_1 = b'\x00' * 500
        audio_data_2 = b'\x00' * 500
        
        chunk_event_1 = Mock()
        chunk_event_1.type = "audio-chunk"
        chunk_event_2 = Mock()
        chunk_event_2.type = "audio-chunk"
        stop_event = Mock()
        stop_event.type = "audio-stop"
        
        AudioChunk.is_type = lambda t: t == "audio-chunk"
        AudioStop.is_type = lambda t: t == "audio-stop"
        
        mock_chunk_1 = Mock(audio=audio_data_1)
        mock_chunk_2 = Mock(audio=audio_data_2)
        
        def from_event_side_effect(e):
            if e == chunk_event_1:
                return mock_chunk_1
            elif e == chunk_event_2:
                return mock_chunk_2
        
        AudioChunk.from_event = from_event_side_effect
        
        async def mock_read_event(reader):
            if not hasattr(mock_read_event, 'call_count'):
                mock_read_event.call_count = 0
            mock_read_event.call_count += 1
            
            if mock_read_event.call_count == 1:
                return chunk_event_1
            elif mock_read_event.call_count == 2:
                return chunk_event_2
            elif mock_read_event.call_count == 3:
                return stop_event
            return None
        
        with patch('backend.ai.tts_engine.async_read_event', side_effect=mock_read_event):
            with patch('backend.ai.tts_engine.async_write_event', new_callable=AsyncMock):
                result = await tts_engine.synthesize(long_text, "fr")
        
        assert result is not None
        assert result["text_length"] == len(long_text)


@pytest.mark.asyncio
async def test_synthesize_empty_text(tts_engine):
    """Test avec texte vide - doit lever ValueError."""
    with pytest.raises(ValueError) as exc_info:
        await tts_engine.synthesize("", "fr")
    
    assert "text cannot be empty" in str(exc_info.value)


@pytest.mark.asyncio
async def test_synthesize_whitespace_only(tts_engine):
    """Test avec seulement espaces - doit lever ValueError."""
    with pytest.raises(ValueError) as exc_info:
        await tts_engine.synthesize("   ", "fr")
    
    assert "text cannot be empty" in str(exc_info.value)


@pytest.mark.asyncio
async def test_synthesize_connection_refused(tts_engine):
    """Test erreur de connexion au serveur."""
    with patch('asyncio.open_connection', side_effect=ConnectionRefusedError("Connection refused")):
        with pytest.raises(RuntimeError) as exc_info:
            await tts_engine.synthesize("Test", "fr")
        
        assert "Cannot connect to TTS server" in str(exc_info.value)
        assert "Is Piper running?" in str(exc_info.value)


@pytest.mark.asyncio
async def test_synthesize_no_audio_data(tts_engine):
    """Test quand serveur ne retourne pas d'audio."""
    with patch('asyncio.open_connection') as mock_connect:
        mock_reader = AsyncMock()
        mock_writer = AsyncMock()
        mock_connect.return_value = (mock_reader, mock_writer)
        
        stop_event = Mock()
        stop_event.type = "audio-stop"
        AudioStop.is_type = lambda t: t == "audio-stop"
        
        async def mock_read_event(reader):
            return stop_event
        
        with patch('backend.ai.tts_engine.async_read_event', side_effect=mock_read_event):
            with patch('backend.ai.tts_engine.async_write_event', new_callable=AsyncMock):
                with pytest.raises(RuntimeError) as exc_info:
                    await tts_engine.synthesize("Test", "fr")
                
                assert "No audio data received" in str(exc_info.value)


@pytest.mark.asyncio
async def test_synthesize_request_id(tts_engine):
    """Test avec request_id personnalisé."""
    with patch('asyncio.open_connection') as mock_connect:
        mock_reader = AsyncMock()
        mock_writer = AsyncMock()
        mock_connect.return_value = (mock_reader, mock_writer)
        
        audio_data = b'\x00' * 1000
        chunk_event = Mock(type="audio-chunk")
        stop_event = Mock(type="audio-stop")
        
        AudioChunk.is_type = lambda t: t == "audio-chunk"
        AudioStop.is_type = lambda t: t == "audio-stop"
        AudioChunk.from_event = lambda e: Mock(audio=audio_data)
        
        async def mock_read_event(reader):
            if not hasattr(mock_read_event, 'call_count'):
                mock_read_event.call_count = 0
            mock_read_event.call_count += 1
            return chunk_event if mock_read_event.call_count == 1 else stop_event
        
        with patch('backend.ai.tts_engine.async_read_event', side_effect=mock_read_event):
            with patch('backend.ai.tts_engine.async_write_event', new_callable=AsyncMock):
                result = await tts_engine.synthesize("Test", "fr", request_id="custom-001")
        
        assert result["request_id"] == "custom-001"


@pytest.mark.asyncio
async def test_synthesize_auto_request_id(tts_engine):
    """Test génération automatique de request_id."""
    with patch('asyncio.open_connection') as mock_connect:
        mock_reader = AsyncMock()
        mock_writer = AsyncMock()
        mock_connect.return_value = (mock_reader, mock_writer)
        
        audio_data = b'\x00' * 1000
        chunk_event = Mock(type="audio-chunk")
        stop_event = Mock(type="audio-stop")
        
        AudioChunk.is_type = lambda t: t == "audio-chunk"
        AudioStop.is_type = lambda t: t == "audio-stop"
        AudioChunk.from_event = lambda e: Mock(audio=audio_data)
        
        async def mock_read_event(reader):
            if not hasattr(mock_read_event, 'call_count'):
                mock_read_event.call_count = 0
            mock_read_event.call_count += 1
            return chunk_event if mock_read_event.call_count == 1 else stop_event
        
        with patch('backend.ai.tts_engine.async_read_event', side_effect=mock_read_event):
            with patch('backend.ai.tts_engine.async_write_event', new_callable=AsyncMock):
                result = await tts_engine.synthesize("Test", "fr")
        
        assert "request_id" in result
        assert result["request_id"].startswith("tts_")


@pytest.mark.asyncio
async def test_synthesize_audio_metadata(tts_engine):
    """Test que les métadonnées audio sont complètes."""
    with patch('asyncio.open_connection') as mock_connect:
        mock_reader = AsyncMock()
        mock_writer = AsyncMock()
        mock_connect.return_value = (mock_reader, mock_writer)
        
        audio_data = b'\x00' * 1000
        chunk_event = Mock(type="audio-chunk")
        stop_event = Mock(type="audio-stop")
        
        AudioChunk.is_type = lambda t: t == "audio-chunk"
        AudioStop.is_type = lambda t: t == "audio-stop"
        AudioChunk.from_event = lambda e: Mock(audio=audio_data)
        
        async def mock_read_event(reader):
            if not hasattr(mock_read_event, 'call_count'):
                mock_read_event.call_count = 0
            mock_read_event.call_count += 1
            return chunk_event if mock_read_event.call_count == 1 else stop_event
        
        with patch('backend.ai.tts_engine.async_read_event', side_effect=mock_read_event):
            with patch('backend.ai.tts_engine.async_write_event', new_callable=AsyncMock):
                result = await tts_engine.synthesize("Test", "fr")
        
        metadata = result["audio_metadata"]
        assert "sample_rate" in metadata
        assert "channels" in metadata
        assert "sample_width" in metadata
        assert "duration_ms" in metadata
        assert metadata["sample_rate"] == 21470
        assert metadata["channels"] == 1
        assert metadata["sample_width"] == 2


def test_synthesize_sync(tts_engine):
    """Test de la méthode synchrone."""
    with patch.object(tts_engine, 'synthesize', new_callable=AsyncMock) as mock_synth:
        mock_synth.return_value = {"audio_data": "test", "audio_format": "wav"}
        
        result = tts_engine.synthesize_sync("Test synchrone", "fr")
        
        assert result is not None
        mock_synth.assert_called_once_with("Test synchrone", "fr", None)


@pytest.mark.asyncio
async def test_health_check_server_available(tts_engine):
    """Test health check quand serveur disponible."""
    with patch('asyncio.open_connection') as mock_connect:
        mock_reader = AsyncMock()
        mock_writer = AsyncMock()
        mock_connect.return_value = (mock_reader, mock_writer)
        
        result = await tts_engine.health_check()
        
        assert result is True


@pytest.mark.asyncio
async def test_health_check_server_unavailable(tts_engine):
    """Test health check quand serveur indisponible."""
    with patch('asyncio.open_connection', side_effect=ConnectionRefusedError):
        result = await tts_engine.health_check()
        
        assert result is False
