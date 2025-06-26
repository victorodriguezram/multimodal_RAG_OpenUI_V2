# 📁 Scripts Directory

This directory contains all the utility scripts for the Multimodal RAG System.

## 🚀 Quick Start

From the project root directory, run:
```bash
chmod +x run-scripts.sh
./run-scripts.sh
```

This will launch an interactive menu to help you choose the right script.

## 📋 Script Categories

### 🔧 Installation & Setup Scripts
- **check-deps.sh** - Check system prerequisites (Docker, Docker Compose)
- **check-env.sh** - Verify environment configuration and API keys
- **setup.sh** - Complete automated setup process
- **setup.ps1** - Windows PowerShell setup script
- **fix-versions.sh** - Fix common package version compatibility issues

### 🚀 Deployment & Maintenance Scripts
- **deploy.sh** - Full system deployment with validation
- **rebuild.sh** - Force rebuild containers with dependency fixes
- **rebuild.ps1** - Windows PowerShell rebuild script
- **validate.sh** - Validate deployment and check system health
- **start.sh** - Container startup script (used internally by Docker)

### 🧹 Cleanup & Troubleshooting Scripts
- **cleanup-targeted.sh** - Remove only project-specific containers and images
- **cleanup-full.sh** - Remove all project resources and volumes
- **cleanup-nuclear.sh** - Remove ALL Docker resources (⚠️ WARNING: affects other projects)

## 📖 Usage Guidelines

### First Time Setup
1. Run `check-deps.sh` to verify system requirements
2. Configure your `.env` file with API keys
3. Run `check-env.sh` to verify configuration
4. Run `setup.sh` for automated setup

### Regular Usage
- Use `deploy.sh` for complete deployment
- Use `validate.sh` to check system health
- Use `rebuild.sh` if you need to rebuild containers

### Troubleshooting
- Use `cleanup-targeted.sh` for safe cleanup
- Use `cleanup-full.sh` for complete project reset
- Use `cleanup-nuclear.sh` only if system is completely broken

## ⚠️ Important Notes

- Always run scripts from the project root directory
- Some scripts require Docker and Docker Compose to be installed
- The `cleanup-nuclear.sh` script will affect ALL Docker resources on your system
- Windows users should use the `.ps1` versions of scripts where available

## 🔗 Related Documentation

- See `../README_DOCKER.md` for detailed deployment instructions
- See `../DEPLOYMENT_SUMMARY.md` for deployment overview
