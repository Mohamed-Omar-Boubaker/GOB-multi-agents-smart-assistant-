"""
Tests unitaires - STT Engine
Responsable: Omar
Date: 2026-02-10
"""

import pytest
import asyncio
import base64
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock
from backend.ai.stt_engine import STTEngine


@pytest.fixture
def stt_engine():
    """Fixture pour créer une instance de STTEngine pour les tests."""
    with patch('backend.ai.stt_engine.WhisperModel') as mock_whisper:
        # Mock du modèle Whisper
        mock_model = MagicMock()
        mock_whisper.return_value = mock_model
        
        engine = STTEngine(model="tiny", device="cpu", compute_type="int8")
        engine.model = mock_model
        
        yield engine


@pytest.fixture
def sample_audio_wav():
    """Crée un fichier audio WAV de test."""
    # Créer un fichier WAV minimal (header + quelques bytes)
    wav_header = b'RIFF' + b'\x00\x00\x00\x00' + b'WAVEfmt ' + b'\x10\x00\x00\x00'
    audio_data = wav_header + b'\x00' * 100  # Données audio simulées
    return base64.b64encode(audio_data).decode()


@pytest.fixture
def sample_audio_mp3():
    """Crée un fichier audio MP3 de test."""
    # Header MP3 minimal
    mp3_header = b'\xFF\xFB\x90\x00'  # MP3 header
    audio_data = mp3_header + b'\x00' * 100
    return base64.b64encode(audio_data).decode()


@pytest.mark.asyncio
async def test_transcribe_audio_wav(stt_engine, sample_audio_wav):
    """Test transcription audio WAV."""
    # Mock des segments retournés par Whisper
    mock_segment1 = Mock()
    mock_segment1.text = "Bonjour"
    mock_segment2 = Mock()
    mock_segment2.text = "comment allez-vous"
    
    mock_info = Mock()
    stt_engine.model.transcribe.return_value = ([mock_segment1, mock_segment2], mock_info)
    
    # Appel de la méthode
    result = await stt_engine.transcribe(
        audio_data=sample_audio_wav,
        audio_format="wav",
        language="fr",
        request_id="test-001"
    )
    
    # Vérifications
    assert result is not None
    assert isinstance(result, dict)
    assert result["transcription"] == "Bonjour comment allez-vous"
    assert result["language"] == "fr"
    assert result["request_id"] == "test-001"
    assert "processing_time_ms" in result
    assert "model_used" in result
    assert result["model_used"] == "whisper-tiny"
    assert "timestamp" in result
    assert "confidence" in result


@pytest.mark.asyncio
async def test_transcribe_audio_mp3(stt_engine, sample_audio_mp3):
    """Test transcription audio MP3."""
    # Mock des segments
    mock_segment = Mock()
    mock_segment.text = "Test MP3"
    mock_info = Mock()
    stt_engine.model.transcribe.return_value = ([mock_segment], mock_info)
    
    # Appel de la méthode
    result = await stt_engine.transcribe(
        audio_data=sample_audio_mp3,
        audio_format="mp3",
        language="fr"
    )
    
    # Vérifications
    assert result is not None
    assert result["transcription"] == "Test MP3"
    assert "request_id" in result  # Généré automatiquement
    assert result["request_id"].startswith("stt_")


@pytest.mark.asyncio
async def test_transcribe_empty_audio_data(stt_engine):
    """Test avec audio_data vide - doit lever ValueError."""
    with pytest.raises(ValueError) as exc_info:
        await stt_engine.transcribe(
            audio_data="",
            audio_format="wav",
            language="fr"
        )
    
    assert "audio_data cannot be empty" in str(exc_info.value)


@pytest.mark.asyncio
async def test_transcribe_invalid_base64(stt_engine):
    """Test avec base64 invalide - doit lever RuntimeError."""
    with pytest.raises(RuntimeError) as exc_info:
        await stt_engine.transcribe(
            audio_data="invalid!!!base64",
            audio_format="wav",
            language="fr"
        )
    
    assert "STT transcription failed" in str(exc_info.value)
    assert "Invalid base64" in str(exc_info.value)


@pytest.mark.asyncio
async def test_transcribe_whisper_error(stt_engine, sample_audio_wav):
    """Test erreur lors de la transcription Whisper."""
    # Mock une erreur Whisper
    stt_engine.model.transcribe.side_effect = Exception("Whisper model error")
    
    with pytest.raises(RuntimeError) as exc_info:
        await stt_engine.transcribe(
            audio_data=sample_audio_wav,
            audio_format="wav",
            language="fr"
        )
    
    assert "STT transcription failed" in str(exc_info.value)


@pytest.mark.asyncio
async def test_transcribe_temp_file_cleanup(stt_engine, sample_audio_wav):
    """Test que le fichier temporaire est bien supprimé."""
    mock_segment = Mock()
    mock_segment.text = "Test cleanup"
    mock_info = Mock()
    stt_engine.model.transcribe.return_value = ([mock_segment], mock_info)
    
    # Tracker pour vérifier la suppression
    created_files = []
    original_mkstemp = tempfile.mkstemp
    
    def track_mkstemp(*args, **kwargs):
        fd, path = original_mkstemp(*args, **kwargs)
        created_files.append(path)
        return fd, path
    
    with patch('tempfile.mkstemp', side_effect=track_mkstemp):
        await stt_engine.transcribe(
            audio_data=sample_audio_wav,
            audio_format="wav",
            language="fr"
        )
    
    # Vérifier que les fichiers créés ont été supprimés
    for file_path in created_files:
        assert not os.path.exists(file_path), f"Temp file {file_path} was not cleaned up"


@pytest.mark.asyncio
async def test_transcribe_multiple_segments(stt_engine, sample_audio_wav):
    """Test transcription avec plusieurs segments."""
    # Mock plusieurs segments
    segments = []
    for i, text in enumerate(["Ceci", "est", "un", "test", "complet"]):
        seg = Mock()
        seg.text = text
        segments.append(seg)
    
    mock_info = Mock()
    stt_engine.model.transcribe.return_value = (segments, mock_info)
    
    result = await stt_engine.transcribe(
        audio_data=sample_audio_wav,
        audio_format="wav",
        language="fr"
    )
    
    assert result["transcription"] == "Ceci est un test complet"


@pytest.mark.asyncio
async def test_transcribe_empty_transcription(stt_engine, sample_audio_wav):
    """Test avec transcription vide (silence)."""
    # Mock aucun segment
    stt_engine.model.transcribe.return_value = ([], Mock())
    
    result = await stt_engine.transcribe(
        audio_data=sample_audio_wav,
        audio_format="wav",
        language="fr"
    )
    
    # Transcription vide doit retourner chaîne vide
    assert result["transcription"] == ""


def test_transcribe_sync(stt_engine, sample_audio_wav):
    """Test de la méthode synchrone transcribe_sync."""
    mock_segment = Mock()
    mock_segment.text = "Test synchrone"
    mock_info = Mock()
    stt_engine.model.transcribe.return_value = ([mock_segment], mock_info)
    
    result = stt_engine.transcribe_sync(
        audio_data=sample_audio_wav,
        audio_format="wav",
        language="fr"
    )
    
    assert result["transcription"] == "Test synchrone"


@pytest.mark.asyncio
async def test_transcribe_default_language(stt_engine, sample_audio_wav):
    """Test avec langue par défaut (fr)."""
    mock_segment = Mock()
    mock_segment.text = "Test langue"
    mock_info = Mock()
    stt_engine.model.transcribe.return_value = ([mock_segment], mock_info)
    
    result = await stt_engine.transcribe(
        audio_data=sample_audio_wav,
        audio_format="wav"
        # language non spécifié, doit utiliser "fr" par défaut
    )
    
    assert result["language"] == "fr"
    # Vérifier que transcribe a été appelé avec language="fr"
    stt_engine.model.transcribe.assert_called_once()
    call_args = stt_engine.model.transcribe.call_args
    assert call_args.kwargs["language"] == "fr"


@pytest.mark.asyncio
async def test_transcribe_processing_time(stt_engine, sample_audio_wav):
    """Test que le temps de traitement est mesuré."""
    mock_segment = Mock()
    mock_segment.text = "Test temps"
    mock_info = Mock()
    stt_engine.model.transcribe.return_value = ([mock_segment], mock_info)
    
    result = await stt_engine.transcribe(
        audio_data=sample_audio_wav,
        audio_format="wav",
        language="fr"
    )
    
    assert "processing_time_ms" in result
    assert isinstance(result["processing_time_ms"], int)
    assert result["processing_time_ms"] >= 0


@pytest.mark.asyncio 
async def test_transcribe_confidence_score(stt_engine, sample_audio_wav):
    """Test que le score de confiance est présent."""
    mock_segment = Mock()
    mock_segment.text = "Test confiance"
    mock_info = Mock()
    stt_engine.model.transcribe.return_value = ([mock_segment], mock_info)
    
    result = await stt_engine.transcribe(
        audio_data=sample_audio_wav,
        audio_format="wav",
        language="fr"
    )
    
    assert "confidence" in result
    assert isinstance(result["confidence"], (int, float))
    assert 0.0 <= result["confidence"] <= 1.0
