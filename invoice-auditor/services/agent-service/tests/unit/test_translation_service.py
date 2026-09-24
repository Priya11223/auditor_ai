import uuid
from unittest.mock import AsyncMock, patch

import pytest

from app.services.translation_service import TranslationService


@pytest.fixture
def mock_invoice_repo():
    return AsyncMock()


@pytest.fixture
def mock_bedrock():
    return AsyncMock()


@pytest.fixture
def mock_redis():
    redis = AsyncMock()
    redis.get.return_value = None
    return redis


@pytest.mark.asyncio
@patch("app.services.translation_service.get_bedrock_client")
@patch("app.services.translation_service.get_redis")
@patch("app.services.translation_service.detect")
async def test_english_skips_translation(
    mock_detect, mock_get_redis, mock_get_bedrock, mock_invoice_repo, mock_bedrock, mock_redis
):
    """Test that English text skips caching and LLM translation."""
    mock_detect.return_value = "en"
    mock_get_bedrock.return_value = mock_bedrock
    mock_get_redis.return_value = mock_redis

    service = TranslationService(invoice_repo=mock_invoice_repo)
    
    invoice_id = uuid.uuid4()
    result = await service.translate_if_needed("Invoice for 100 dollars", invoice_id)

    assert result["source_language"] == "en"
    assert result["translated_text"] is None
    assert result["translation_confidence"] is None

    mock_bedrock.translate_text.assert_not_called()
    mock_redis.get.assert_not_called()
    mock_invoice_repo.update_translation.assert_called_once_with(
        invoice_id=invoice_id,
        source_language="en",
        translated_text=None,
        translation_confidence=None
    )


@pytest.mark.asyncio
@patch("app.services.translation_service.get_bedrock_client")
@patch("app.services.translation_service.get_redis")
@patch("app.services.translation_service.detect")
async def test_foreign_language_bedrock_translation(
    mock_detect, mock_get_redis, mock_get_bedrock, mock_invoice_repo, mock_bedrock, mock_redis
):
    """Test that non-English text triggers translation."""
    mock_detect.return_value = "de"
    mock_bedrock.translate_text.return_value = "Translated English text"
    
    mock_get_bedrock.return_value = mock_bedrock
    mock_get_redis.return_value = mock_redis

    service = TranslationService(invoice_repo=mock_invoice_repo)
    
    invoice_id = uuid.uuid4()
    result = await service.translate_if_needed("Rechnung über 100 Euro", invoice_id)

    assert result["source_language"] == "de"
    assert result["translated_text"] == "Translated English text"
    assert result["translation_confidence"] == 1.0

    mock_redis.get.assert_called_once()
    mock_bedrock.translate_text.assert_called_once_with("Rechnung über 100 Euro", "de")
    mock_redis.setex.assert_called_once()
    mock_invoice_repo.update_translation.assert_called_once()


@pytest.mark.asyncio
@patch("app.services.translation_service.get_bedrock_client")
@patch("app.services.translation_service.get_redis")
@patch("app.services.translation_service.detect")
async def test_foreign_language_cache_hit(
    mock_detect, mock_get_redis, mock_get_bedrock, mock_invoice_repo, mock_bedrock, mock_redis
):
    """Test that a cache hit skips the LLM call."""
    mock_detect.return_value = "de"
    mock_redis.get.return_value = "Cached English text"
    
    mock_get_bedrock.return_value = mock_bedrock
    mock_get_redis.return_value = mock_redis

    service = TranslationService(invoice_repo=mock_invoice_repo)
    
    invoice_id = uuid.uuid4()
    result = await service.translate_if_needed("Rechnung über 100 Euro", invoice_id)

    assert result["source_language"] == "de"
    assert result["translated_text"] == "Cached English text"

    mock_redis.get.assert_called_once()
    mock_bedrock.translate_text.assert_not_called()
    mock_redis.setex.assert_not_called()
