"""
Agent Service - File Service

Handles the first phase of the pipeline: directory monitoring, stability checking,
routing by extension, duplicate detection via SHA-256, and database registration.
"""

import logging
import os
import time
from pathlib import Path

from app.config.rules import rules
from app.models.database import InvoiceAudit
from app.repositories.invoice_repository import InvoiceRepository
from app.utils.hashing import calculate_sha256

logger = logging.getLogger(__name__)


class FileService:
    """Service for file preprocessing and deduplication."""

    def __init__(self, invoice_repo: InvoiceRepository):
        self.invoice_repo = invoice_repo

    async def get_stable_files(self, directory: str) -> list[Path]:
        """
        Poll a directory and return a list of files that have stabilized
        (size and mtime haven't changed across configured checks).
        """
        dir_path = Path(directory)
        if not dir_path.exists() or not dir_path.is_dir():
            logger.error(f"Incoming directory does not exist: {directory}")
            return []

        # We need the rules to know polling and stability settings
        if not rules:
            logger.error("Rules configuration not loaded, cannot poll files.")
            return []

        exts = [ext.lower().strip(".") for ext in rules.monitor.supported_extensions]
        max_size_bytes = rules.monitor.max_file_size_mb * 1024 * 1024
        
        candidates = {}
        for entry in os.scandir(dir_path):
            if not entry.is_file():
                continue
                
            path = Path(entry.path)
            
            # Extension check
            ext = path.suffix.lower().strip(".")
            if ext not in exts:
                # Silently ignore unsupported extensions to avoid log spam on .gitkeep
                continue
                
            # Size check
            stat = entry.stat()
            if stat.st_size > max_size_bytes:
                logger.warning(f"File {path.name} exceeds max size ({stat.st_size} bytes)")
                continue
                
            candidates[path] = {"size": stat.st_size, "mtime": stat.st_mtime}

        if not candidates:
            return []

        # Wait and verify stability
        time.sleep(rules.monitor.poll_interval_seconds)
        
        stable_files = []
        for path, previous_stat in candidates.items():
            if not path.exists():
                continue
                
            current_stat = path.stat()
            if (current_stat.st_size == previous_stat["size"] and 
                current_stat.st_mtime == previous_stat["mtime"]):
                stable_files.append(path)
                
        return stable_files

    async def preprocess_file(self, file_path: Path) -> dict:
        """
        Process a new file: Calculate checksum, detect duplicates, and register it.
        Returns the initial workflow state dictionary.
        """
        ext = file_path.suffix.lower().strip(".")
        file_name = file_path.name
        
        try:
            checksum = calculate_sha256(str(file_path))
        except FileNotFoundError:
            logger.warning(f"File {file_name} disappeared during hashing.")
            return {
                "file_path": str(file_path),
                "file_name": file_name,
                "file_type": ext,
                "checksum": "",
                "is_duplicate": False,
                "error": "File disappeared",
            }
        except Exception as e:
            logger.error(f"Error hashing {file_name}: {e}")
            return {
                "file_path": str(file_path),
                "file_name": file_name,
                "file_type": ext,
                "checksum": "",
                "is_duplicate": False,
                "error": str(e),
            }

        # Check for duplicate
        is_duplicate = await self.invoice_repo.exists_by_checksum(checksum)
        
        invoice_id = None
        if not is_duplicate:
            # Register in database
            audit_record = InvoiceAudit(
                file_path=str(file_path),
                file_checksum=checksum,
            )
            audit_record = await self.invoice_repo.create(audit_record)
            invoice_id = audit_record.invoice_id
            logger.info(f"Registered new invoice {invoice_id} for {file_name}")
        else:
            logger.info(f"Duplicate file detected (checksum match): {file_name}")

        return {
            "file_path": str(file_path),
            "file_name": file_name,
            "file_type": ext,
            "checksum": checksum,
            "invoice_id": invoice_id,
            "is_duplicate": is_duplicate,
            "error": None,
        }
