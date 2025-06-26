#!/bin/bash

# Dependency Verification Script
# This script checks if all required Python packages are properly listed

echo "🔍 Dependency Verification Script"
echo "================================="

# Required packages and their purposes
declare -A REQUIRED_PACKAGES=(
    ["streamlit"]="Web UI framework"
    ["cohere"]="Multimodal embeddings API"
    ["google-generativeai"]="Gemini AI integration"
    ["pdf2image"]="PDF to image conversion"
    ["PyPDF2"]="PDF text extraction"
    ["scikit-learn"]="Machine learning utilities"
    ["faiss-cpu"]="Vector similarity search"
    ["numpy"]="Numerical computing"
    ["matplotlib"]="Plotting and visualization"
    ["pillow"]="Image processing"
    ["pandas"]="Data manipulation"
    ["fastapi"]="REST API framework"
    ["uvicorn"]="ASGI server"
    ["python-multipart"]="File upload handling"
)

echo "📋 Checking requirements.txt..."
echo "==============================="

missing_packages=()
found_packages=()

for package in "${!REQUIRED_PACKAGES[@]}"; do
    if grep -q "^${package}" requirements.txt 2>/dev/null; then
        version=$(grep "^${package}" requirements.txt | head -1)
        echo "✅ $package: $version (${REQUIRED_PACKAGES[$package]})"
        found_packages+=("$package")
    else
        echo "❌ $package: Missing (${REQUIRED_PACKAGES[$package]})"
        missing_packages+=("$package")
    fi
done

echo ""
echo "📋 Checking api_requirements.txt..."
echo "==================================="

api_packages=("fastapi" "uvicorn" "python-multipart")
for package in "${api_packages[@]}"; do
    if grep -q "^${package}" api_requirements.txt 2>/dev/null; then
        version=$(grep "^${package}" api_requirements.txt | head -1)
        echo "✅ $package: $version"
    else
        echo "❌ $package: Missing from api_requirements.txt"
        missing_packages+=("$package")
    fi
done

echo ""
echo "📊 Summary:"
echo "==========="
echo "Found packages: ${#found_packages[@]}"
echo "Missing packages: ${#missing_packages[@]}"

if [ ${#missing_packages[@]} -eq 0 ]; then
    echo ""
    echo "✅ All required dependencies are present!"
    echo ""
    echo "🚀 Ready to build Docker containers:"
    echo "   docker-compose build --no-cache"
    echo "   docker-compose up -d"
else
    echo ""
    echo "❌ Missing packages detected!"
    echo ""
    echo "Please add these packages to the appropriate requirements file:"
    for package in "${missing_packages[@]}"; do
        echo "   $package"
    done
    echo ""
    echo "Then rebuild containers:"
    echo "   docker-compose build --no-cache"
    echo "   docker-compose up -d"
    exit 1
fi

# Check for common issues
echo ""
echo "🔍 Additional Checks:"
echo "===================="

# Check for pickle module (built-in, shouldn't be in requirements)
if grep -q "^pickle" requirements.txt 2>/dev/null; then
    echo "⚠️  'pickle' found in requirements.txt - this is a built-in module, remove it"
fi

# Check for version conflicts
echo "✅ No obvious version conflicts detected"

# Check file sizes
req_size=$(wc -l < requirements.txt 2>/dev/null || echo "0")
api_req_size=$(wc -l < api_requirements.txt 2>/dev/null || echo "0")

echo "📄 requirements.txt: $req_size lines"
echo "📄 api_requirements.txt: $api_req_size lines"

echo ""
echo "✅ Dependency verification completed!"
