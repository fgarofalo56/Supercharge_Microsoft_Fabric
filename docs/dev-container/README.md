# Dev Container for Microsoft Fabric Casino/Gaming POC

This directory contains the configuration for a VS Code Dev Container that provides a complete, consistent development environment for the Microsoft Fabric Casino/Gaming POC.

## What is a Dev Container?

A Dev Container is a Docker container specifically configured for development. It ensures that every developer on the team has the same tools, dependencies, and configuration, eliminating "works on my machine" issues.

## Quick Start

### Using VS Code (Recommended)

1. **Prerequisites:**
   - [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
   - [VS Code](https://code.visualstudio.com/) installed
   - [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) installed

2. **Open in Container:**
   - Open this repository folder in VS Code
   - When prompted, click "Reopen in Container"
   - Or use Command Palette: `Dev Containers: Reopen in Container`

3. **Wait for Setup:**
   - First build takes 5-10 minutes (subsequent opens are faster)
   - Watch the terminal for setup progress

4. **Start Coding:**
   - All dependencies are pre-installed
   - Run `python data_generation/generate.py --help` to verify

### Using GitHub Codespaces

1. **Open in Codespaces:**
   - Navigate to the repository on GitHub
   - Click the green "Code" button
   - Select "Codespaces" tab
   - Click "Create codespace on main"

2. **Wait for Setup:**
   - Codespace builds automatically
   - Environment is ready when terminal shows welcome message

3. **Access:**
   - Codespace opens in browser-based VS Code
   - Or connect from local VS Code using Codespaces extension

## What's Included

### Languages & Runtimes

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.11 | Primary development language |
| Node.js | 20.x | VS Code extensions support |
| PowerShell | Latest | Cross-platform scripting |

### Development Tools

| Tool | Purpose |
|------|---------|
| Azure CLI | Azure resource management |
| Bicep | Infrastructure as Code |
| GitHub CLI | Repository management |
| Git | Version control |
| Git LFS | Large file support |

### Python Packages

**Core:**
- `pandas`, `numpy` - Data manipulation
- `faker` - Test data generation
- `pyarrow` - Parquet file support
- `pydantic` - Data validation
- `great-expectations` - Data quality

**Azure:**
- `azure-identity` - Authentication
- `azure-storage-blob` - Blob storage
- `azure-keyvault-secrets` - Secrets management
- `azure-eventhub` - Event streaming

**Development:**
- `pytest` - Testing framework
- `black`, `isort` - Code formatting
- `ruff`, `mypy` - Linting & type checking
- `jupyter`, `jupyterlab` - Notebook support

### VS Code Extensions

**Python Development:**
- Python, Pylance, Black Formatter
- Jupyter notebooks support
- Ruff linter, MyPy type checker

**Azure & Infrastructure:**
- Azure Tools pack
- Bicep language support
- Azure Pipelines

**Productivity:**
- GitLens, Git Graph
- Markdown support with Mermaid diagrams
- Code spell checker
- TODO highlighting

## Configuration

### Environment Variables

Create a `.env` file (copy from `.env.sample`):

```bash
# Copy the sample environment file
cp .env.sample .env

# Edit with your values
code .env
```

### Azure Authentication

```bash
# Login to Azure (uses device code flow in container)
az login --use-device-code

# Verify login
az account show

# Set subscription (if needed)
az account set --subscription "Your-Subscription-Name"
```

### Jupyter Notebooks

```bash
# Start Jupyter Lab
jupyter lab --no-browser --port 8888

# Access via forwarded port in VS Code
```

## Common Tasks

### Generate Test Data

```bash
# Show help
python data_generation/generate.py --help

# Generate slot machine events
python data_generation/generate.py --type slot_events --records 1000

# Generate all data types
python data_generation/generate.py --type all --records 5000
```

### Run Tests

```bash
# All tests
pytest validation/ -v

# Specific test categories
pytest validation/unit_tests/ -v
pytest validation/integration_tests/ -v
pytest validation/deployment_tests/ -v

# With coverage
pytest validation/ --cov=data_generation --cov-report=html
```

### Validate Infrastructure

```bash
# Validate Bicep templates
az bicep build --file infra/main.bicep

# What-if deployment
az deployment sub what-if \
  --location eastus \
  --template-file infra/main.bicep \
  --parameters infra/parameters/dev.bicepparam
```

## Customization

### Adding Python Packages

1. Add to `requirements.txt` or `requirements-dev.txt`
2. Rebuild container: `Dev Containers: Rebuild Container`

### Adding VS Code Extensions

1. Edit `.devcontainer/devcontainer.json`
2. Add extension ID to `customizations.vscode.extensions`
3. Rebuild container

### Modifying Container

1. Edit `.devcontainer/Dockerfile`
2. Rebuild container: `Dev Containers: Rebuild Container`

## Troubleshooting

### Container Won't Start

**Symptom:** Container fails to build or start

**Solutions:**
1. Ensure Docker Desktop is running
2. Try `Dev Containers: Rebuild Container Without Cache`
3. Check Docker has enough resources (4GB+ RAM)
4. Review Docker Desktop logs

### Slow Performance

**Symptom:** Container is slow, especially file operations

**Solutions:**
1. Ensure repo is cloned to a case-sensitive filesystem
2. On Windows, use WSL 2 backend for Docker
3. Increase Docker resource allocation
4. Consider using named volumes for node_modules

### Azure CLI Issues

**Symptom:** `az` commands fail or authentication issues

**Solutions:**
```bash
# Re-login
az logout
az login --use-device-code

# Clear cached credentials
rm -rf ~/.azure

# Reinstall CLI
az upgrade
```

### Python Import Errors

**Symptom:** ImportError for installed packages

**Solutions:**
```bash
# Reinstall dependencies
pip install -r requirements.txt -r requirements-dev.txt

# Check Python path
python -c "import sys; print(sys.path)"

# Verify installation
pip list | grep <package-name>
```

### Jupyter Kernel Issues

**Symptom:** Kernel not found or crashes

**Solutions:**
```bash
# Reinstall kernel
python -m ipykernel install --user --name fabric-casino-poc

# List available kernels
jupyter kernelspec list

# Remove and reinstall
jupyter kernelspec remove fabric-casino-poc
python -m ipykernel install --user --name fabric-casino-poc
```

## File Structure

```
.devcontainer/
├── devcontainer.json    # Main configuration
├── Dockerfile           # Container image definition
├── post-create.sh       # Post-creation setup script
└── README.md           # This file
```

## Best Practices

1. **Always rebuild after changes** to devcontainer files
2. **Commit devcontainer changes** so team gets updates
3. **Use `.env` for secrets** - never commit secrets
4. **Test in clean container** before pushing changes
5. **Document customizations** in this README

## Resources

- [VS Code Dev Containers Documentation](https://code.visualstudio.com/docs/devcontainers/containers)
- [Dev Container Specification](https://containers.dev/)
- [GitHub Codespaces Documentation](https://docs.github.com/en/codespaces)
- [Microsoft Python Dev Containers](https://github.com/microsoft/vscode-dev-containers/tree/main/containers/python-3)

## Support

If you encounter issues:

1. Check this troubleshooting guide
2. Review Docker Desktop logs
3. Check VS Code Dev Containers output panel
4. Create an issue in the repository
