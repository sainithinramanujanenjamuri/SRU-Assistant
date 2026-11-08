"""Document Security and Ingestion Validation for SRU Assistant (Phase 11).

Enforces institutional upload controls, file integrity validation, duplicate detection,
and path traversal safeguards.
"""

from __future__ import annotations

import hashlib
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Set


class DocumentSecurityError(ValueError):
    """Raised when an ingested document violates security or validation policies."""
    pass


@dataclass
class DocumentValidationResult:
    """Outcome of document security and integrity inspection."""

    is_valid: bool
    safe_filename: str
    file_size_bytes: int
    sha256_hash: str
    is_duplicate: bool = False
    error_message: Optional[str] = None
    detected_mime_type: Optional[str] = None


class DocumentGuard:
    """Protects document ingestion pipeline against path traversal, oversized files, and invalid formats."""

    # Default limits
    MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB
    MIN_FILE_SIZE_BYTES = 10  # Minimum 10 bytes to prevent zero-byte stub files
    ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}

    # Magic byte signatures
    PDF_HEADER = b"%PDF-"
    ZIP_HEADER = b"PK\x03\x04"  # DOCX files are zip containers

    def __init__(
        self,
        max_size_bytes: int = MAX_FILE_SIZE_BYTES,
        allowed_extensions: Optional[Set[str]] = None,
    ) -> None:
        self.max_size_bytes = max_size_bytes
        self.allowed_extensions = allowed_extensions or self.ALLOWED_EXTENSIONS
        self._known_hashes: set[str] = set()

    def register_known_hash(self, sha256_hash: str) -> None:
        """Register a known document hash to support duplicate detection."""
        self._known_hashes.add(sha256_hash)

    def sanitize_filename(self, filename: str) -> str:
        """Sanitize a filename, stripping directory traversal attempts and illegal characters."""
        if not filename or not filename.strip():
            raise DocumentSecurityError("Filename cannot be empty.")

        # Check for path traversal attempts
        if ".." in filename or "/" in filename or "\\" in filename:
            # Extract only the base name
            filename = os.path.basename(filename.replace("\\", "/"))

        # Strip null bytes and control chars
        filename = re.sub(r"[\x00-\x1f\x7f]", "", filename)

        # Remove dangerous shell characters
        filename = re.sub(r"[^\w\.\-\s]", "_", filename).strip()

        if not filename:
            raise DocumentSecurityError("Filename is invalid after sanitization.")

        return filename

    def validate_file_content(
        self,
        filename: str,
        content: bytes,
    ) -> DocumentValidationResult:
        """Validate in-memory document bytes for size, format, magic bytes, and duplicates."""
        safe_name = self.sanitize_filename(filename)
        size = len(content)

        # 1. Size Checks
        if size < self.MIN_FILE_SIZE_BYTES:
            raise DocumentSecurityError(
                f"File '{safe_name}' is too small ({size} bytes). Minimum required size is {self.MIN_FILE_SIZE_BYTES} bytes."
            )

        if size > self.max_size_bytes:
            raise DocumentSecurityError(
                f"File '{safe_name}' exceeds maximum allowed size of {self.max_size_bytes} bytes ({size} bytes received)."
            )

        # 2. Extension Check
        ext = Path(safe_name).suffix.lower()
        if ext not in self.allowed_extensions:
            raise DocumentSecurityError(
                f"File extension '{ext}' is not permitted. Allowed extensions: {sorted(list(self.allowed_extensions))}."
            )

        # 3. Magic Header Integrity Checks
        mime_type = "text/plain"
        if ext == ".pdf":
            if not content.startswith(self.PDF_HEADER):
                raise DocumentSecurityError(f"Corrupted or invalid PDF header in '{safe_name}'.")
            mime_type = "application/pdf"
        elif ext == ".docx":
            if not content.startswith(self.ZIP_HEADER):
                raise DocumentSecurityError(f"Corrupted or invalid DOCX archive structure in '{safe_name}'.")
            mime_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        elif ext == ".txt":
            # Verify text is decodable
            try:
                content[:4096].decode("utf-8")
            except UnicodeDecodeError:
                try:
                    content[:4096].decode("latin-1")
                except Exception as e:
                    raise DocumentSecurityError(f"Plain text file '{safe_name}' could not be decoded: {e}")

        # 4. SHA-256 Hash and Duplicate Detection
        sha256_hash = hashlib.sha256(content).hexdigest()
        is_duplicate = sha256_hash in self._known_hashes

        return DocumentValidationResult(
            is_valid=True,
            safe_filename=safe_name,
            file_size_bytes=size,
            sha256_hash=sha256_hash,
            is_duplicate=is_duplicate,
            detected_mime_type=mime_type,
        )

    def validate_file_on_disk(self, file_path: Path) -> DocumentValidationResult:
        """Inspect and validate an existing file on disk."""
        if not file_path.exists() or not file_path.is_file():
            raise DocumentSecurityError(f"File not found on disk: {file_path}")

        with open(file_path, "rb") as f:
            content = f.read()

        return self.validate_file_content(file_path.name, content)
