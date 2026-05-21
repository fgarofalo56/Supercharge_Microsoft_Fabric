---
hero: assets/heroes/best-practices.svg
hero_alt: Dev experience best practice — Dev Container Setup for Fabric Development
---

# Dev Container Setup for Fabric Development

![Version](https://img.shields.io/badge/Version-1.0.0-blue)
![Updated](https://img.shields.io/badge/Updated-April_2026-green)
![Category](https://img.shields.io/badge/Category-Developer_Experience-purple)

---

**Last Updated:** `2026-04-27` | **Version:** 1.0.0

---

## Overview

A dev container provides a fully configured, reproducible development environment in a Docker container. Instead of each developer installing Python, Java, PySpark, Bicep CLI, and Azure CLI on their local machine, the entire toolchain is packaged in a container definition that "just works" when opened in VS Code.

### Benefits

| Concern | Without Dev Container | With Dev Container |
|---------|----------------------|-------------------|
| Onboarding time | Hours (install everything) | Minutes (open in container) |
| Environment parity | "Works on my machine" | Identical for all developers |
| Python/Java versions | Manual version management | Pinned in Dockerfile |
| Dependency conflicts | System-wide pip installs | Isolated container |
| CI/local parity | Drift between local and CI | Same base image |

---

## What is a Dev Container

A dev container is defined by two files in the `.devcontainer/` directory:

```
.devcontainer/
  devcontainer.json     # VS Code configuration, extensions, mounts
  Dockerfile            # Container image with all tools installed
  docker-compose.yml    # Optional: multi-service setup (Spark, MinIO)
```

When you open the project in VS Code, it detects `.devcontainer/` and offers to reopen in the container. Your source code is mounted into the container, so all edits persist on your local filesystem.

### How It Works

```
+--------------------------------------------------+
| Docker Container                                  |
|                                                   |
|  Python 3.12  +  JDK 17  +  PySpark 3.5.3       |
|  Bicep CLI    +  az CLI  +  gh CLI               |
|  pytest       +  delta-spark  +  DuckDB          |
|                                                   |
|  /workspaces/Suppercharge_Microsoft_Fabric/  <----+-- Mounted from host
|                                                   |
|  VS Code Server (runs inside container)           |
+--------------------------------------------------+
          ^
          | VS Code connects via Dev Containers extension
          |
+------------------+
| VS Code (host)   |
| Dev Containers   |
| extension        |
+------------------+
```

---

## Prerequisites

| Requirement | Purpose | Installation |
|-------------|---------|-------------|
| Docker Desktop | Run containers | [docker.com](https://www.docker.com/products/docker-desktop/) |
| VS Code | Editor | [code.visualstudio.com](https://code.visualstudio.com/) |
| Dev Containers extension | `ms-vscode-remote.remote-containers` | VS Code marketplace |

> **Windows note:** Docker Desktop requires WSL 2 or Hyper-V. On Intune-managed machines, verify Docker Desktop is approved by your IT policy.

---

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/fgarofalo56/Suppercharge_Microsoft_Fabric.git
cd Suppercharge_Microsoft_Fabric

# 2. Open in VS Code
code .

# 3. VS Code detects .devcontainer/ and shows a notification:
#    "Reopen in Container"
#    Click it (or Ctrl+Shift+P > "Dev Containers: Reopen in Container")

# 4. Wait for container build (first time: ~5 minutes, subsequent: seconds)

# 5. You're ready. Run tests to verify:
pytest validation/unit_tests/ -v --tb=short
```

---

## Dockerfile

```dockerfile
# .devcontainer/Dockerfile
# =============================================================================
# Fabric POC Development Container
# Python 3.12 + PySpark 3.5.3 + Bicep CLI + Azure CLI
# =============================================================================

FROM mcr.microsoft.com/devcontainers/python:3.12-bookworm

# ── Metadata ────────────────────────────────────────────────────
LABEL maintainer="platform-team"
LABEL description="Microsoft Fabric POC development environment"
LABEL version="1.0.0"

# ── System Dependencies ────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Java (required by PySpark)
    openjdk-17-jdk-headless \
    # Build tools
    build-essential \
    curl \
    wget \
    unzip \
    git \
    jq \
    # Networking tools (useful for debugging)
    dnsutils \
    iputils-ping \
    && rm -rf /var/lib/apt/lists/*

# ── Java Environment ───────────────────────────────────────────
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV PATH="${JAVA_HOME}/bin:${PATH}"

# ── Azure CLI ──────────────────────────────────────────────────
RUN curl -sL https://aka.ms/InstallAzureCLIDeb | bash

# ── Bicep CLI ──────────────────────────────────────────────────
RUN az bicep install

# ── GitHub CLI ─────────────────────────────────────────────────
RUN curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
    | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
    | tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
    && apt-get update \
    && apt-get install -y gh \
    && rm -rf /var/lib/apt/lists/*

# ── Python Dependencies ───────────────────────────────────────
COPY requirements-dev.txt /tmp/requirements-dev.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r /tmp/requirements-dev.txt

# ── Spark Configuration ───────────────────────────────────────
ENV SPARK_LOCAL_IP=127.0.0.1
ENV PYSPARK_PYTHON=python3
ENV PYSPARK_DRIVER_PYTHON=python3
# Reduce Spark logging noise
ENV SPARK_LOG_LEVEL=WARN

# ── Working Directory ─────────────────────────────────────────
WORKDIR /workspaces/Suppercharge_Microsoft_Fabric

# ── Healthcheck ────────────────────────────────────────────────
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python3 -c "import pyspark; print('OK')" || exit 1
```

### requirements-dev.txt

```text
# .devcontainer/requirements-dev.txt
# ==================================
# All dependencies for local Fabric POC development.

# -- Spark & Delta -----------------------------------------------
pyspark==3.5.3
delta-spark==3.3.0

# -- Testing -----------------------------------------------------
pytest==8.3.4
pytest-cov==6.0.0
great-expectations==1.3.0

# -- Data Generation ---------------------------------------------
faker==33.0.0
numpy==2.2.0
pandas==2.2.3
pyarrow==18.1.0
python-dateutil==2.9.0
pyyaml==6.0.2
requests==2.32.3

# -- Fabric CI/CD ------------------------------------------------
fabric-cicd==1.0.0
azure-identity==1.19.0

# -- Code Quality ------------------------------------------------
ruff==0.8.4
mypy==1.14.0

# -- Utilities ----------------------------------------------------
ipython==8.30.0
duckdb==1.1.3
jupytext==1.16.6
nbval==0.11.0
```

---

## devcontainer.json

```jsonc
// .devcontainer/devcontainer.json
{
  "name": "Fabric POC Dev",
  "build": {
    "dockerfile": "Dockerfile",
    "context": "."
  },

  // ── Features (additional tools installed via dev container features) ──
  "features": {
    // Docker-in-Docker (for running Spark containers inside the dev container)
    "ghcr.io/devcontainers/features/docker-in-docker:2": {
      "version": "latest"
    }
  },

  // ── VS Code Extensions ──────────────────────────────────────────────
  "customizations": {
    "vscode": {
      "extensions": [
        // Core
        "ms-python.python",
        "ms-python.vscode-pylance",
        "ms-azuretools.vscode-bicep",
        "ms-vscode.azure-account",

        // Fabric
        "ms-fabric.fabric-vscode",

        // Testing
        "ms-python.debugpy",

        // Git
        "eamodio.gitlens",
        "mhutchie.git-graph",

        // Documentation
        "yzhang.markdown-all-in-one",
        "redhat.vscode-yaml",
        "bierner.markdown-mermaid",

        // Productivity
        "usernamehw.errorlens",
        "oderwat.indent-rainbow",
        "charliermarsh.ruff",
        "ms-azuretools.vscode-docker"
      ],
      "settings": {
        // Python
        "python.defaultInterpreterPath": "/usr/local/bin/python3",
        "python.analysis.typeCheckingMode": "basic",
        "python.analysis.autoImportCompletions": true,
        "python.analysis.extraPaths": [
          "/workspaces/Suppercharge_Microsoft_Fabric/data_generation",
          "/workspaces/Suppercharge_Microsoft_Fabric/notebooks"
        ],
        "python.languageServer": "Pylance",

        // Testing
        "python.testing.pytestEnabled": true,
        "python.testing.pytestArgs": [
          "validation/unit_tests",
          "-v"
        ],

        // Formatting
        "editor.formatOnSave": true,
        "[python]": {
          "editor.defaultFormatter": "charliermarsh.ruff",
          "editor.codeActionsOnSave": {
            "source.organizeImports": "explicit"
          }
        },

        // Files
        "files.exclude": {
          "**/__pycache__": true,
          "**/.pytest_cache": true,
          ".fabric/": true
        },

        // Terminal
        "terminal.integrated.defaultProfile.linux": "bash",
        "terminal.integrated.env.linux": {
          "FABRIC_POC_HASH_SALT": "devcontainer-salt-do-not-use-in-prod"
        },

        // Bicep
        "bicep.experimental.deployPane": true,

        // Search
        "search.exclude": {
          "**/data_generation/output": true,
          "**/temp": true
        }
      }
    }
  },

  // ── Mounts ──────────────────────────────────────────────────────────
  "mounts": [
    // Azure CLI credential cache (persist across container rebuilds)
    "source=${localEnv:HOME}${localEnv:USERPROFILE}/.azure,target=/home/vscode/.azure,type=bind,consistency=cached",
    // Git credentials
    "source=${localEnv:HOME}${localEnv:USERPROFILE}/.gitconfig,target=/home/vscode/.gitconfig,type=bind,consistency=cached"
  ],

  // ── Port Forwarding ────────────────────────────────────────────────
  "forwardPorts": [
    4040,   // Spark Application UI
    8080,   // Spark Master UI (if using docker-compose)
    9000,   // MinIO S3 API (if using docker-compose)
    9001    // MinIO Console (if using docker-compose)
  ],

  // ── Lifecycle Commands ─────────────────────────────────────────────
  "postCreateCommand": "pip install -e . 2>/dev/null || true && echo 'Dev container ready.'",
  "postStartCommand": "echo '=== Fabric POC Dev Container ===' && python3 --version && java -version 2>&1 | head -1 && az bicep version 2>/dev/null | head -1",

  // ── Environment Variables ──────────────────────────────────────────
  "containerEnv": {
    "FABRIC_POC_HASH_SALT": "devcontainer-salt-do-not-use-in-prod",
    "SPARK_LOCAL_IP": "127.0.0.1",
    "PYTHONDONTWRITEBYTECODE": "1"
  },

  // ── User ───────────────────────────────────────────────────────────
  "remoteUser": "vscode"
}
```

---

## VS Code Extensions and Features

### Extensions Installed Automatically

When the container starts, these extensions are installed inside it:

| Extension | Purpose |
|-----------|---------|
| `ms-python.python` | Python language support |
| `ms-python.vscode-pylance` | Type checking and IntelliSense |
| `ms-azuretools.vscode-bicep` | Bicep IaC editing |
| `ms-fabric.fabric-vscode` | Fabric workspace sync |
| `eamodio.gitlens` | Git blame, history |
| `charliermarsh.ruff` | Python linting and formatting |
| `yzhang.markdown-all-in-one` | Documentation editing |
| `redhat.vscode-yaml` | YAML config editing |
| `usernamehw.errorlens` | Inline error display |

### Dev Container Features

[Dev container features](https://containers.dev/features) are composable units of installation logic:

```jsonc
"features": {
  // Docker-in-Docker: run containers inside the dev container
  "ghcr.io/devcontainers/features/docker-in-docker:2": {},

  // Node.js: if you need npm-based tooling
  "ghcr.io/devcontainers/features/node:1": {
    "version": "20"
  },

  // PowerShell: for cross-platform scripting
  "ghcr.io/devcontainers/features/powershell:1": {
    "version": "latest"
  }
}
```

---

## Volume Mounts and Credential Caching

### Azure Credentials

Mount your local Azure CLI cache so `az login` persists across container rebuilds:

```jsonc
"mounts": [
  // Windows
  "source=${localEnv:USERPROFILE}/.azure,target=/home/vscode/.azure,type=bind,consistency=cached",
  // Linux/macOS
  "source=${localEnv:HOME}/.azure,target=/home/vscode/.azure,type=bind,consistency=cached"
]
```

### Git Credentials

Mount your `.gitconfig` so Git operations work seamlessly:

```jsonc
"mounts": [
  "source=${localEnv:HOME}${localEnv:USERPROFILE}/.gitconfig,target=/home/vscode/.gitconfig,type=bind,consistency=cached"
]
```

For GitHub CLI authentication, run `gh auth login` inside the container once. The token is stored in the container's home directory.

### SSH Keys (Optional)

If you use SSH for Git operations:

```jsonc
"mounts": [
  "source=${localEnv:HOME}${localEnv:USERPROFILE}/.ssh,target=/home/vscode/.ssh,type=bind,consistency=cached"
]
```

> **Security note:** SSH key mounts expose your private keys to the container. For enterprise environments, prefer HTTPS with credential manager or `gh auth`.

---

## Pre-Built Tasks

### tasks.json

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Test: All Unit Tests",
      "type": "shell",
      "command": "pytest validation/unit_tests/ -v --tb=short",
      "group": {
        "kind": "test",
        "isDefault": true
      },
      "presentation": {
        "reveal": "always",
        "panel": "dedicated"
      },
      "problemMatcher": []
    },
    {
      "label": "Test: Casino Tests Only",
      "type": "shell",
      "command": "pytest validation/unit_tests/test_generators.py -v",
      "group": "test",
      "problemMatcher": []
    },
    {
      "label": "Test: Federal Tests Only",
      "type": "shell",
      "command": "pytest validation/unit_tests/federal/ -v",
      "group": "test",
      "problemMatcher": []
    },
    {
      "label": "Test: With Coverage",
      "type": "shell",
      "command": "pytest validation/unit_tests/ -v --cov=data_generation --cov=notebooks/utils --cov-report=html --cov-report=term-missing",
      "group": "test",
      "problemMatcher": []
    },
    {
      "label": "Lint: Ruff Check",
      "type": "shell",
      "command": "ruff check data_generation/ notebooks/utils/ validation/",
      "group": "build",
      "problemMatcher": []
    },
    {
      "label": "Lint: Ruff Format",
      "type": "shell",
      "command": "ruff format data_generation/ notebooks/utils/ validation/",
      "group": "build",
      "problemMatcher": []
    },
    {
      "label": "Validate: Bicep Build",
      "type": "shell",
      "command": "az bicep build --file infra/main.bicep",
      "group": "build",
      "problemMatcher": []
    },
    {
      "label": "Deploy: Dry Run (Dev)",
      "type": "shell",
      "command": "python scripts/fabric-cicd-deploy.py --workspace-id ${input:workspaceId} --environment dev --dry-run",
      "group": "build",
      "problemMatcher": []
    },
    {
      "label": "Generate: Test Fixtures",
      "type": "shell",
      "command": "python scripts/create_local_fixtures.py",
      "group": "build",
      "problemMatcher": []
    }
  ],
  "inputs": [
    {
      "id": "workspaceId",
      "type": "promptString",
      "description": "Fabric Workspace ID (GUID)"
    }
  ]
}
```

### Running Tasks

- `Ctrl+Shift+P` > **Tasks: Run Task** > select from the list.
- Or use the keyboard shortcut `Ctrl+Shift+B` for the default build task.
- Or press `Ctrl+Shift+P` > **Tasks: Run Test Task** for the default test task.

---

## Docker Compose for Multi-Service Setup

For a full local stack with Spark cluster and MinIO (S3-compatible storage):

### docker-compose.yml

```yaml
# .devcontainer/docker-compose.yml
version: "3.9"

services:
  # ── Dev Container ─────────────────────────────────────────────
  devcontainer:
    build:
      context: .
      dockerfile: Dockerfile
    volumes:
      - ..:/workspaces/Suppercharge_Microsoft_Fabric:cached
      - azure-cache:/home/vscode/.azure
    command: sleep infinity
    environment:
      - FABRIC_POC_HASH_SALT=devcontainer-salt-do-not-use-in-prod
      - SPARK_LOCAL_IP=127.0.0.1
      - MINIO_ENDPOINT=http://minio:9000
      - MINIO_ACCESS_KEY=fabricadmin
      - MINIO_SECRET_KEY=fabricpassword123
    depends_on:
      - minio

  # ── MinIO (S3-compatible storage) ────────────────────────────
  minio:
    image: minio/minio:RELEASE.2024-12-18T13-15-44Z
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: fabricadmin
      MINIO_ROOT_PASSWORD: fabricpassword123
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - minio-data:/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 10s
      timeout: 5s
      retries: 3

  # ── MinIO Setup (create default buckets) ─────────────────────
  minio-setup:
    image: minio/mc:latest
    depends_on:
      minio:
        condition: service_healthy
    entrypoint: >
      /bin/sh -c "
        mc alias set local http://minio:9000 fabricadmin fabricpassword123;
        mc mb local/lakehouse --ignore-existing;
        mc mb local/landing --ignore-existing;
        mc mb local/checkpoints --ignore-existing;
        echo 'Buckets created successfully';
      "

volumes:
  minio-data:
  azure-cache:
```

### Using Docker Compose with Dev Containers

Update `devcontainer.json` to use Docker Compose:

```jsonc
{
  "name": "Fabric POC Dev (Full Stack)",
  "dockerComposeFile": "docker-compose.yml",
  "service": "devcontainer",
  "workspaceFolder": "/workspaces/Suppercharge_Microsoft_Fabric",
  // ... rest of devcontainer.json settings
}
```

---

## GitHub Codespaces Compatibility

This dev container configuration is fully compatible with GitHub Codespaces:

### Using Codespaces

1. Navigate to the repository on GitHub.
2. Click the green **Code** button.
3. Select the **Codespaces** tab.
4. Click **Create codespace on main**.
5. Wait for the container to build (~5 minutes first time).
6. You are now in a browser-based VS Code with all tools installed.

### Codespaces-Specific Settings

Add these to `devcontainer.json` for Codespaces optimization:

```jsonc
{
  // Machine type recommendation
  "hostRequirements": {
    "cpus": 4,
    "memory": "8gb",
    "storage": "32gb"
  },

  // Codespaces secrets (mapped from GitHub Secrets)
  "secrets": {
    "FABRIC_POC_HASH_SALT": {
      "description": "Salt for PII hashing in data generators"
    },
    "AZURE_TENANT_ID": {
      "description": "Azure AD tenant ID for Fabric authentication"
    },
    "FABRIC_WORKSPACE_ID_DEV": {
      "description": "Dev workspace GUID for fabric-cicd deployment"
    }
  }
}
```

### Cost Considerations

| Machine Type | Cost/Hour | Use Case |
|-------------|-----------|----------|
| 2-core | ~$0.18 | Documentation, code review |
| 4-core | ~$0.36 | Development, small test runs |
| 8-core | ~$0.72 | Full test suite, Spark jobs |

> **Tip:** Configure an idle timeout of 30 minutes to avoid unnecessary costs:
> GitHub Settings > Codespaces > Default idle timeout: 30 minutes.

---

## Environment Variables

### Required Variables

| Variable | Purpose | Default in Container |
|----------|---------|---------------------|
| `FABRIC_POC_HASH_SALT` | PII hashing salt | `devcontainer-salt-do-not-use-in-prod` |
| `SPARK_LOCAL_IP` | Spark driver bind address | `127.0.0.1` |
| `JAVA_HOME` | JDK location | `/usr/lib/jvm/java-17-openjdk-amd64` |

### Optional Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `MINIO_ENDPOINT` | MinIO S3 endpoint | `http://minio:9000` (compose) |
| `MINIO_ACCESS_KEY` | MinIO access key | `fabricadmin` (compose) |
| `MINIO_SECRET_KEY` | MinIO secret key | `fabricpassword123` (compose) |
| `SPARK_LOG_LEVEL` | Spark logging verbosity | `WARN` |

### Setting Secrets

For sensitive values (Azure credentials, workspace IDs), use VS Code's dev container secrets or GitHub Codespaces secrets. Never hardcode real credentials in `devcontainer.json`.

```bash
# Inside the container, authenticate with Azure
az login --use-device-code

# Authenticate with GitHub CLI
gh auth login
```

---

## Customization

### Adding New Python Packages

Edit `.devcontainer/requirements-dev.txt` and rebuild the container:

```bash
# Ctrl+Shift+P > "Dev Containers: Rebuild Container"
```

### Adding System Packages

Edit the `Dockerfile` `RUN apt-get install` line and rebuild.

### Changing Python Version

Update the base image in `Dockerfile`:

```dockerfile
# Python 3.11
FROM mcr.microsoft.com/devcontainers/python:3.11-bookworm

# Python 3.12 (default)
FROM mcr.microsoft.com/devcontainers/python:3.12-bookworm
```

### Adding More VS Code Extensions

Add extension IDs to the `customizations.vscode.extensions` array in `devcontainer.json`.

---

## Troubleshooting

### Container Build Fails

```
Problem: "ERROR: failed to solve: process /bin/sh -c apt-get..."
Cause:   Network issue during build or stale cache
Fix:     Ctrl+Shift+P > "Dev Containers: Rebuild Container Without Cache"
```

### Java Not Found in Container

```
Problem: "JAVA_HOME is not set" when running PySpark
Cause:   JDK installation failed during build
Fix:     Check Dockerfile for openjdk-17-jdk-headless installation
         Verify: java -version inside the container terminal
```

### Azure CLI Token Expired

```
Problem: "AADSTS700082: The refresh token has expired"
Cause:   Cached Azure credentials are stale
Fix:     az login --use-device-code (re-authenticate)
```

### Slow Container Startup

```
Problem: Container takes minutes to start
Cause:   Extensions installing, large Docker image
Fix:     Use "Dev Containers: Rebuild Container" to cache layers
         Minimize extensions to those actually needed
```

### Git Push Fails with Permission Denied

```
Problem: "Permission denied (publickey)" on git push
Cause:   SSH keys not mounted, or credential helper not configured
Fix:     Option A: Mount SSH keys (see Volume Mounts section)
         Option B: Use HTTPS + gh auth login
         Option C: git config credential.helper store
```

### Port Forwarding Not Working

```
Problem: Cannot access Spark UI at localhost:4040
Cause:   Port not listed in forwardPorts
Fix:     Add port to devcontainer.json forwardPorts array
         Or: VS Code > Ports tab > Forward a Port
```

---

## References

- [Dev Containers Specification](https://containers.dev/)
- [VS Code Dev Containers Documentation](https://code.visualstudio.com/docs/devcontainers/containers)
- [Dev Container Features](https://containers.dev/features)
- [GitHub Codespaces](https://github.com/features/codespaces)
- [Microsoft Dev Container Images](https://mcr.microsoft.com/product/devcontainers/python)
- [This POC: Local Spark Debugging](./local-spark-debugging.md)
- [This POC: VS Code Workflow](./vscode-fabric-workflow.md)
- [This POC: Notebook Unit Testing](./notebook-unit-testing.md)
