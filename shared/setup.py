from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="ms_communicator",
    version="1.0.0",
    author="Priscope Team",
    author_email="team@priscope.com",
    description="A secure, maintainable library for microservice-to-microservice communication",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/priscope/ms_communicator",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=[
        "fastapi>=0.68.0",
        "starlette>=0.14.0",
        "pydantic>=1.8.0",
        "cryptography>=3.4.0",
        "httpx>=0.23.0",
        "tenacity>=8.0.0",
        "python-dotenv>=0.19.0",
        "aiohttp>=3.8.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0.0",
            "pytest-asyncio>=0.16.0",
            "pytest-cov>=2.12.0",
            "black>=21.5b2",
            "isort>=5.9.0",
            "mypy>=0.910",
            "flake8>=3.9.0",
        ],
    },
)
