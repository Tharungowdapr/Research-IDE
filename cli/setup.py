"""
CLI package setup for ResearchIDE
"""
from setuptools import setup, find_packages

setup(
    name="research-ide-cli",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "rich>=13.0.0",
        "typer>=0.15.0",
        "httpx>=0.27.0",
    ],
    entry_points={
        "console_scripts": [
            "research-ide=research_cli:app",
        ],
    },
    python_requires=">=3.9",
)
