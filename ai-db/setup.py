from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="ai-db",
    version="0.1.0",
    author="AI-DB Team",
    description="An AI-native database engine that interprets natural language queries",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ai-db/ai-db",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Database",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.10",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "pytest-asyncio>=0.21.1",
            "pytest-cov>=4.1.0",
            "mypy>=1.7.0",
            "black>=23.11.0",
            "ruff>=0.1.6",
            "types-pyyaml>=6.0.12",
            "types-aiofiles>=23.2.0",
        ]
    },
)