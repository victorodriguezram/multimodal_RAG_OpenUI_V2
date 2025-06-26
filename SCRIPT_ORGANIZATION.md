# 📁 Script Organization Summary

## 🔄 What Changed

All utility scripts have been moved from the root directory to the `/scripts` folder for better organization and easier maintenance.

## 📂 New Structure

```
multimodal_RAG_OpenUI_V2/
├── run-scripts.sh              # Main script launcher (NEW)
├── scripts/                    # All utility scripts (NEW FOLDER)
│   ├── README.md              # Script documentation
│   ├── menu.sh                # Interactive script manager (NEW)
│   │
│   ├── # Setup & Installation Scripts
│   ├── check-deps.sh          # System prerequisites check
│   ├── check-env.sh           # Environment verification
│   ├── setup.sh               # Full automated setup
│   ├── setup.ps1              # Windows PowerShell setup
│   ├── fix-versions.sh        # Package version fixes
│   │
│   ├── # Deployment & Maintenance Scripts
│   ├── deploy.sh              # Full deployment with validation
│   ├── rebuild.sh             # Container rebuild
│   ├── rebuild.ps1            # Windows PowerShell rebuild
│   ├── validate.sh            # Deployment validation
│   ├── start.sh               # Container startup (internal)
│   │
│   └── # Cleanup Scripts
│       ├── cleanup-targeted.sh    # Safe project cleanup
│       ├── cleanup-full.sh        # Complete project cleanup
│       └── cleanup-nuclear.sh     # Nuclear cleanup (all Docker)
│
├── README_DOCKER.md           # Updated with new script paths
├── DEPLOYMENT_SUMMARY.md      # Updated references
└── ... (other project files)
```

## 🚀 How to Use

### Option 1: Interactive Menu (Recommended)
```bash
# From project root directory
chmod +x run-scripts.sh
./run-scripts.sh
```

This launches an interactive menu with categorized options:
- **Installation & Setup** (options 1-5)
- **Deployment & Maintenance** (options 6-8)
- **Cleanup & Troubleshooting** (options 9-11)

### Option 2: Direct Script Execution
```bash
# Run scripts directly from project root
./scripts/check-env.sh
./scripts/deploy.sh
./scripts/rebuild.sh
```

## 📋 Script Categories

### 🔧 Installation & Setup (Run These First)
1. **check-deps.sh** - Verify Docker/Docker Compose installation
2. **check-env.sh** - Verify .env file and API keys
3. **setup.sh** - Complete automated setup process
4. **fix-versions.sh** - Fix package version issues

### 🚀 Deployment & Maintenance (Run After Setup)
5. **deploy.sh** - Full deployment with validation
6. **rebuild.sh** - Force rebuild containers
7. **validate.sh** - Check deployment health

### 🧹 Cleanup & Troubleshooting
8. **cleanup-targeted.sh** - Safe project cleanup
9. **cleanup-full.sh** - Complete project reset
10. **cleanup-nuclear.sh** - ⚠️ Remove ALL Docker resources

## ✅ Updated References

All documentation has been updated to reference the new script locations:
- ✅ README_DOCKER.md - Updated all script paths
- ✅ DEPLOYMENT_SUMMARY.md - Updated references
- ✅ Dockerfile - Updated start.sh path
- ✅ deploy.sh - Internal script references fixed

## 🎯 Benefits

1. **Better Organization** - Scripts are no longer cluttering the root directory
2. **Easy Discovery** - Interactive menu helps users find the right script
3. **Categorization** - Scripts are organized by purpose and use case
4. **Documentation** - Each category has clear descriptions
5. **Guided Workflow** - Menu suggests proper order for first-time users

## 🔗 Quick Reference

| Task | Command |
|------|---------|
| **First Time Setup** | `./run-scripts.sh` → Options 1-4 |
| **Deploy System** | `./run-scripts.sh` → Option 6 |
| **Rebuild Containers** | `./run-scripts.sh` → Option 7 |
| **Clean Up Issues** | `./run-scripts.sh` → Options 9-10 |
| **Emergency Reset** | `./run-scripts.sh` → Option 11 |

The system is now much more organized and user-friendly! 🎉
