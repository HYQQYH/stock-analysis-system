"""Test setup file"""

import pytest
from app.config import settings


@pytest.fixture
def test_settings():
    """Fixture for test settings"""
    return settings
