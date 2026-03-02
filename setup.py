from setuptools import find_packages, setup

setup(
    name="mekong-cli",
    version="3.0.0",
    description="Open-source AI agent framework for autonomous task execution",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Binh Phap Venture Studio",
    author_email="admin@binhphap.io",
    url="https://github.com/mekong-cli/mekong-cli",
    packages=find_packages(exclude=["tests", "tests.*", "docs", "plans", "scripts", "apps", "apps.*"]),
    install_requires=[
        "typer>=0.12.0",
        "rich>=13.0.0",
        "fastapi>=0.109.0",
        "uvicorn[standard]>=0.27.0",
        "pydantic>=2.5.0",
        "pydantic-settings>=2.1.0",
        "requests>=2.31.0",
        "httpx>=0.26.0",
        "python-dotenv>=1.0.0",
        "python-multipart>=0.0.6",
        "jinja2>=3.1.3",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.1",
            "pytest-cov>=4.1.0",
            "ruff>=0.1.11",
            "mypy>=1.8.0",
            "black>=23.12.0",
        ],
        "enterprise": [
            "stripe>=7.10.0",
            "sqlalchemy[asyncio]>=2.0.25",
            "psycopg2-binary>=2.9.9",
            "python-jose[cryptography]>=3.3.0",
            "passlib[bcrypt]>=1.7.4",
        ],
    },
    entry_points={
        "console_scripts": [
            "mekong=src.main:app",
        ],
    },
    python_requires=">=3.9",
    license="MIT",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries",
        "License :: OSI Approved :: MIT License",
    ],
)
