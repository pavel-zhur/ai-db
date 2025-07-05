"""Pytest configuration and fixtures."""

import os
import shutil
import tempfile
from pathlib import Path
from typing import Generator

import pytest


@pytest.fixture
def temp_repo_path() -> Generator[Path, None, None]:
    """Create a temporary directory for a test repository."""
    temp_dir = tempfile.mkdtemp(prefix="git-layer-test-")
    yield Path(temp_dir)
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def test_file_content() -> str:
    """Sample content for test files."""
    return """# Test Data
key1: value1
key2: value2
items:
  - item1
  - item2
  - item3
"""


@pytest.fixture(autouse=True)
def setup_git_config():
    """Ensure Git user config is set for tests."""
    # Save current config
    old_name = os.environ.get("GIT_AUTHOR_NAME")
    old_email = os.environ.get("GIT_AUTHOR_EMAIL")
    
    # Set test config
    os.environ["GIT_AUTHOR_NAME"] = "Test User"
    os.environ["GIT_AUTHOR_EMAIL"] = "test@example.com"
    os.environ["GIT_COMMITTER_NAME"] = "Test User"
    os.environ["GIT_COMMITTER_EMAIL"] = "test@example.com"
    
    yield
    
    # Restore config
    if old_name is not None:
        os.environ["GIT_AUTHOR_NAME"] = old_name
    else:
        os.environ.pop("GIT_AUTHOR_NAME", None)
        
    if old_email is not None:
        os.environ["GIT_AUTHOR_EMAIL"] = old_email
    else:
        os.environ.pop("GIT_AUTHOR_EMAIL", None)
        
    os.environ.pop("GIT_COMMITTER_NAME", None)
    os.environ.pop("GIT_COMMITTER_EMAIL", None)