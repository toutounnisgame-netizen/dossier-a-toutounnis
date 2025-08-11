from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="almaa",
    version="2.0.0",
    author="ALMAA Development Team",
    author_email="contact@almaa.ai",
    description="Autonomous Local Multi-Agent Architecture",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/almaa/almaa-v2",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "pydantic>=2.0.0",
        "click>=8.0.0",
        "pyyaml>=6.0.0",
        "python-dotenv>=1.0.0",
        "loguru>=0.7.0",
        "ollama>=0.1.7",
        "chromadb>=0.4.0",
        "sentence-transformers>=2.2.0",
        "numpy>=1.24.0",
        "scikit-learn>=1.3.0",
        "psutil>=5.9.0",
        "rich>=13.0.0",
    ],
    entry_points={
        "console_scripts": [
            "almaa=main:cli",
        ],
    },
)
