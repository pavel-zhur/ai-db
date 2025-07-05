#!/usr/bin/env python3
"""Setup script for AI-DB MCP Server."""

from setuptools import setup, find_packages

setup(
    name="ai-db-mcp-server",
    version="0.1.0",
    packages=find_packages(),
    python_requires=">=3.13",
    entry_points={
        "console_scripts": [
            "ai-db-mcp=src.ai_db_server:main",
            "ai-frontend-mcp=src.ai_frontend_server:main",
        ],
    },
)