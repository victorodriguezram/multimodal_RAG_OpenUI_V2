#!/bin/bash

# Quick fix script for package version issues
echo "🔧 Fixing package version compatibility issues..."

# Check current package versions in requirements
echo "📋 Current package versions:"
grep -E "(cohere|google-generativeai)" requirements.txt api_requirements.txt

echo ""
echo "🔄 The following fixes have been applied:"
echo "  • cohere: 4.21.1 → 4.57 (latest stable)"
echo "  • google-generativeai: 0.7.0 → 0.8.3 (latest compatible)"

echo ""
echo "🚀 Ready to rebuild. Run:"
echo "  docker-compose build --no-cache"
echo "  docker-compose up -d"

echo ""
echo "📊 Verify the fix worked:"
echo "  docker-compose exec multimodal-rag pip list | grep -E '(cohere|google-generativeai|faiss)'"
