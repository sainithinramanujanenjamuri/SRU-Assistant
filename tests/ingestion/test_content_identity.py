"""Tests for canonical document identity (full content SHA-256 hashing)."""

from pathlib import Path

from ingestion.loaders.base import compute_file_sha256


def test_identical_content_produces_identical_hash(tmp_path: Path) -> None:
    """Verify that two files with identical content produce the exact same document_id."""
    content = b"SR University Academic Regulations R23 - Official Copy"
    file1 = tmp_path / "regulations_r23.txt"
    file2 = tmp_path / "copy_of_regulations_r23.txt"

    file1.write_bytes(content)
    file2.write_bytes(content)

    hash1 = compute_file_sha256(file1)
    hash2 = compute_file_sha256(file2)

    assert hash1 == hash2
    assert len(hash1) == 64  # Standard SHA-256 hex string length


def test_different_content_produces_different_hash(tmp_path: Path) -> None:
    """Verify that different file contents produce distinct document IDs."""
    file1 = tmp_path / "calendar_2025.txt"
    file2 = tmp_path / "calendar_2026.txt"

    file1.write_text("Academic Calendar 2025-26", encoding="utf-8")
    file2.write_text("Academic Calendar 2026-27", encoding="utf-8")

    hash1 = compute_file_sha256(file1)
    hash2 = compute_file_sha256(file2)

    assert hash1 != hash2


def test_filename_does_not_affect_content_identity(tmp_path: Path) -> None:
    """Verify that renaming a file does not change its canonical identity."""
    content = b"Course Syllabus for 23CSE302T - Natural Language Processing"
    original = tmp_path / "original_syllabus.txt"
    renamed = tmp_path / "renamed_syllabus_v2.txt"

    original.write_bytes(content)
    renamed.write_bytes(content)

    assert compute_file_sha256(original) == compute_file_sha256(renamed)
