"""
Agent Service - Translation Service

Detects if the raw extracted text is non-English.
If it is, it translates it to English using AWS Bedrock, caching the result in Redis.
Updates the database with the result.
"""

import hashlib
import logging
import uuid
from typing import Optional

from langdetect import LangDetectException, detect

from app.clients.bedrock_client import get_bedrock_client
from app.clients.redis_client import get_redis
from app.config.rules import rules
from app.repositories.invoice_repository import InvoiceRepository

logger = logging.getLogger(__name__)


class TranslationService:
    def __init__(self, invoice_repo: InvoiceRepository):
        self.invoice_repo = invoice_repo
        self.bedrock = get_bedrock_client()
        
    async def translate_if_needed(self, raw_text: str, invoice_id: uuid.UUID) -> dict:
        """
        Detect language, translate if not English, and update the database.
        Returns the workflow state dict.
        """
        if not raw_text or not raw_text.strip():
            return self._build_result("en", None, None, "No text provided")

        if not rules:
            return self._build_result("en", None, None, "Rules not loaded")

        # 1. Language Detection
        source_lang = "en"
        if len(raw_text) >= rules.translation.min_text_length_for_detection:
            try:
                detected = detect(raw_text)
                if detected:
                    source_lang = detected
            except LangDetectException as e:
                logger.warning(f"langdetect failed, assuming English: {e}")
            except Exception as e:
                logger.warning(f"Unexpected langdetect error: {e}")

        # If it's English, we are done.
        if source_lang == "en":
            await self._update_db(invoice_id, "en", None, None)
            return self._build_result("en", None, None, None)

        logger.info(f"Foreign language detected: {source_lang} for invoice {invoice_id}")

        # 2. Redis Cache Lookup
        redis = get_redis()
        cache_key = f"translation:{source_lang}:{hashlib.md5(raw_text.encode()).hexdigest()}"
        translated_text: Optional[str] = None
        
        if redis:
            try:
                cached = await redis.get(cache_key)
                if cached:
                    logger.info(f"Translation cache hit for invoice {invoice_id}")
                    translated_text = cached
            except Exception as e:
                logger.warning(f"Redis cache read error: {e}")

        # 3. AWS Bedrock Translation
        error_msg = None
        if not translated_text:
            logger.info(f"Calling Bedrock for translation (invoice {invoice_id})")
            translated_text = await self.bedrock.translate_text(raw_text, source_lang)
            
            if not translated_text:
                error_msg = "Bedrock translation failed"
                logger.error(f"Translation failed for invoice {invoice_id}")
            elif redis:
                # 4. Save to Cache
                try:
                    await redis.setex(
                        cache_key,
                        rules.translation.cache_ttl_seconds,
                        translated_text
                    )
                except Exception as e:
                    logger.warning(f"Redis cache write error: {e}")

        # Currently we don't calculate a strict confidence score from Bedrock, 
        # so we assume 1.0 if it succeeded.
        confidence = 1.0 if translated_text else None
        
        # 5. Database Update
        await self._update_db(invoice_id, source_lang, translated_text, confidence)
        
        return self._build_result(source_lang, translated_text, confidence, error_msg)

    async def _update_db(
        self, 
        invoice_id: uuid.UUID, 
        source_lang: str, 
        translated: Optional[str], 
        confidence: Optional[float]
    ) -> None:
        """Helper to update the DB."""
        await self.invoice_repo.update_translation(
            invoice_id=invoice_id,
            source_language=source_lang,
            translated_text=translated,
            translation_confidence=confidence,
        )

    def _build_result(
        self, 
        source_lang: str, 
        translated: Optional[str], 
        confidence: Optional[float], 
        error: Optional[str]
    ) -> dict:
        """Helper to format the workflow state return dictionary."""
        return {
            "source_language": source_lang,
            "translated_text": translated,
            "translation_confidence": confidence,
            "error": error,
        }
