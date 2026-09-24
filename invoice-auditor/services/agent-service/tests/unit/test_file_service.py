import hashlib
import os
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from app.services.file_service import FileService
from app.utils.hashing import calculate_sha256


def test_calculate_sha256():
    """Test that SHA-256 calculation is correct and streaming works."""
    content = b"test file content"
    expected_hash = hashlib.sha256(content).hexdigest()

    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        # Test with a very small chunk size to force multiple chunks
        result = calculate_sha256(tmp_path, chunk_size=2)
        assert result == expected_hash
    finally:
        os.remove(tmp_path)


@pytest.mark.asyncio
async def test_preprocess_file_new():
    """Test preprocessing a new (non-duplicate) file."""
    mock_repo = AsyncMock()
    mock_repo.exists_by_checksum.return_value = False
    
    # Mock create to return an object with a generated invoice_id
    mock_audit = AsyncMock()
    mock_audit.invoice_id = "test-uuid"
    mock_repo.create.return_value = mock_audit

    service = FileService(invoice_repo=mock_repo)

    content = b"invoice data"
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        result = await service.preprocess_file(tmp_path)
        
        assert result["file_path"] == str(tmp_path)
        assert result["file_type"] == "pdf"
        assert result["is_duplicate"] is False
        assert result["invoice_id"] == "test-uuid"
        assert result["error"] is None
        assert result["checksum"] == hashlib.sha256(content).hexdigest()
        
        mock_repo.create.assert_called_once()
    finally:
        os.remove(tmp_path)


@pytest.mark.asyncio
async def test_preprocess_file_duplicate():
    """Test preprocessing a duplicate file."""
    mock_repo = AsyncMock()
    mock_repo.exists_by_checksum.return_value = True

    service = FileService(invoice_repo=mock_repo)

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp.write(b"duplicate data")
        tmp_path = Path(tmp.name)

    try:
        result = await service.preprocess_file(tmp_path)
        
        assert result["is_duplicate"] is True
        assert result["invoice_id"] is None
        mock_repo.create.assert_not_called()
    finally:
        os.remove(tmp_path)
