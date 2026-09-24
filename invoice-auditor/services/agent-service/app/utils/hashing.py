"""
Agent Service - Hashing Utility

Provides streaming SHA-256 generation for files to handle large documents
without excessive memory consumption.
"""

import hashlib


def calculate_sha256(file_path: str, chunk_size: int = 8192) -> str:
    """
    Calculate the SHA-256 hash of a file by reading it in chunks.
    
    Args:
        file_path (str): The absolute path to the file.
        chunk_size (int): Size of chunks to read into memory. Default 8KB.
        
    Returns:
        str: The hexadecimal representation of the SHA-256 checksum.
    """
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            hasher.update(chunk)
    return hasher.hexdigest()
