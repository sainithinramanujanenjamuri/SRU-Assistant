"""Phase 0 Foundation Tests.

Verifies repository foundation, package importability, configuration
initialization, directory structure integrity, and independence from RYU AI.
Does not test or claim any RAG functionality.
"""

import importlib
from pathlib import Path

from app.config import Settings, get_settings


def test_core_package_imports() -> None:
    """Verify that all foundational packages and modules can be imported cleanly."""
    modules = [
        "app",
        "app.api",
        "app.config",
        "app.services",
        "citations",
        "evaluation",
        "evaluation.datasets",
        "evaluation.generation",
        "evaluation.reports",
        "evaluation.retrieval",
        "generation",
        "generation.llm",
        "generation.prompts",
        "generation.response",
        "ingestion",
        "ingestion.chunking",
        "ingestion.loaders",
        "ingestion.metadata",
        "ingestion.processors",
        "retrieval",
        "retrieval.embeddings",
        "retrieval.filtering",
        "retrieval.fusion",
        "retrieval.lexical",
        "retrieval.reranking",
        "retrieval.vectorstore",
    ]

    for module_name in modules:
        mod = importlib.import_module(module_name)
        assert mod is not None, f"Failed to import {module_name}"

    app_mod = importlib.import_module("app")
    assert getattr(app_mod, "__version__", None) == "0.1.0"


def test_configuration_loading() -> None:
    """Verify that configuration settings instantiate correctly with valid defaults."""
    settings = get_settings()
    assert isinstance(settings, Settings)
    assert settings.app_name == "SRU Assistant"
    assert settings.app_env in ["development", "staging", "production", "test"]
    assert settings.raw_documents_dir == "./documents/raw"
    assert settings.processed_documents_dir == "./documents/processed"


def test_directory_structure_exists() -> None:
    """Verify that all foundational project directories exist on disk."""
    base_dir = Path(__file__).resolve().parent.parent

    expected_directories = [
        base_dir / "app",
        base_dir / "app" / "api",
        base_dir / "app" / "services",
        base_dir / "app" / "config",
        base_dir / "ingestion",
        base_dir / "ingestion" / "loaders",
        base_dir / "ingestion" / "processors",
        base_dir / "ingestion" / "chunking",
        base_dir / "ingestion" / "metadata",
        base_dir / "retrieval",
        base_dir / "retrieval" / "embeddings",
        base_dir / "retrieval" / "vectorstore",
        base_dir / "retrieval" / "lexical",
        base_dir / "retrieval" / "fusion",
        base_dir / "retrieval" / "filtering",
        base_dir / "retrieval" / "reranking",
        base_dir / "generation",
        base_dir / "generation" / "prompts",
        base_dir / "generation" / "llm",
        base_dir / "generation" / "response",
        base_dir / "citations",
        base_dir / "evaluation",
        base_dir / "evaluation" / "datasets",
        base_dir / "evaluation" / "retrieval",
        base_dir / "evaluation" / "generation",
        base_dir / "evaluation" / "reports",
        base_dir / "documents",
        base_dir / "documents" / "raw",
        base_dir / "documents" / "processed",
        base_dir / "configs",
        base_dir / "frontend",
        base_dir / "scripts",
        base_dir / "tests",
        base_dir / "project_memory",
    ]

    for directory in expected_directories:
        assert directory.is_dir(), f"Expected directory does not exist: {directory}"


def test_no_ryu_references_in_codebase() -> None:
    """Verify that no code files import or reference RYU AI components."""
    base_dir = Path(__file__).resolve().parent.parent
    code_packages = ["app", "ingestion", "retrieval", "generation", "citations", "evaluation"]

    for package_name in code_packages:
        package_dir = base_dir / package_name
        for py_file in package_dir.rglob("*.py"):
            content = py_file.read_text(encoding="utf-8").lower()
            assert "import ryu" not in content, f"Forbidden RYU import in {py_file}"
            assert "from ryu" not in content, f"Forbidden RYU import in {py_file}"
