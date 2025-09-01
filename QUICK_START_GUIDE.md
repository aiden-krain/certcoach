# Quick Start Guide: New Python Project with uv + Private GitHub Repo

This guide walks you through creating a new Python project using `uv`, setting up a private GitHub repository, and pushing your code.

## Prerequisites

- [uv](https://docs.astral.sh/uv/) installed
- [GitHub CLI](https://cli.github.com/) installed
- Git configured with your name/email
- GitHub account with authentication set up

## Step-by-Step Commands

### 1. Create a New Python Project with uv

```powershell
# Navigate to your development directory
cd C:\DEV

# Create a new Python project with uv
uv init my-project
cd my-project

# Add dependencies (optional)
uv add requests fastapi pytest

# Create a virtual environment and install dependencies
uv sync
```

### 2. Initialize Git Repository

```powershell
# Initialize git repository
git init

# Configure git user (if not already set globally)
git config user.name "Your Name"
git config user.email "your.email@gmail.com"

# Add all files and create initial commit
git add .
git commit -m "Initial commit: Python project setup with uv"
```

### 3. Create Private GitHub Repository and Push

```powershell
# Create a private repository on GitHub and push code
gh repo create your-username/my-project --private --source=. --remote=origin --push
```

**Alternative: Manual approach if GitHub CLI fails:**

```powershell
# Add remote origin (replace with your username/repo)
git remote add origin https://github.com/your-username/my-project.git

# Push to GitHub (you'll be prompted for authentication)
git push -u origin main
```

### 4. Verify Everything Works

```powershell
# Check repository status
git status

# View your repository on GitHub
gh repo view your-username/my-project --web

# Test your Python environment
uv run python --version
uv run python -c "print('Hello from uv project!')"
```

## Complete Command Sequence (Copy & Paste)

```powershell
# Replace 'my-project' and 'your-username' with your actual values
cd C:\DEV
uv init my-project
cd my-project
uv add requests pytest
uv sync
git init
git add .
git commit -m "Initial commit: Python project setup with uv"
gh repo create your-username/my-project --private --source=. --remote=origin --push
git status
```

## Project Structure Created by uv

```
my-project/
├── .python-version      # Python version specification
├── README.md           # Project documentation
├── pyproject.toml      # Project configuration and dependencies
├── uv.lock            # Lock file for reproducible builds
└── src/
    └── my_project/
        └── __init__.py
```

## Common Issues & Solutions

### Issue: "Repository not found" during push
```powershell
# Check if remote is set correctly
git remote -v

# Update remote URL if needed
git remote set-url origin https://github.com/your-username/my-project.git
```

### Issue: Authentication failed
```powershell
# Re-authenticate with GitHub CLI
gh auth login

# Or use personal access token
gh auth login --with-token < your-token.txt
```

### Issue: "src refspec HEAD does not match any"
```powershell
# This means no commits exist - create one first
git add .
git commit -m "Initial commit"
git push -u origin main
```

## Development Workflow

### Adding Dependencies
```powershell
# Add a new dependency
uv add package-name

# Add development dependency
uv add --dev pytest black

# Install/sync all dependencies
uv sync
```

### Running Code
```powershell
# Run Python with uv
uv run python your-script.py

# Run with module
uv run -m pytest

# Activate shell (optional)
uv shell
```

### Making Changes and Pushing
```powershell
# Stage changes
git add .

# Commit with message
git commit -m "Add new feature"

# Push to GitHub
git push
```

## Tips

1. **Always use `uv sync`** after cloning or when dependencies change
2. **Use `uv run`** instead of activating virtual environments manually
3. **Keep `uv.lock` in version control** for reproducible builds
4. **Use `--private` flag** when creating repositories for personal/company projects
5. **Check `git status`** frequently to see what files are staged/unstaged

## Useful uv Commands Reference

```powershell
uv init project-name          # Create new project
uv add package               # Add dependency
uv add --dev package         # Add dev dependency
uv remove package            # Remove dependency
uv sync                      # Install/update dependencies
uv run command               # Run command in environment
uv shell                     # Activate shell
uv python install 3.12      # Install Python version
uv python list              # List installed Python versions
```

---

**Created:** September 1, 2025  
**For:** Python development with uv and GitHub workflow
