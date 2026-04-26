"""Shared pytest configuration for hancom-mcp."""

from __future__ import annotations


def pytest_configure(config):
    config.addinivalue_line("markers", "unit: lightweight tests, no Java required")
    config.addinivalue_line(
        "markers", "integration: tests that require Java + JAR conversion"
    )
