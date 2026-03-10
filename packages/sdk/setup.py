"""Setup script for mekong-sdk package."""

from setuptools import find_packages, setup

with open("README.md", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="mekong-sdk",
    version="0.1.0",
    author="Mekong CLI Team",
    author_email="mekong@agencyos.vn",
    description="Python SDK for Mekong CLI API - AI-powered task execution engine",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/longtho638-jpg/mekong-cli",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.11",
    install_requires=[
        "httpx>=0.25.0",
        "pydantic>=2.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "ruff>=0.1.0",
            "mypy>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "mekong-sdk=mekong_sdk.cli:main",
        ],
    },
    keywords="mekong cli sdk api ai automation agent",
    project_urls={
        "Documentation": "https://github.com/longtho638-jpg/mekong-cli#readme",
        "Source": "https://github.com/longtho638-jpg/mekong-cli",
        "Tracker": "https://github.com/longtho638-jpg/mekong-cli/issues",
    },
)
