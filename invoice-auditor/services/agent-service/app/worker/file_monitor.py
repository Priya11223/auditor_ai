"""
Agent Service - File Monitor Worker

Background task that polls the /incoming directory and 
triggers the LangGraph workflow for new, stable files.
"""

import asyncio
import logging
from pathlib import Path

from app.api.deps_sync import get_invoice_repo_sync
from app.config.rules import rules
from app.services.file_service import FileService
from app.workflow.graph import build_graph

logger = logging.getLogger(__name__)

# Compile graph once
compiled_graph = build_graph()


async def start_file_monitor(directory_path: str):
    """
    Infinite loop that polls for files, preprocesses them, 
    and feeds them into the LangGraph workflow.
    """
    logger.info(f"Starting file monitor on directory: {directory_path}")
    path = Path(directory_path)
    
    # Ensure directory exists
    path.mkdir(parents=True, exist_ok=True)
    
    poll_interval = getattr(
        rules.monitor, 
        "poll_interval_seconds", 
        5
    )

    while True:
        try:
            repo = get_invoice_repo_sync()
            file_service = FileService(repo)
            
            # 1. Get stable files
            stable_files = file_service.get_stable_files(path)
            
            for file_path in stable_files:
                # 2. Preprocess (Hash, check duplicates, create DB record)
                initial_state = await file_service.preprocess_file(file_path)
                
                if initial_state.get("is_duplicate"):
                    logger.info(f"Skipping duplicate file: {file_path}")
                    # In production, we might move this to a /duplicates folder
                    continue
                    
                if initial_state.get("error"):
                    logger.error(f"Error preprocessing {file_path}: {initial_state['error']}")
                    continue
                    
                logger.info(f"Triggering workflow for {file_path} (ID: {initial_state.get('invoice_id')})")
                
                # 3. Execute LangGraph workflow
                # The workflow handles its own async execution and DB updates per node
                try:
                    final_state = await compiled_graph.ainvoke(initial_state)
                    logger.info(
                        f"Workflow completed for {file_path}. "
                        f"Status: {final_state.get('validation_status')}, "
                        f"Recommendation: {final_state.get('recommendation')}"
                    )
                except Exception as e:
                    logger.error(f"Workflow crashed for {file_path}: {e}")
                    
                # In production, we would move the file to /processed or /failed here
                
        except asyncio.CancelledError:
            logger.info("File monitor cancelled.")
            break
        except Exception as e:
            logger.error(f"Unexpected error in file monitor loop: {e}")
            
        await asyncio.sleep(poll_interval)
