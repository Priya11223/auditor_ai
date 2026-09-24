"""
Agent Service - AWS Bedrock Client

Wrapper for AWS Bedrock API calls using aioboto3.
"""

import json
import logging
from typing import Optional

import aioboto3
from botocore.exceptions import ClientError

from app.config.settings import settings

logger = logging.getLogger(__name__)


class BedrockClient:
    """Async wrapper for AWS Bedrock converse API."""

    def __init__(self):
        self.session = aioboto3.Session(
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
        )
        self.model_id = settings.bedrock_model_id

    async def translate_text(self, text: str, source_lang: str) -> Optional[str]:
        """
        Ask Bedrock to translate the text to English.
        """
        prompt = (
            f"Translate the following invoice text from {source_lang} to English. "
            f"Preserve all numbers, line breaks, and formatting exactly. "
            f"Only output the translated text, no conversational filler.\n\n{text}"
        )

        try:
            async with self.session.client("bedrock-runtime") as client:
                response = await client.converse(
                    modelId=self.model_id,
                    messages=[
                        {
                            "role": "user",
                            "content": [{"text": prompt}],
                        }
                    ],
                    inferenceConfig={
                        "maxTokens": 4096,
                        "temperature": 0.0,
                        "topP": 0.9,
                    },
                )
                
                output_message = response["output"]["message"]
                return output_message["content"][0]["text"].strip()
                
        except ClientError as e:
            logger.error(f"AWS Bedrock error during translation: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during Bedrock translation: {e}")
            return None

    async def extract_json(self, text: str, schema: dict) -> Optional[dict]:
        """
        Ask Bedrock to extract structured data matching the provided JSON schema.
        Uses Bedrock's tool calling capability to enforce the structure.
        """
        prompt = (
            "Extract the invoice details from the following text according to the provided tool schema. "
            "If a field is missing, omit it or set it to null. "
            f"\n\n<invoice_text>\n{text}\n</invoice_text>"
        )

        tool_config = {
            "tools": [
                {
                    "toolSpec": {
                        "name": "extract_invoice",
                        "description": "Extract structured invoice data",
                        "inputSchema": {
                            "json": schema
                        }
                    }
                }
            ],
            "toolChoice": {
                "tool": {
                    "name": "extract_invoice"
                }
            }
        }

        try:
            async with self.session.client("bedrock-runtime") as client:
                response = await client.converse(
                    modelId=self.model_id,
                    messages=[
                        {
                            "role": "user",
                            "content": [{"text": prompt}],
                        }
                    ],
                    toolConfig=tool_config,
                    inferenceConfig={
                        "maxTokens": 4096,
                        "temperature": 0.0,
                    },
                )
                
                output_message = response["output"]["message"]
                
                # Find the tool use block
                for block in output_message.get("content", []):
                    if "toolUse" in block:
                        return block["toolUse"]["input"]
                
                logger.error("Bedrock did not return a toolUse block.")
                return None
                
        except ClientError as e:
            logger.error(f"AWS Bedrock error during JSON extraction: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during JSON extraction: {e}")
            return None

# Singleton instance
bedrock_client = BedrockClient()

def get_bedrock_client() -> BedrockClient:
    return bedrock_client
