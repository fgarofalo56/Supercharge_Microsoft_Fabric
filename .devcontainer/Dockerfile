# ==============================================================================
# Dockerfile for Microsoft Fabric Casino/Gaming POC Dev Container
# ==============================================================================
# This Dockerfile creates a complete development environment with:
# - Python 3.11 with all project dependencies
# - Azure CLI with Bicep
# - Data science tools (Jupyter, pandas, etc.)
# - Development tools (pytest, black, ruff, mypy)
# ==============================================================================

# Base image: Microsoft's Python dev container
ARG PYTHON_VERSION=3.11
FROM mcr.microsoft.com/devcontainers/python:1-${PYTHON_VERSION}-bullseye

# Metadata
LABEL maintainer="Fabric Casino POC Team"
LABEL description="Development container for Microsoft Fabric Casino/Gaming POC"
LABEL version="1.0.0"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Build tools
    build-essential \
    cmake \
    # Git and version control
    git \
    git-lfs \
    # Network utilities
    curl \
    wget \
    # JSON processing
    jq \
    # Compression utilities
    zip \
    unzip \
    # Process utilities
    htop \
    # Text editors
    vim \
    nano \
    # Database clients (for debugging)
    postgresql-client \
    # Clean up
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js (required for some VS Code extensions and tools)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && npm install -g npm@latest \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create working directory
WORKDIR /workspaces/Supercharge_Microsoft_Fabric

# Copy requirements files
COPY requirements.txt requirements-dev.txt ./

# Upgrade pip and install Python dependencies
RUN pip install --upgrade pip setuptools wheel \
    && pip install -r requirements.txt \
    && pip install -r requirements-dev.txt

# Install additional useful Python packages
RUN pip install \
    # Code formatting
    black \
    isort \
    # Type checking
    mypy \
    # Linting
    ruff \
    pylint \
    flake8 \
    # Documentation
    sphinx \
    mkdocs \
    # Interactive development
    ipython \
    # HTTP client for API testing
    httpx \
    requests \
    # Data validation
    jsonschema \
    # Date/time utilities
    arrow \
    # Progress bars
    rich \
    # CLI enhancements
    typer

# Install Jupyter extensions
RUN pip install \
    jupyterlab \
    jupyterlab-git \
    jupyterlab-lsp \
    python-lsp-server \
    nbstripout

# Configure Jupyter
RUN mkdir -p /home/vscode/.jupyter \
    && echo "c.NotebookApp.token = ''" >> /home/vscode/.jupyter/jupyter_notebook_config.py \
    && echo "c.NotebookApp.password = ''" >> /home/vscode/.jupyter/jupyter_notebook_config.py \
    && echo "c.ServerApp.token = ''" >> /home/vscode/.jupyter/jupyter_notebook_config.py \
    && echo "c.ServerApp.password = ''" >> /home/vscode/.jupyter/jupyter_notebook_config.py

# Create directories for project artifacts
RUN mkdir -p /workspaces/Supercharge_Microsoft_Fabric/temp \
    && mkdir -p /workspaces/Supercharge_Microsoft_Fabric/.data/raw \
    && mkdir -p /workspaces/Supercharge_Microsoft_Fabric/.data/processed \
    && mkdir -p /workspaces/Supercharge_Microsoft_Fabric/.logs

# Set ownership to vscode user
RUN chown -R vscode:vscode /home/vscode \
    && chown -R vscode:vscode /workspaces

# Switch to non-root user
USER vscode

# Configure git for the user
RUN git config --global init.defaultBranch main \
    && git config --global core.autocrlf input \
    && git config --global pull.rebase false

# Set up bash aliases and environment
RUN echo '\n\
# Fabric Casino POC aliases\n\
alias ll="ls -la"\n\
alias la="ls -A"\n\
alias l="ls -CF"\n\
alias py="python"\n\
alias pip="pip3"\n\
alias pytest="python -m pytest"\n\
alias generate="python data_generation/generate.py"\n\
alias validate="python -m pytest validation/ -v"\n\
alias bicep-lint="az bicep build --file infra/main.bicep"\n\
\n\
# Azure shortcuts\n\
alias azlogin="az login --use-device-code"\n\
alias azaccount="az account show"\n\
\n\
# Project navigation\n\
alias cddata="cd /workspaces/Supercharge_Microsoft_Fabric/data_generation"\n\
alias cdinfra="cd /workspaces/Supercharge_Microsoft_Fabric/infra"\n\
alias cdnotebooks="cd /workspaces/Supercharge_Microsoft_Fabric/notebooks"\n\
alias cdvalidation="cd /workspaces/Supercharge_Microsoft_Fabric/validation"\n\
' >> /home/vscode/.bashrc

# Set default shell to bash
SHELL ["/bin/bash", "-c"]

# Default command
CMD ["sleep", "infinity"]
